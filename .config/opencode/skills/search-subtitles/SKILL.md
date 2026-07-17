---
name: search-subtitles
description: Use ONLY when the user wants to download subtitle files (.srt) for one or more video files in a folder (movie or TV series episodes). Triggers on phrases like "baja los subtítulos", "descarga subs en español", "srt files for this folder", "get Spanish subs", "subtítulos de <X>", "download subs for this series", "search subtitles for this movie". Default language Spanish (Latin American), default provider OpenSubtitles, supports .mkv/.mp4/.avi/.mov/.m4v. Saves each subtitle as `<basename>.<alpha2>.srt` (e.g. `Episode 1.es.srt`), the convention expected by VLC, Plex, Kodi, Jellyfin, MPC-HC. Requires OpenSubtitles credentials (one-time setup with `setup_credentials.py`).
---

# Search Subtitles

A workflow for the agent to download subtitles for a folder of video files via the `subliminal` Python library and OpenSubtitles.

Credentials are required and must be configured once with `setup_credentials.py`. The script then uses them transparently on every run. Language defaults to `spa` (Latin American Spanish → `.es.srt`).

## When to use this skill
Use this skill when the user wants to obtain `.srt` files for a folder that already contains video files (movies or series). The user typically:

- Has a folder with several `.mkv`/`.mp4`/`.avi`/`.mov`/`.m4v` files.
- Has no `.srt` (or has incomplete ones).
- Specifies a language (default Spanish) and a provider (default OpenSubtitles).

Do NOT use this skill when:
- The user wants to extract subtitles already embedded inside the video (use `ffmpeg`/`mkvextract` instead).
- The user wants to convert a subtitle format (`.ass` → `.srt`, etc.) without downloading.
- The user just wants to find *information* about a subtitle, not download it.

## Naming convention
Subtitles are saved as `<basename>.<alpha2>.srt`, where `alpha2` is the ISO 639-1 two-letter code derived from the OpenSubtitles language code via `babelfish`:

| OpenSubtitles code | alpha2 suffix | Example filename              |
| ------------------ | ------------- | ----------------------------- |
| `spa`              | `es`          | `Episode 1.es.srt`            |
| `eng`              | `en`          | `Episode 1.en.srt`            |
| `fra`              | `fr`          | `Episode 1.fr.srt`            |
| `por`              | `pt`          | `Episode 1.pt.srt`            |
| `deu`              | `de`          | `Episode 1.de.srt`            |

This is the convention auto-recognized by VLC, Plex, Kodi, Jellyfin, and MPC-HC.

OpenSubtitles' `spa` already means Latin American Spanish (vs. `spn` for European Spanish), so the `.es` suffix is sufficient for `lang=spa`.

## Workflow

### 1. Locate the target folder
- If the cwd already contains video files, use it.
- Otherwise, take the folder path the user provides (absolute or relative to cwd).
- Glob for the configured extensions: `*.mkv`, `*.mp4`, `*.avi`, `*.mov`, `*.m4v`.
- If no video files are found, report it and stop.

### 2. Confirm the environment (silent)
- Run `python --version` and `pip show subliminal babelfish guessit python-Levenshtein`.
- If any of them is missing, install them:
  ```
  pip install "subliminal[opensubtitles]" babelfish guessit python-Levenshtein
  ```
- If `python` itself is missing, report and stop.

### 3. Credentials (one-time setup, then transparent)
On the very first use, credentials are not configured yet. Run the bundled setup script and let the user enter them once:

```
python scripts/setup_credentials.py
```

This prompts for `OpenSubtitles username` and `OpenSubtitles password` and writes them to:
```
~/.config/opencode/skills/search-subtitles/.credentials.json
```
with restrictive permissions (0600 on POSIX, default ACL on Windows). **Do not echo, log, or commit the file.** This file is already in the dotfiles `.gitignore`.

On every subsequent run, `download_subs.py` reads from that file automatically. The agent does not need to re-prompt the user.

Override at runtime via env vars (take precedence over the file):
```
$env:OS_USER = '<user>'; $env:OS_PASS = '<pass>'
python scripts/download_subs.py --dir <carpeta>
```
or via the alternative env var names `OPEN_SUBTITLES_USER` / `OPEN_SUBTITLES_PASSWORD`. The `--user` / `--pass` CLI flags also override the file when explicitly passed.

