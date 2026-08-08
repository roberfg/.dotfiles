"""Re-sync a local .srt against a video in the same folder and rename it.

Uso:
    python sync_subs.py [carpeta]

- Sin flags. Si no se da carpeta, usa el directorio actual.
- Detecta automaticamente el video (.mkv/.mp4/.avi/.mov/.m4v) y el .srt.
- Si hay varios de cualquiera, aborta (asociacion ambigua).
- Ejecuta ffsubsync con los mismos flags y umbrales que search-subtitles.
- Renombra el resultado a <basename>.es.srt.
- Si ffsubsync falla, conserva el .srt original y lo renombra igual.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VIDEO_EXTS = ("mkv", "mp4", "avi", "mov", "m4v")
SRT_EXT = ".srt"
ALPHA2 = "es"

# Mismos umbrales que search-subtitles/scripts/download_subs.py
_FFSUBSYNC_MIN_SCORE = 1000
_FFSUBSYNC_MAX_OFFSET = 600.0  # segundos (10 min)

_FFSUBSYNC_SCORE_RE = re.compile(r"score:\s*([0-9]+(?:\.[0-9]+)?)")
_FFSUBSYNC_OFFSET_RE = re.compile(r"offset seconds:\s*(-?[0-9]+(?:\.[0-9]+)?)")

# Orden de fallback de encoding para SRTs. La mayoria son UTF-8 con o sin BOM,
# pero algunos uploaders suben Windows-1252.
_SRT_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


# ---------------------------------------------------------------------------
# Deteccion
# ---------------------------------------------------------------------------

def _list_videos(folder: Path) -> list[Path]:
    files: list[Path] = []
    for ext in VIDEO_EXTS:
        files.extend(folder.glob(f"*.{ext}"))
    return sorted(files)


def _list_srts(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() == SRT_EXT)


def _resolve_pair(folder: Path) -> tuple[Path | None, Path | None, str | None, str]:
    """Localiza (video, srt) en `folder`.

    Devuelve (video, srt, error_msg, exit_code). Si todo OK, error_msg es "" y
    exit_code es 0. Si falta video o srt, exit_code es 1. Si hay mas de uno
    de cualquiera, exit_code es 2.
    """
    videos = _list_videos(folder)
    srts = _list_srts(folder)
    if not videos:
        return None, None, (
            f"No se encontro ningun video ({', '.join('.' + e for e in VIDEO_EXTS)}) "
            f"en {folder}."
        ), "1"
    if not srts:
        return None, None, "No se encontro ningun .srt en la carpeta.", "1"
    if len(videos) > 1:
        names = ", ".join(v.name for v in videos)
        return None, None, (
            f"Hay {len(videos)} videos en la carpeta ({names}). "
            "Deja solo el que corresponda al .srt."
        ), "2"
    if len(srts) > 1:
        names = ", ".join(s.name for s in srts)
        return None, None, (
            f"Hay {len(srts)} archivos .srt en la carpeta ({names}). "
            "Deja solo el que quieras sincronizar."
        ), "2"
    return videos[0], srts[0], "", "0"


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def _read_text_with_fallback(path: Path) -> str:
    """Lee un .srt probando varios encodings y lo reescribe en UTF-8.

    Si el archivo no es UTF-8 valido, lo reescribimos en UTF-8 sin BOM para
    que los pasos siguientes y los reproductores lo carguen sin problemas.
    """
    raw = path.read_bytes()
    chosen = None
    for enc in _SRT_ENCODINGS:
        try:
            text = raw.decode(enc)
            chosen = enc
            break
        except UnicodeDecodeError:
            continue
    if chosen is None:
        text = raw.decode("utf-8", errors="replace")
        chosen = "utf-8"

    if chosen in ("cp1252", "latin-1"):
        try:
            path.write_text(text, encoding="utf-8")
        except OSError:
            pass
    return text


# ---------------------------------------------------------------------------
# ffsubsync
# ---------------------------------------------------------------------------
# Mismo nucleo que search-subtitles/scripts/download_subs.py:_run_ffsubsync.
# ffsubsync detecta el speech del audio del video y el speech "inferido" del
# .srt (por la disposicion de los cues), calcula el offset entre ambos y
# reescribe los timestamps del .srt.
#
# Defence: --skip-sync-on-low-quality + min-score + max-offset-seconds.
# Si ffsubsync considera el resultado poco fiable, no escribe salida y
# conservamos el .srt original.


def _ensure_ffsubsync() -> bool:
    """Devuelve True si ffsubsync esta disponible; intenta instalarlo si no."""
    if shutil.which("ffsubsync"):
        return True
    print("ffsubsync no encontrado, intentando instalar...", file=sys.stderr)
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "ffsubsync", "-q"],
            check=True,
            timeout=180,
        )
    except Exception as e:
        print(f"WARN: pip install ffsubsync fallo ({e}).", file=sys.stderr)
        return False
    return bool(shutil.which("ffsubsync"))


def _run_ffsubsync(video: Path, srt: Path) -> tuple[bool, float, float]:
    """Re-sincroniza `srt` al audio de `video` con ffsubsync.

    Devuelve (ok, offset_seconds, score). Si falla, (False, 0.0, 0.0).
    """
    if not _ensure_ffsubsync():
        return False, 0.0, 0.0
    # ffsubsync determina el formato de salida por extension: el .tmp
    # original no servia. Usamos <stem>.synced.srt (mantiene .srt) como
    # archivo intermedio y lo movemos sobre el original solo si todo OK.
    srt_out = srt.with_name(srt.stem + ".synced.srt")
    try:
        proc = subprocess.run(
            [
                "ffsubsync",
                str(video),
                "-i", str(srt),
                "-o", str(srt_out),
                "--skip-sync-on-low-quality",
                f"--min-score={_FFSUBSYNC_MIN_SCORE}",
                f"--quality-max-offset-seconds={_FFSUBSYNC_MAX_OFFSET}",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("WARN: ffsubsync excedio el timeout de 600s.")
        if srt_out.exists():
            try:
                srt_out.unlink()
            except OSError:
                pass
        return False, 0.0, 0.0
    except FileNotFoundError:
        print("WARN: ffsubsync no esta instalado y no se pudo instalar.")
        return False, 0.0, 0.0

    score = 0.0
    offset = 0.0
    for line in proc.stderr.splitlines() + proc.stdout.splitlines():
        m = _FFSUBSYNC_SCORE_RE.search(line)
        if m:
            score = float(m.group(1))
        m = _FFSUBSYNC_OFFSET_RE.search(line)
        if m:
            offset = float(m.group(1))

    if proc.returncode != 0:
        print(f"WARN: ffsubsync retorno codigo {proc.returncode}.")
        if srt_out.exists():
            try:
                srt_out.unlink()
            except OSError:
                pass
        return False, offset, score

    if not srt_out.exists() or srt_out.stat().st_size == 0:
        # ffsubsync con --skip-sync-on-low-quality no escribe salida cuando
        # descarta el resultado (score bajo u offset absurdo). Lo tratamos
        # como no-aplicable, no como error.
        print(
            f"ffsubsync no escribio salida (score/offset fuera de umbrales): "
            f"score={score:.0f}, offset={offset:+.2f}s."
        )
        return False, offset, score

    os.replace(srt_out, srt)
    return True, offset, score


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if len(args) > 1:
        print("Uso: python sync_subs.py [carpeta]", file=sys.stderr)
        return 2
    folder = Path(args[0]).resolve() if args else Path.cwd()
    if not folder.is_dir():
        print(f"ERROR: {folder} no es un directorio valido.", file=sys.stderr)
        return 2

    print(f"Carpeta: {folder}")
    video, srt, err, err_code = _resolve_pair(folder)
    if err:
        print(f"ERROR: {err}")
        return int(err_code)
    print(f"Video:  {video.name}")
    print(f"SRT:    {srt.name}")

    target = video.with_name(video.stem + f".{ALPHA2}.srt")
    same_as_target = srt.resolve() == target.resolve()
    if target.exists() and not same_as_target:
        print(f"Sobrescribiendo {target.name} (ya existia).")
    elif same_as_target:
        print(f"Re-sincronizando {target.name} en sitio.")

    print("\nRe-sincronizando con ffsubsync contra el audio...")
    ffsubsync_available = bool(shutil.which("ffsubsync"))
    sync_ok, offset, score = _run_ffsubsync(video, srt)
    if sync_ok:
        print(
            f"ffsubsync: offset aplicado {offset:+.3f}s "
            f"(score={score:.0f})."
        )
    else:
        print(
            "ffsubsync no se aplico (fallo, ausente o score bajo). "
            "Se conserva el .srt original."
        )

    # Asegurar encoding UTF-8 consistente en el .srt final (sea el original
    # o el sincronizado).
    _read_text_with_fallback(srt)

    # Renombrar a <basename>.es.srt.
    if srt.resolve() != target.resolve():
        if target.exists():
            try:
                target.unlink()
            except OSError as e:
                print(f"ERROR: no se pudo borrar {target.name}: {e}")
                return 2
        os.replace(srt, target)

    print(f"\nOK -> {target.name} ({target.stat().st_size:,} bytes)")
    if not sync_ok and not ffsubsync_available:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
