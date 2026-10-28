# TODO: Post title

> **Read the post:** _not yet published_ · **Authors:** TODO
> **Code release:** _pending_ · **Data (CC0):** _none / pending_

One-paragraph summary of what the post shows and what a reader can reproduce here.

## Reproduce a figure

Every figure in the post is one standalone script in [`figures/`](figures/). With
[uv](https://docs.astral.sh/uv/) installed:

```bash
cd figures
uv run make_<name>.py
```

That's all it needs: dependencies are declared in the script and the data it
plots is the `<name>.tsv` beside it. Each PNG also carries its own script in
its metadata (see [`figures/README.md`](figures/README.md)).

To rebuild the figure tables from the raw inputs:

```bash
uv sync
uv run blog-data fetch .                     # only if data/manifest.tsv lists large files
uv run python code/<processing script>.py    # writes figures/<name>.tsv
```

## Contents

| Path | What it is |
|---|---|
| `figures/` | One standalone script + source table + outputs + caption per figure |
| `code/` | Processing that turns `data/` into the figure tables |
| `data/` | Small inputs (committed); `manifest.tsv` lists large files on Zenodo |
| `post.toml` | Metadata for the repo index and releases |

## Methods

Data sources (URL + access date), identifiers and mappings used, filters and
thresholds, `n` at each step, and known limitations.

## Cite

Authors (Year). *Title*. Deliverome blog. URL. Code: DOI (release `<slug>-v1`).
Data: DOI.
