# Third-party licenses shipped in the Revisica DMG

Revisica bundles Pandoc (via `pypandoc-binary`) to parse LaTeX input. Pandoc
is released under GPL-2.0-or-later; the About dialog links to this folder so
redistributing the binary stays compliant.

| File | Component | License | Upstream |
|---|---|---|---|
| `pandoc-GPL2.txt` | Pandoc | GPL-2.0-or-later | https://github.com/jgm/pandoc |
| `pandoc-COPYRIGHT.txt` | Pandoc | Mixed (see file) | https://github.com/jgm/pandoc/blob/main/COPYRIGHT |

Source code for the bundled Pandoc binary is available at
<https://github.com/jgm/pandoc>. To obtain the exact source matching the
shipped binary, inspect `pypandoc._pandoc_version` inside the frozen
`python-backend` and check out the matching tag from the Pandoc repo.
