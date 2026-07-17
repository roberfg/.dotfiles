"""Download subtitles for a folder of video files via subliminal.

Usage:
    python download_subs.py --dir <folder> [--lang spa] [--user <u>] [--pass <p>]

Credentials are resolved in this order:
    1. CLI args --user / --pass
    2. Env vars OS_USER / OS_PASS (or OPEN_SUBTITLES_USER / OPEN_SUBTITLES_PASSWORD)
    3. ~/.config/opencode/skills/search-subtitles/.credentials.json
       (created once via scripts/setup_credentials.py)

If none of the above provide credentials, the script exits with code 2
and instructs the user to run setup_credentials.py.

Saves each subtitle as ``<basename>.<alpha2>.srt`` (e.g. ``Episode 1.es.srt``),
the convention auto-recognized by VLC, Plex, Kodi, Jellyfin, MPC-HC.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from babelfish import Language
from subliminal import (
    download_best_subtitles,
    list_subtitles,
    save_subtitles,
    scan_video,
)

DEFAULT_EXTS = ("mkv", "mp4", "avi", "mov", "m4v")
DEFAULT_PROVIDERS = ("opensubtitles",)
DEFAULT_LANG = "spa"
RATE_LIMIT_SECONDS = 1.5
PREFIX_STRIPS = ("BBC ", "TV ", "The ")

CRED_PATH = Path.home() / ".config" / "opencode" / "skills" / "search-subtitles" / ".credentials.json"
SETUP_HINT = (
    "Credenciales de OpenSubtitles no configuradas. Ejecuta primero:\n"
    f"  python {Path(__file__).parent / 'setup_credentials.py'}\n"
    "o define las variables de entorno OS_USER y OS_PASS."
)


def _from_env() -> tuple[str | None, str | None]:
    user = os.environ.get("OS_USER") or os.environ.get("OPEN_SUBTITLES_USER")
    password = os.environ.get("OS_PASS") or os.environ.get("OPEN_SUBTITLES_PASSWORD")
    return user, password


def _from_file() -> tuple[str | None, str | None]:
    if not CRED_PATH.exists():
        return None, None
    try:
        data = json.loads(CRED_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARN: no se pudo leer {CRED_PATH}: {e}", file=sys.stderr)
        return None, None
    user = data.get("user")
    password = data.get("pass")
    if user and password:
        return user, password
    return None, None


def load_credentials() -> tuple[str, str]:
    """Return (user, password) from env, file, or raise SystemExit."""
    user, password = _from_env()
    if user and password:
        return user, password
    user, password = _from_file()
    if user and password:
        return user, password
    raise SystemExit(SETUP_HINT)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=".", help="Folder containing video files (default: cwd)")
    p.add_argument("--lang", default=DEFAULT_LANG, help=f"Language (default: {DEFAULT_LANG}). Accepts OS code (spa/eng/...) or ISO (es/en/...)")
    p.add_argument("--user", default=None, help="OpenSubtitles username (overrides env/file). Run setup_credentials.py first if omitted.")
    p.add_argument("--pass", dest="password", default=None, help="OpenSubtitles password (overrides env/file). Run setup_credentials.py first if omitted.")
    p.add_argument("--providers", default=",".join(DEFAULT_PROVIDERS), help=f"Comma-separated provider names (default: {','.join(DEFAULT_PROVIDERS)})")
    p.add_argument("--ext", default=",".join(DEFAULT_EXTS), help=f"Comma-separated video extensions (default: {','.join(DEFAULT_EXTS)})")
    p.add_argument("--force", action="store_true", help="Re-download even if <basename>.<alpha2>.srt already exists")
    p.add_argument("--dry-run", action="store_true", help="Only search, don't download or save")
    p.add_argument("--limit", type=int, default=0, help="Process at most N files (0 = unlimited)")
    p.add_argument("--rate", type=float, default=RATE_LIMIT_SECONDS, help=f"Sleep seconds between downloads (default: {RATE_LIMIT_SECONDS})")
    return p.parse_args()


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """CLI args win; otherwise load_credentials() (env + file)."""
    if args.user and args.password:
        return args.user, args.password
    user, password = load_credentials()
    if args.user:
        user = args.user
    if args.password:
        password = args.password
    return user, password


def resolve_language(lang: str) -> tuple[Language, str]:
    """Return (babelfish Language, alpha2 code) for the requested language.

    Accepts either OpenSubtitles codes (spa, eng) or ISO 639-1 (es, en).
    """
    normalized = lang.strip().lower()
    if len(normalized) == 2:
        candidates = [normalized, Language.fromalpha2(normalized).opensubtitles]
    else:
        candidates = [normalized, Language.fromopensubtitles(normalized).alpha2]
    for code in candidates:
        try:
            language = Language(code)
            return language, language.alpha2
        except (ValueError, AttributeError):
            continue
    raise SystemExit(f"Idioma no reconocido: {lang!r}. Prueba con 'spa', 'eng', 'es', 'en', ...")


def list_videos(folder: Path, exts: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for ext in exts:
        files.extend(folder.glob(f"*.{ext}"))
    return sorted(files)


def find_produced_srt(video: Path, alpha2: str) -> Path | None:
    expected = video.with_suffix("").name + f".{alpha2}.srt"
    expected_path = video.parent / expected
    if expected_path.exists():
        return expected_path
    base = video.with_suffix("").name
    for p in video.parent.iterdir():
        if p.suffix.lower() != ".srt":
            continue
        if p.stem == base or p.stem.startswith(base + "."):
            return p
    return None


def download_one(video: Path, language: Language, alpha2: str, providers: list[str], user: str, password: str, force: bool, dry_run: bool) -> str:
    expected = video.parent / (video.with_suffix("").name + f".{alpha2}.srt")
    print(f"\n=== {video.name} ===")
    if not force and expected.exists() and expected.stat().st_size > 0:
        print(f"  Ya existe {expected.name}, omitiendo.")
        return "skip"

    v = scan_video(str(video))
    is_episode = bool(getattr(v, "series", None))
    if is_episode:
        original_series = v.series
        v.series = v.series.replace("BBC ", "").strip()
        v.original_series = True
        print(f"  Series: {v.series} S{v.season:02d}E{v.episode:02d} - {v.title}")
    else:
        original_series = None
        print(f"  Pelicula: {v.title} ({v.year})")
    print(f"  Tamano: {v.size:,} bytes")

    pool_kw = dict(
        providers=providers,
        provider_configs={"opensubtitles": {"username": user, "password": password}},
    )

    print(f"  Buscando subtitulos [{language.opensubtitles} -> .{alpha2}.srt]...")
    subs = list_subtitles({v}, {language}, **pool_kw).get(v, [])

    if not subs and is_episode and original_series != v.series:
        for prefix in PREFIX_STRIPS:
            alt = v.series.replace(prefix, "").strip()
            if alt and alt != v.series:
                print(f"  Sin resultados, reintentando series='{alt}'...")
                v.series = alt
                subs = list_subtitles({v}, {language}, **pool_kw).get(v, [])
                if subs:
                    break

    if not subs:
        print("  Sin resultados.")
        return "missing"

    TEXT_FMT = {"srt", "ass", "ssa", "vtt", "subrip", "webvtt"}
    print(f"  Encontrados {len(subs)} candidatos.")

    if dry_run:
        for s in subs[:5]:
            print(f"    - {getattr(s, 'filename', s)} (movie_name={getattr(s, 'movie_name', '?')}, year={getattr(s, 'movie_year', '?')})")
        return "dry"

    print("  Descargando el mejor...")
    best_list = download_best_subtitles(
        {v}, {language}, only_one=True, **pool_kw
    ).get(v, [])
    if not best_list:
        print("  No se pudo descargar (score insuficiente).")
        return "missing"

    best = best_list[0]
    print(f"  Mejor por subliminal: {best.filename} (fmt={best.subtitle_format})")

    if getattr(best, "subtitle_format", None) not in TEXT_FMT:
        print(f"  Formato {best.subtitle_format!r} no convertible a .srt. Buscando alternativa...")
        from subliminal import download_subtitles as dl_subs
        from subliminal.score import compute_score
        to_try = [s for s in subs[:15] if s is not best]
        dl_subs(to_try, **pool_kw)
        text_subs = [s for s in to_try if getattr(s, "subtitle_format", None) in TEXT_FMT]
        if text_subs:
            text_subs.sort(key=lambda s: compute_score(s, v), reverse=True)
            best = text_subs[0]
            print(f"  Fallback en formato texto: {best.filename} (fmt={best.subtitle_format}, score={compute_score(best, v)})")
        else:
            print("  No hay alternativa en formato texto.")
            return "missing"

    save_subtitles(v, [best], directory=str(video.parent))
    produced = find_produced_srt(video, alpha2)
    if produced is None:
        print("  No se localizo el .srt producido.")
        return "missing"
    if produced.resolve() != expected.resolve():
        os.replace(produced, expected)
    size = expected.stat().st_size
    print(f"  OK -> {expected.name} ({size:,} bytes)")
    return "ok"


def main() -> int:
    args = parse_args()

    try:
        language, alpha2 = resolve_language(args.lang)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2

    try:
        user, password = resolve_credentials(args)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2

    folder = Path(args.dir).resolve()
    if not folder.is_dir():
        print(f"ERROR: {folder} no es un directorio valido.", file=sys.stderr)
        return 2

    exts = tuple(e.strip().lstrip(".").lower() for e in args.ext.split(",") if e.strip())
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]

    videos = list_videos(folder, exts)
    if not videos:
        print(f"No se encontraron videos ({', '.join('.'+e for e in exts)}) en {folder}")
        return 1
    if args.limit:
        videos = videos[: args.limit]

    print(f"Folder: {folder}")
    print(f"{len(videos)} video(s), lang {language.opensubtitles} (suffix .{alpha2})")
    print(f"providers: {', '.join(providers)}\n")

    counts: dict[str, int] = {}
    for i, v in enumerate(videos):
        try:
            r = download_one(v, language, alpha2, providers, user, password, args.force, args.dry_run)
        except Exception as e:
            import traceback
            print(f"  ERROR: {e}")
            traceback.print_exc()
            r = "error"
        counts[r] = counts.get(r, 0) + 1
        if i < len(videos) - 1 and r in ("ok", "missing") and args.rate > 0:
            time.sleep(args.rate)

    print("\n--- Resumen ---")
    for k, n in sorted(counts.items()):
        print(f"  {k}: {n}")
    missing = counts.get("missing", 0) + counts.get("error", 0)
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
