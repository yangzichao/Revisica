"""Fail unless every recorded version agrees (and matches the tag, if given).

Usage:
    python3 scripts/release/check_release_version.py           # versions agree
    python3 scripts/release/check_release_version.py v0.2.0    # ... and match the tag
"""

from __future__ import annotations

import sys

from release_version_sources import is_valid_release_version, read_recorded_versions


def main(arguments: list[str]) -> int:
    if len(arguments) > 1:
        print(__doc__, file=sys.stderr)
        return 2

    recorded_versions = read_recorded_versions()
    distinct_versions = set(recorded_versions.values())
    if len(distinct_versions) != 1:
        print("Recorded versions disagree:", file=sys.stderr)
        for location, version in recorded_versions.items():
            print(f"  {location}: {version}", file=sys.stderr)
        print("Fix with: python3 scripts/release/set_release_version.py X.Y.Z", file=sys.stderr)
        return 1

    (recorded_version,) = distinct_versions
    if not is_valid_release_version(recorded_version):
        print(f"Recorded version {recorded_version!r} is not X.Y.Z or X.Y.Z-rc.N", file=sys.stderr)
        return 1

    if arguments:
        tag = arguments[0]
        expected_tag = f"v{recorded_version}"
        if tag != expected_tag:
            print(
                f"Tag {tag!r} does not match the recorded version {recorded_version!r} "
                f"(expected tag {expected_tag!r}).",
                file=sys.stderr,
            )
            return 1

    print(f"Release version {recorded_version} is consistent across {len(recorded_versions)} locations.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
