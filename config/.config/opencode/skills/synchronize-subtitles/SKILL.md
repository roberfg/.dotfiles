---
name: synchronize-subtitles
description: Use ONLY when the user wants to re-synchronize a local .srt file against a video file in the same folder using ffsubsync, and rename the result to <video>.es.srt. Triggers on phrases like "sincroniza el subtítulo", "sincroniza el .srt con la película", "ajusta el timing del .srt", "re-sincroniza el subtítulo", "sync the subtitle", "fix subtitle offset". Auto-detects a single video and a single .srt in the current folder; aborts with a clear error if more than one of either is found. Supports .mkv/.mp4/.avi/.mov/.m4v. Overwrites an existing <video>.es.srt without prompting. If ffsubsync fails or is unavailable, preserves the original .srt and still renames it to <video>.es.srt (better a misnamed but intact file than an aborted run).
---

# Synchronize Subtitles

A workflow for the agent to re-synchronize a local `.srt` against a video in the same folder using `ffsubsync`, and rename the result to `<basename>.es.srt`.

The user runs the bundled script. **No flags, no configuration knobs.** The script auto-detects the video and the `.srt` in the current folder (or in a folder passed as the sole argument), runs `ffsubsync` with the same parameters and thresholds used by `search-subtitles`, and renames the result.

## When to use this skill
Use this skill when the user has **already** obtained a `.srt` (manually, from another site, or as a leftover from a previous download) and wants to align its timing with a local video. The user typically:

- Has a folder with one video and one `.srt` that are out of sync.
- Wants the result saved as `<video>.es.srt` (the convention auto-recognized by VLC, Plex, Kodi, Jellyfin, MPC-HC).
- Does not want to (or cannot) re-download from OpenSubtitles.

Do NOT use this skill when:
- The user wants to **download** a subtitle from the internet (use `search-subtitles`).
- The user wants to **extract** subtitles already embedded in the video (`ffmpeg`/`mkvextract`).
- The user wants to **convert** between subtitle formats (`.ass` → `.srt`, etc.).
- The user wants to **normalize** European Spanish to LATAM (use `search-subtitles`; this skill does not touch subtitle text).
- The folder contains more than one video or more than one `.srt` (ambiguous pairing; the script aborts with a clear message).

## Naming convention
The output is always `<video_basename>.es.srt`, regardless of the input `.srt` name. This matches the convention used by `search-subtitles` so that media players auto-pick the right file. To re-synchronize, just run the script again; it will overwrite the existing `<video>.es.srt`.

## Workflow

### 1. Locate the target folder
- If the cwd already contains the video and the `.srt`, use it.
- Otherwise, take the folder path the user provides (absolute or relative to cwd).
- Glob for the configured video extensions: `*.mkv`, `*.mp4`, `*.avi`, `*.mov`, `*.m4v`.
- Glob for `*.srt` files.

### 2. Resolve the video ↔ srt pair
- Exactly **one** video and **one** `.srt` in the folder is required.
- If zero of either: abort with a clear error (exit code 1).
- If more than one of either: abort with a clear error explaining that the user should remove the extras (exit code 2).

### 3. Confirm the environment (silent)
- Run `python --version`.
- Check `shutil.which("ffsubsync")`; if missing, auto-install via `pip install ffsubsync`.
- If `ffsubsync` cannot be installed, the script will still rename the `.srt` to `<video>.es.srt` and report that synchronization did not happen. The user's `.srt` is preserved as-is.

### 4. Run the bundled script
```
python scripts/sync_subs.py [carpeta]
```

The script handles everything end-to-end:

- **Detection** is automatic; no flags. If the user passes a folder, it must be the only positional argument.
- **Synchronization** uses `ffsubsync` with the same flags and thresholds as `search-subtitles/scripts/download_subs.py`:
  - `ffsubsync <video> -i <srt> -o <stem>.synced.srt --skip-sync-on-low-quality --min-score=1000 --quality-max-offset-seconds=600`
  - Defence: if the computed sync has a score below 1000 or an offset above 10 minutes, `ffsubsync` writes no output (we preserve the original `.srt`).
  - Cost: ~30-40 s for a feature film (audio extraction + speech-activity detection). Language-agnostic.
- **Encoding normalization** is run on the final `.srt` (whether the original or the synchronized one) with the same fallback chain as `search-subtitles`: `utf-8-sig` → `utf-8` → `cp1252` → `latin-1`. If the file was decoded via a single-byte encoding, it is re-written as UTF-8 so downstream consumers work with a consistent file.
- **Renaming** moves the final `.srt` to `<video>.es.srt`. If a `<video>.es.srt` already exists, it is overwritten without prompting (per the design decision).
- **Failure handling** is permissive: if `ffsubsync` is missing, returns non-zero, times out, or produces an unusable output, the script keeps the original `.srt` and still renames it to `<video>.es.srt`. The rationale: the user asked for a file at that name; a misnamed but intact file is more useful than an aborted run that leaves the `.srt` with its original (possibly meaningless) name.

### 5. Verify and report
- After the script finishes, list the folder and confirm the presence of `<video>.es.srt`.
- Show the script's own summary line: the offset applied (if any), the score, and the final filename.
- Categories in the script's stdout:
  - `OK -> <video>.es.srt` — success, with the offset and score from `ffsubsync` (or a note that ffsubsync was skipped).
  - `ERROR: <reason>` — abort before any rename, with the reason.
- If a result is reported as "ffsubsync no se aplico" and the user reports poor sync, the options are: try a different source `.srt`, manually run `ffsubsync` with custom parameters, or re-download via `search-subtitles` and let it auto-sync.

## Known pitfalls
- `ffsubsync` infers the output format from the file extension. The intermediate file MUST end in `.srt` (e.g. `<stem>.synced.srt`), not `.srt.tmp` — otherwise ffsubsync raises `NotImplementedError: unsupported output format: tmp`.
- `ffsubsync` decodes the audio and runs speech-activity detection, which takes ~30-40 s for a feature film. It works on any language because it compares the *timing* of speech segments, not the transcription itself.
- The script does not handle the case of multiple videos or multiple `.srt` files. This is intentional: silently picking one would be worse than asking the user to clean up the folder. The error message names the count and the extension.
- If the user has both `<video>.srt` and `<video>.es.srt` in the folder, the script will abort (two `.srt` files). The user should remove the one they do not want to sync.
- The script auto-installs `ffsubsync` via pip if missing. This requires the user's environment to allow pip installs; in locked-down environments the install will fail and the script will fall back to "rename only".
- On Windows consoles, the script forces UTF-8 stdout (`sys.stdout.reconfigure(encoding="utf-8")`) so that `á`, `é`, `í`, etc. print correctly.

## Reusable script reference

| Script | Purpose |
| --- | --- |
| `scripts/sync_subs.py` | Re-synchronizer. Auto-detects video and `.srt`, runs `ffsubsync`, renames to `<video>.es.srt`. No flags; takes an optional folder path as the sole argument. |

Exit codes:
- `0` — success (synchronized or at least renamed).
- `1` — no video or no `.srt` in the folder.
- `2` — usage error (too many arguments, invalid folder, multiple videos, multiple `.srt`).
- `3` — `ffsubsync` unavailable and could not be installed. The `.srt` is still renamed, so this is informational, not fatal.
