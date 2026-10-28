# TODO: Post title

> **Substack:** _not yet published_ · **Authors:** TODO · **Data:** TODO (DOI or "all in this folder")

One-paragraph summary of what the post shows and what a reader can reproduce here.

## Contents

| Path | What it is |
|---|---|
| `post.toml` | Metadata used by the repo index |
| `code/` | Analysis and figure scripts (`make_figures.py` regenerates every figure) |
| `data/` | Small inputs committed directly; `data/manifest.tsv` lists large files hosted elsewhere |
| `figures/` | Generated figures, each with its source-data TSV and `MANIFEST.tsv` |

## Reproduce

```bash
cd posts/<slug>
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
