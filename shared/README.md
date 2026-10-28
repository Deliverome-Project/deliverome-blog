# deliverome-blog-utils

Tooling shared by every post. The rules it enforces are in the repo
[CLAUDE.md](../CLAUDE.md#figures).

| Module | What it does |
|---|---|
| `brand_style` | Canonical Deliverome figure style (palette, Manrope, sizing, `save_figure` with embedded provenance). Pasted verbatim into every figure script; importable for notebooks. |
| `figures` | `blog-figure new / sync / check / extract` for standalone figure scripts |
| `data` | `blog-data fetch / hash` for large data listed in `data/manifest.tsv` |
| `zenodo` | `blog-data zenodo push` creates or updates a post's Zenodo data draft (never publishes) |

```bash
cd shared && uv run pytest
```
