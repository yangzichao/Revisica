"""Set the release version in every file that records it.

Usage:
    python3 scripts/release/set_release_version.py 0.2.0
    python3 scripts/release/set_release_version.py 0.2.0-rc.1
"""

from __future__ import annotations

import sys

from release_version_sources import read_recorded_versions, write_release_version


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print(__doc__, file=sys.stderr)
        return 2

    try:
        write_release_version(arguments[0])
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    for location, version in read_recorded_versions().items():
        print(f"{location}: {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
