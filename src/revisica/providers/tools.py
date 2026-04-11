"""Local tool implementations for API providers.

When using direct API calls (Anthropic/OpenAI), agents can't use the
CLI's built-in sandbox tools.  These functions provide equivalent
Read/Glob/Grep functionality executed locally in the Python process.
"""

from __future__ import annotations

import re
from pathlib import Path

# ── tool definitions (for API tool_use schemas) ─────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "Read",
        "description": "Read the contents of a file at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file to read.",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "Glob",
        "description": "Find files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. '**/*.tex').",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to current directory.",
                    "default": ".",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "Grep",
        "description": "Search file contents for a regex pattern, returning matching lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in.",
                },
            },
            "required": ["pattern", "path"],
        },
    },
]


# ── tool execution ──────────────────────────────────────────────────


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a string."""
    if tool_name == "Read":
        return tool_read(tool_input["file_path"])
    if tool_name == "Glob":
        return tool_glob(tool_input["pattern"], tool_input.get("path", "."))
    if tool_name == "Grep":
        return tool_grep(tool_input["pattern"], tool_input["path"])
    return f"Unknown tool: {tool_name}"


def tool_read(file_path: str) -> str:
    """Read and return the contents of a file."""
    target = Path(file_path).expanduser().resolve()
    if not target.exists():
        return f"Error: file not found: {target}"
    if not target.is_file():
        return f"Error: not a file: {target}"
    try:
        return target.read_text(encoding="utf-8")
    except Exception as error:
        return f"Error reading {target}: {error}"


def tool_glob(pattern: str, search_path: str = ".") -> str:
    """Find files matching a glob pattern, returning paths one per line."""
    base = Path(search_path).expanduser().resolve()
    matches = sorted(str(match) for match in base.glob(pattern))
    if not matches:
        return "No files matched."
    return "\n".join(matches[:200])


def tool_grep(pattern: str, search_path: str) -> str:
    """Search for a regex pattern in files, returning matching lines."""
    target = Path(search_path).expanduser().resolve()
    results: list[str] = []

    try:
        compiled_pattern = re.compile(pattern)
    except re.error as error:
        return f"Invalid regex: {error}"

    if target.is_file():
        results.extend(_grep_file(target, compiled_pattern))
    elif target.is_dir():
        for child in sorted(target.rglob("*")):
            if child.is_file() and child.suffix in (
                ".tex", ".md", ".txt", ".py", ".bib", ".cls", ".sty", ".bbl",
                ".json", ".yaml", ".yml", ".csv", ".rst",
            ):
                results.extend(_grep_file(child, compiled_pattern))
                if len(results) > 200:
                    break
    else:
        return f"Error: path not found: {target}"

    if not results:
        return "No matches found."
    return "\n".join(results[:200])


def _grep_file(file_path: Path, pattern: re.Pattern) -> list[str]:
    """Search a single file for lines matching a pattern."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    matches = []
    for line_number, line in enumerate(content.split("\n"), start=1):
        if pattern.search(line):
            matches.append(f"{file_path}:{line_number}:{line.rstrip()}")
    return matches
