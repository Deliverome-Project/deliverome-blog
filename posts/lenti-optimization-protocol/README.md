# Optimizing lentivirus production

> **Substack:** _not yet published_ · **Authors:** Maria ter Weele · **Data:** TODO (DOI or "all in this folder")

> **Placeholder post.** Structure only; protocol, data, and figures to come from Maria.

The full protocol is in [`protocol/protocol.md`](protocol/protocol.md) and reagents in
[`protocol/reagents.tsv`](protocol/reagents.tsv). The optimization data behind each
choice is in `data/`, and `code/make_figures.py` regenerates every figure in the post.

## Contents

| Path | What it is |
|---|---|
| `post.toml` | Metadata used by the repo index |
| `protocol/` | Bench protocol (`protocol.md`) and reagent list (`reagents.tsv`) |
| `code/` | Analysis and figure scripts (`make_figures.py` regenerates every figure) |
| `data/` | Small inputs committed directly; `data/manifest.tsv` lists large files hosted elsewhere |
| `figures/` | Generated figures, each with its source-data TSV and `MANIFEST.tsv` |

## Reproduce

```bash
cd posts/lenti-optimization-protocol
uv sync
uv run blog-data fetch .           # only if data/manifest.tsv lists external files
uv run python code/make_figures.py
```

## Methods

Data sources (URL + access date), identifiers and mappings used, filters and
thresholds, `n` at each step, and known limitations.

## Citation

Authors (Year). *Title*. Deliverome blog. URL. Code and data: this folder at
commit `<published_commit>`; large data: DOI.
