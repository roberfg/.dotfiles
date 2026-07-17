"""One-time setup for OpenSubtitles credentials.

Reads username and password interactively and saves them to
~/.config/opencode/skills/search-subtitles/.credentials.json with
restrictive permissions. Subsequent invocations of download_subs.py
will pick them up automatically.

Re-running this script overwrites the existing credentials file.
"""
from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path

CRED_PATH = Path.home() / ".config" / "opencode" / "skills" / "search-subtitles" / ".credentials.json"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Configurando credenciales de OpenSubtitles")
    print(f"Destino: {CRED_PATH}")
    print()

    user = input("Usuario OpenSubtitles: ").strip()
    if not user:
        print("ERROR: usuario vacio.", file=sys.stderr)
        return 2

    password = getpass.getpass("Contrasena OpenSubtitles: ")
    if not password:
        print("ERROR: contrasena vacia.", file=sys.stderr)
        return 2

    CRED_PATH.parent.mkdir(parents=True, exist_ok=True)
    CRED_PATH.write_text(
        json.dumps({"user": user, "pass": password}, indent=2),
        encoding="utf-8",
    )
    try:
        os.chmod(CRED_PATH, 0o600)
    except OSError:
        pass

    print(f"\nOK -> Credenciales guardadas en {CRED_PATH}")
    print("No se volveran a pedir en futuros usos de download_subs.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