If no credentials are found anywhere, `download_subs.py` exits with an error message pointing to `setup_credentials.py` — the agent should relay that message to the user.

### 4. Run the bundled script
The reference script lives at `scripts/download_subs.py` (relative to this skill):

```
python scripts/download_subs.py --dir <carpeta>
```

The script handles detection of series vs movie via `subliminal.scan_video`, retries with stripped series prefixes if no results are found, picks the best subtitle by subliminal's internal scoring, falls back to text-format candidates if the best is image-only, and sleeps 1.5 s between downloads to respect OpenSubtitles v1 rate limits.

### 5. Verify and report
- After the script finishes, list the folder and confirm one `<basename>.<alpha2>.srt` per video file.
- Read the first 5 lines of one of the `.srt` files to sanity-check the language and encoding.
- Show the script's own summary table: `ok / skip / missing / error / dry`.

If anything fails (network, auth, no candidates in text format), the script prints the cause and the agent reports it to the user without prompting.

## Known pitfalls (from prior runs)
- `Language` is exported by `babelfish`, NOT by `subliminal` (subliminal 2.6). Always `from babelfish import Language`.
- `subliminal.save_subtitles(video, subtitles, directory=DIR)` - the first positional arg is the `Video` object, not the `Subtitle` list. Easy to get wrong.
- `Subtitle.subtitle_format` is `None` until the subtitle is downloaded. Filtering by format requires downloading first.
- `download_best_subtitles(only_one=True)` uses `subliminal.score.compute_score` internally - that scoring is the source of truth, do not re-implement it.
- guessit sometimes over-tags series names (e.g. `BBC Planet Earth II` when OpenSubtitles indexes it as just `Planet Earth II`). The script strips common prefixes (`BBC `, `TV `) and retries; the LLM can also override the series name by editing the script if needed.
- For movies whose title guessit under-parses (e.g. `"The Lord of the Rings"` instead of `"The Lord of the Rings: The Two Towers"`), `compute_score` may rank subtitles from sibling films highly. This is a subliminal/guessit limitation, not a script bug.
- The OpenSubtitles v1 XML-RPC endpoint (`https://api.opensubtitles.org/xml-rpc`) is deprecated but still functional in subliminal 2.6. v2 (REST) is NOT supported by this library.
- Don't forget the `sleep` between downloads - v1 will silently return empty results if you hammer it.
- On Windows consoles, the script forces UTF-8 stdout (`sys.stdout.reconfigure(encoding="utf-8")`) so that `á`, `é`, `í`, etc. print correctly.

## Reusable script reference

| Script | Purpose |
| --- | --- |
| `scripts/setup_credentials.py` | One-time interactive prompt for OpenSubtitles credentials, writes to `.credentials.json`. |
| `scripts/download_subs.py` | Main downloader; reads credentials from the file/env vars/CLI args. |

Flags for `download_subs.py`:

| Flag       | Default                  | Description                                                              |
| ---------- | ------------------------ | ------------------------------------------------------------------------ |
| `--dir`    | cwd                      | Folder containing the video files                                        |
| `--lang`   | `spa`                    | Language (OS code `spa`/`eng`/... or ISO `es`/`en`/...)                  |
| `--user`   | file or env              | OpenSubtitles username (override)                                        |
| `--pass`   | file or env              | OpenSubtitles password (override)                                        |
| `--providers` | `opensubtitles`       | Comma-separated list (e.g. `opensubtitles`)                              |
| `--ext`    | `mkv,mp4,avi,mov,m4v`    | Video file extensions to consider                                        |
| `--force`  | off                      | Re-download even if `<basename>.<alpha2>.srt` already exists             |
| `--dry-run` | off                     | Only search and print candidates; do not download                        |
| `--limit`  | unlimited                | Process at most N video files (useful for quick tests)                   |

Exit codes:
- `0` - all videos covered (ok or skip).
- `1` - one or more videos had no subtitle found.
- `2` - usage error (bad arguments) or missing credentials.
