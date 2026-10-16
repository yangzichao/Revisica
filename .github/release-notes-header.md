## Install on macOS (Apple Silicon)

Download the `revisica-*-arm64.dmg` below, open it, and drag Revisica to Applications.

This build is not notarized by Apple yet, so macOS blocks the first launch. To open it anyway:

1. Launch Revisica once and dismiss the warning.
2. Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the Revisica message.

Or clear the download quarantine from a terminal:

```bash
xattr -dr com.apple.quarantine /Applications/Revisica.app
```

## Install the CLI

```bash
pip install revisica-*.whl   # the wheel attached below
revisica bootstrap
```

## Verify a download

Every asset below has a build provenance attestation from this repository's release workflow:

```bash
gh attestation verify <downloaded-file> --repo yangzichao/Revisica
```
