# Releasing Revisica

A release is a `vX.Y.Z` tag on `main`. Pushing the tag runs `.github/workflows/release.yml`, which publishes a GitHub Release with:

- `revisica-X.Y.Z-arm64.dmg` (desktop app, Apple Silicon, macOS 11+, ad-hoc signed and not notarized)
- `revisica-X.Y.Z-py3-none-any.whl` and `revisica-X.Y.Z.tar.gz` (CLI)
- a build provenance attestation for each file

## Where the version lives

| Location | Role |
|---|---|
| `src/revisica/__init__.py` (`__version__`) | Python source of truth. `pyproject.toml` reads it (`dynamic = ["version"]`); `api.py` and `bootstrap_assets.py` import it. |
| `desktop/package.json` (`version`) | Desktop source of truth. The DMG file name and the Help page read it. |
| `desktop/package-lock.json` (two `version` fields) | Mirrors `package.json`. |

Never edit these by hand. `tests/test_release_version_sources.py` fails on every PR if they disagree, and the release workflow refuses a tag that does not match them.

## Cutting a release

1. On a branch, set the version and open a PR:

   ```bash
   python3 scripts/release/set_release_version.py 0.2.0
   git commit -am "Release 0.2.0"
   ```

   Use `0.2.0-rc.1` (or `-alpha.N` / `-beta.N`) for a prerelease; the workflow marks the GitHub Release as a prerelease.

2. Merge the PR once the `pytest` check passes.

3. Tag the merge commit on `main` and push the tag:

   ```bash
   git switch main && git pull --ff-only
   python3 scripts/release/check_release_version.py v0.2.0
   git tag -a v0.2.0 -m "Revisica 0.2.0"
   git push origin v0.2.0
   ```

4. Watch the `release` workflow. Its jobs:
   - `check-version`: the tag must match every recorded version.
   - `tests`: the full suite on the tagged commit (`tests.yml`).
   - `dmg`: the DMG build (`build-dmg.yml`): frozen-backend smoke test, LZMA recompression, a `codesign --verify` of the app inside the DMG, and the 220 MB size budget.
   - `python-dist`: wheel and sdist.
   - `publish`: attests every file, then creates the GitHub Release with generated notes, prefixed by `.github/release-notes-header.md`.

   If any job fails, nothing is published. Fix forward on `main`, delete the tag (`git push origin :v0.2.0 && git tag -d v0.2.0`), and tag again.

## Code signing

There is no Apple Developer ID yet. electron-builder skips signing and `desktop/build/adhoc-sign-mac-app.cjs` ad-hoc signs the app so the bundle stays valid. Users have to approve the first launch in System Settings (the release notes explain how).

To ship signed and notarized builds:

1. Add `CSC_LINK`, `CSC_KEY_PASSWORD`, `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD` and `APPLE_TEAM_ID` as repository secrets.
2. In `build-dmg.yml`, drop `CSC_IDENTITY_AUTO_DISCOVERY: 'false'` and pass the secrets to the build step.
3. Set `notarize: true` in `desktop/electron-builder.yml`. The hardened-runtime entitlements are already in `desktop/build/entitlements.mac.plist`.
4. Update `.github/release-notes-header.md` to drop the "Open Anyway" instructions.

## Bundled Pandoc

`pypandoc-binary`'s arm64 wheel ships an x86_64 pandoc, so `scripts/pyinstaller/install-arm64-pandoc.sh` swaps in the official arm64 build before freezing. To move to a newer Pandoc, update `PANDOC_VERSION` and `PANDOC_ARM64_ZIP_SHA256` there (the digest is on the release asset: `gh api repos/jgm/pandoc/releases/tags/<version> --jq '.assets[] | select(.name|test("arm64-macOS.zip")) | .digest'`), and the version mentioned in `desktop/resources/LICENSES/README.md`.
