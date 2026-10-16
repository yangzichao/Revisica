# Third-party licenses shipped in the Revisica DMG

Revisica itself is licensed under GPL-3.0-or-later; its license text ships
as `Contents/Resources/LICENSE` next to this folder.

Revisica bundles Pandoc to parse LaTeX input. Pandoc is released under
GPL-2.0-or-later; the About dialog links to this folder so redistributing the
binary stays compliant.

| File | Component | License | Upstream |
|---|---|---|---|
| `pandoc-GPL2.txt` | Pandoc | GPL-2.0-or-later | https://github.com/jgm/pandoc |
| `pandoc-COPYRIGHT.txt` | Pandoc | Mixed (see file) | https://github.com/jgm/pandoc/blob/main/COPYRIGHT |

The bundled binary is the official arm64 macOS build from the Pandoc
releases page; `scripts/pyinstaller/install-arm64-pandoc.sh` pins its version
and checksum. The exact matching source is the same tag in
<https://github.com/jgm/pandoc> (currently `3.9`).
