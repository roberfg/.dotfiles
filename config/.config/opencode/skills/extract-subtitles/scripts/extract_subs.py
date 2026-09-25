"""Extrae una pista de subtítulos incrustada en el vídeo de la carpeta.

Uso:
    python extract_subs.py [carpeta]

- Sin flags. Si no se da carpeta, usa el directorio actual.
- Detecta automáticamente el vídeo (.mkv/.mp4/.avi/.mov/.m4v).
  Si hay varios, aborta (elección ambigua).
- Lista las pistas de subtítulos con ffprobe y elige UNA pista subrip por prioridad:
  español latino > español neutro > español > inglés.
- Si no hay ninguna pista elegible, no extrae nada y avisa.
- Extrae únicamente pistas subrip con ffmpeg en copia directa (sin conversión),
  siempre como .srt. Descarta cualquier otro códec.
- Nombra la salida <video>.es.srt o <video>.en.srt. Única validación
  de nombrado: si el nombre del vídeo contiene "2160p" (case-insensitive),
  la salida se llama igual que el vídeo (<video>.<ext>).
- Sobrescribe el destino sin preguntar.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VIDEO_EXTS = ("mkv", "mp4", "avi", "mov", "m4v")

# Única validación de nombrado: si el nombre del vídeo contiene "2160p"
# (case-insensitive), la salida se llama igual que el vídeo (<video>.<ext>).
_4K_MARKER = "2160p"

# Único códec aceptado y extensión del archivo extraído.
_SUBTITLE_CODEC = "subrip"
_SUBTITLE_EXT = ".srt"

# Patrones sobre el título de la pista para distinguir las variantes de
# español y para detectar pistas SDH en inglés (se prefieren las normales).
_LATINO_RE = re.compile(r"latin|latino", re.IGNORECASE)
_NEUTRAL_RE = re.compile(r"neutral|neutro", re.IGNORECASE)
_SDH_RE = re.compile(r"\bsdh\b|hearing impaired", re.IGNORECASE)


@dataclass
class SubtitleStream:
    index: int      # índice absoluto de stream; vale para ffmpeg -map 0:N
    codec: str
    language: str   # tag del contenedor (normalmente ISO 639-2) en minúsculas
    title: str


# ---------------------------------------------------------------------------
# Detección
# ---------------------------------------------------------------------------

def _list_videos(folder: Path) -> list[Path]:
    files: list[Path] = []
    for ext in VIDEO_EXTS:
        files.extend(folder.glob(f"*.{ext}"))
    return sorted(files)


def _resolve_video(folder: Path) -> tuple[Path | None, str, int]:
    """Localiza el único vídeo de `folder`.

    Devuelve (video, error_msg, exit_code). Si todo OK, error_msg es "" y
    exit_code es 0. Sin vídeo -> 1. Más de uno -> 2.
    """
    videos = _list_videos(folder)
    if not videos:
        return None, (
            f"No se encontró ningún vídeo ({', '.join('.' + e for e in VIDEO_EXTS)}) "
            f"en {folder}."
        ), 1
    if len(videos) > 1:
        names = ", ".join(v.name for v in videos)
        return None, (
            f"Hay {len(videos)} vídeos en la carpeta ({names}). "
            "Deja solo el que tenga los subtítulos a extraer."
        ), 2
    return videos[0], "", 0


def _make_writable(path: Path) -> None:
    """Quita el atributo de solo lectura para permitir reemplazar el archivo.

    En Windows, abrir para escritura falla con PermissionError si el destino
    es de solo lectura (típico en archivos bajados de internet).
    """
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass


def _target_name(video: Path, lang2: str, ext: str) -> Path:
    """Devuelve la ruta destino del subtítulo extraído.

    Única validación de nombrado: si el nombre del vídeo contiene "2160p"
    (case-insensitive), la salida se llama igual que el vídeo
    (<video>.srt); en cualquier otro caso, <video>.<lang2>.srt.
    """
    if _4K_MARKER in video.stem.lower():
        return video.with_suffix(ext)
    return video.with_name(video.stem + f".{lang2}{ext}")


# ---------------------------------------------------------------------------
# ffprobe: listado de pistas
# ---------------------------------------------------------------------------

def _list_subtitle_streams(video: Path) -> list[SubtitleStream]:
    """Lista las pistas de subtítulos del vídeo con ffprobe."""
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "s",
            "-show_entries", "stream=index,codec_name:stream_tags=language,title",
            "-of", "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe retornó {proc.returncode}")
    data = json.loads(proc.stdout or "{}")
    streams: list[SubtitleStream] = []
    for raw in data.get("streams", []):
        tags = raw.get("tags") or {}
        streams.append(SubtitleStream(
            index=int(raw.get("index", -1)),
            codec=raw.get("codec_name") or "",
            language=(tags.get("language") or "").lower(),
            title=tags.get("title") or "",
        ))
    return streams


# ---------------------------------------------------------------------------
# Selección: una sola pista, prioridad estricta
# ---------------------------------------------------------------------------

def _pick_stream(streams: list[SubtitleStream]) -> tuple[SubtitleStream | None, str, str]:
    """Elige UNA pista subrip por prioridad estricta de idioma.

    Orden: español latino > español neutro > español > inglés.
    Devuelve (stream, lang2, motivo). Si no hay elegible, (None, "", "").
    """
    eligible = [s for s in streams if s.codec == _SUBTITLE_CODEC]
    spa = [s for s in eligible if s.language == "spa"]
    eng = [s for s in eligible if s.language == "eng"]

    for s in spa:
        if _LATINO_RE.search(s.title):
            return s, "es", "español latino"
    for s in spa:
        if _NEUTRAL_RE.search(s.title):
            return s, "es", "español neutro"
    if spa:
        return spa[0], "es", "español"
    if eng:
        # Si hay varias en inglés, se prefiere la que no es SDH.
        non_sdh = [s for s in eng if not _SDH_RE.search(s.title)]
        return (non_sdh or eng)[0], "en", "inglés"
    return None, "", ""


# ---------------------------------------------------------------------------
# ffmpeg: extracción por copia directa
# ---------------------------------------------------------------------------

def _extract(video: Path, stream: SubtitleStream, out_path: Path) -> tuple[bool, str]:
    """Vuelca la pista a `out_path` sin conversión. Devuelve (ok, detalle)."""
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(video),
            "-map", f"0:{stream.index}",
            "-c:s", "copy",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip() or f"ffmpeg retornó {proc.returncode}"
    if not out_path.exists() or out_path.stat().st_size == 0:
        return False, "ffmpeg no escribió salida"
    return True, ""


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if len(args) > 1:
        print("Uso: python extract_subs.py [carpeta]", file=sys.stderr)
        return 2
    folder = Path(args[0]).resolve() if args else Path.cwd()
    if not folder.is_dir():
        print(f"ERROR: {folder} no es un directorio válido.", file=sys.stderr)
        return 2

    print(f"Carpeta: {folder}")
    video, err, code = _resolve_video(folder)
    if err:
        print(f"ERROR: {err}")
        return code
    print(f"Video:  {video.name}")

    # ffmpeg/ffprobe son imprescindibles; no hay fallback.
    missing = [t for t in ("ffprobe", "ffmpeg") if not shutil.which(t)]
    if missing:
        print(f"ERROR: no se encontró {' ni '.join(missing)} en el PATH.")
        return 3

    try:
        streams = _list_subtitle_streams(video)
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"ERROR: ffprobe falló sobre {video.name}: {e}")
        return 3

    if streams:
        print("Pistas de subtítulos:")
        for s in streams:
            title = s.title or "(sin título)"
            print(f"  #{s.index} [{s.language or 'und'}] {s.codec}: {title}")
    else:
        print("El vídeo no tiene pistas de subtítulos.")

    stream, lang2, reason = _pick_stream(streams)
    if stream is None:
        print(
            "\nNo se puede extraer ningún subtítulo .srt: "
            "no existen pistas subrip en español ni en inglés."
        )
        return 4

    target = _target_name(video, lang2, _SUBTITLE_EXT)
    title = stream.title or "(sin título)"
    print(f"\nPista elegida: #{stream.index} [{stream.language}] {title} -> {reason}")
    if target.exists():
        print(f"Sobrescribiendo {target.name} (ya existía).")
        _make_writable(target)

    ok, detail = _extract(video, stream, target)
    if not ok:
        print(f"ERROR: extracción fallida: {detail}")
        return 5

    print(f"\nOK -> {target.name} ({target.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
