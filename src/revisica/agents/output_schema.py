"""JSON output schemas shipped inside the package.

They live next to the code (not at the repo root) so a pip-installed or
PyInstaller-frozen backend finds them without depending on the CWD.
"""

from __future__ import annotations

from pathlib import Path

OUTPUT_SCHEMAS_DIR = Path(__file__).resolve().parent / "output_schemas"


def findings_schema_path() -> str:
    """Path to the findings schema passed to Codex ``--output-schema``."""
    return str(OUTPUT_SCHEMAS_DIR / "findings.schema.json")
