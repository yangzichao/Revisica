"""Entrypoint for the PyInstaller-frozen backend.

`src/revisica/api.py` uses relative imports, so PyInstaller cannot freeze it
directly as a top-level script. This module imports the package normally and
forwards to `main()`. Keep it a single line of logic — all heavy lifting lives
in `revisica.api`.
"""

from __future__ import annotations

from revisica.api import main

if __name__ == "__main__":
    main()
