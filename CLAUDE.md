# CLAUDE.md

Instructions for Claude Code and other agents working in this repository.
`AGENTS.md` is a symlink to this file.

## What this repo is

The code and data behind every data-bearing post on the Deliverome Substack.
**One post = one folder under `posts/<slug>/`**, complete enough that a stranger
can regenerate every figure and check every number in the post from that
folder alone.

The repo starts **private** and will be made **public**. Write everything as if
it is already public: git history becomes public with it, so anything committed
once is published (see [Before going public](#before-going-public)).

## Layout

```
README.md            index of posts (generated between POSTS markers) + reader instructions
CLAUDE.md            this file (AGENTS.md -> CLAUDE.md)
LICENSE              MIT, for code
LICENSE-CONTENT.md   CC BY 4.0, for text, figures, data
shared/              deliverome-blog-utils package (plotting, save_figure, blog-data CLI)
scripts/
  new_post.py        scaffold posts/<slug>/ from posts/_template/
  build_index.py     regenerate the README index; --check validates every post (CI)
posts/
  _template/         copied by new_post.py; edit it to change future posts
  <slug>/
    README.md        what the post shows, Substack link, how to reproduce, methods, citation
    post.toml        metadata read by build_index.py
    pyproject.toml   the post's own uv project; uv.lock is committed
    .python-version
    code/            make_figures.py + any analysis scripts
    data/
      README.md      every committed file: source URL, date, how produced, license
      manifest.tsv   large files hosted elsewhere: path, url, sha256, size_bytes, description
      external/      fetched large files (gitignored)
    figures/         <name>.png/.pdf + <name>.tsv source data + MANIFEST.tsv (all generated)
    protocol/        wet-lab posts only: protocol.md + reagents.tsv
```

## Adding a post

1. `uv run scripts/new_post.py <slug> --title "..." --author "Full Name"`.
   Slugs are kebab-case and **never change** once published (they are in
   links), so pick a descriptive slug with no date.
2. Put inputs in `data/` (small) or list them in `data/manifest.tsv` (large;
   see [Data size policy](#data-size-policy)). Document every input in
   `data/README.md`.
3. Write `code/make_figures.py`. Add other dependencies with `uv add <pkg>`
   from the post folder; commit `uv.lock`.
4. Run `uv run python code/make_figures.py` from the post folder and commit the
   generated `figures/`.
5. Fill in the post README (methods, `n`s, limitations, citation).
6. `uv run scripts/build_index.py` to refresh the root README index, then open a PR.

Wet-lab protocol posts also get `protocol/protocol.md` (numbered bench steps
with volumes, timings, and the reason for any non-standard step) and
`protocol/reagents.tsv` (item, vendor, catalog_number, amount_per_prep, notes).

## Publishing a post

When the Substack post goes live:

1. Publish any Zenodo record and fill its real URLs into `data/manifest.tsv`.
2. In `post.toml`, set `status = "published"`, `published` (YYYY-MM-DD),
   `substack_url`, and `data_doi`. Remove every `TODO`.
3. Merge to `main`, then record that merge commit's SHA as `published_commit`
   in a follow-up commit. That SHA is the frozen state readers cite.
4. Link this post's folder from the Substack post
   (`https://github.com/Deliverome-Project/deliverome-blog/tree/main/posts/<slug>`).

After publication, a post's folder changes only for corrections. Add a dated
`## Changelog` entry in its README for each one, and do not change
`published_commit`.

Once the repo is public, unpublished drafts stay on branches (or out of this
repo) until their post goes live, because anything on `main` is visible. While
it is private, drafts may merge to `main` with `status = "draft"`.

## Shared utilities

`shared/` is the `deliverome-blog-utils` package. Every post depends on it
through a path source in its `pyproject.toml`. It is adapted from
`accessible-surfaceome`'s plotting config so blog figures match the papers and
site.

**Every figure script must:**

- Call `setup_plotting_style()` before creating any axes. It applies the
  Deliverome palette and the bundled Manrope font, with a transparent
  background and no in-figure titles (Substack captions replace them).
- Create figures with `create_figure()`, which sizes them for the Substack
  column and despines every axes.
- Take colours from `COLORS`, `CATEGORICAL_PALETTE`, `get_sequential_palette()`
  and `get_diverging_palette()`, never ad hoc hex codes.
- Save with `save_figure(fig, name, source_data=df)`. It writes
  `figures/<name>.png` (1456 px wide, 2x the Substack column, for upload),
  `<name>.pdf` (vector), and `<name>.tsv` (the exact values plotted; pass a
  dict for multi-panel figures). It also updates `figures/MANIFEST.tsv` with
  the generator script, source-data SHA256, git commit, and dirty flag, and
  embeds the post's GitHub URL in the PNG and PDF metadata. Never JPEG.
- Regenerate every figure from one entry point, `code/make_figures.py`.
  `save_figure` warns if the post folder has uncommitted changes; commit, then
  re-run before publishing so the manifest points at real code.
- For heavy pipelines, split a compute step that writes canonical TSVs into
  `data/` from a plot step that only reads them (`--mode compute|plot|all`).
  Commit the TSVs so readers can re-plot without the heavy step.

**Changing `shared/`:** published posts resolve it from the current checkout,
so changes must stay backward compatible. Add parameters with defaults or new
functions; never change an existing signature or default output. Run
`cd shared && uv run pytest` and re-run at least one existing post's
`make_figures.py` before merging. A reader who needs the exact published
styling checks out `published_commit`.

## Data size policy

GitHub warns at 50 MB and rejects files over 100 MB, and cloning should stay
fast. `build_index.py --check` fails CI on any tracked file over 25 MB.

| Size per file | Where it goes |
|---|---|
| < 25 MB | Commit directly in `posts/<slug>/data/`. |
| 25 MB – ~50 GB per post (the usual "multi-GB" case) | **Zenodo**, one record per post, listed in `data/manifest.tsv`. |
| Raw data with a standard archive | The domain repository: SRA/ENA (sequencing), GEO (processed expression), PRIDE (proteomics), BioImage Archive (imaging). |
| > 50 GB, or needs streaming/range reads (e.g. Zarr) | Public Cloudflare R2 bucket (no egress fees), listed in `data/manifest.tsv` the same way. Ask before creating one. |

**Why Zenodo for medium data:** it is free (50 GB and 100 files per record),
permanent (run by CERN), issues a citable DOI per version, and readers download
from it without a login. Files on a published record are immutable, so the
manifest SHA256s stay valid; a correction becomes a new version under the same
concept DOI.

**Why not Git LFS:** once the repo is public, every clone, fork, and CI run
downloads LFS objects against the org's paid bandwidth quota. LFS also gives no
DOI, caps file size at a few GB, and cannot purge a file from history cleanly.

**Workflow for a post with large data:**

1. Keep the large files local (or in team storage) under
   `posts/<slug>/data/external/`, which is gitignored.
2. Make the post reproducible **without** the large download wherever possible:
   commit the processed, figure-level TSVs (small) so `make_figures.py` runs
   from a fresh clone. The large files are only needed to re-run processing.
   Optionally commit a small subsample so the processing code can be exercised.
3. `uv run blog-data hash data/external/*` prints manifest rows (sha256, size)
   from your local originals. Paste them into `data/manifest.tsv`.
4. Create a Zenodo draft in the Deliverome community: title
   `Data for "<post title>"`, CC BY 4.0, the post authors, and a description
   linking this folder. Upload, and publish it when the post goes live.
5. Fill each manifest `url` with
   `https://zenodo.org/records/<id>/files/<name>?download=1` and set
   `data_doi` in `post.toml`.
6. Check end to end: `rm -rf data/external && uv run blog-data fetch .`.
   `fetch` verifies size and SHA256 and logs every file to
   `data/external/FETCH_LOG.tsv`.

## Analysis standards

Posts are public scientific claims, so hold them to the same bar as
deliverome-internal:

- Join on stable identifiers (Ensembl, UniProt, HGNC IDs); use gene symbols only
  as a documented fallback.
- Print counts at every step (rows in, after filtering, final `n` per test) and
  keep `n` visible in figures or their source TSVs.
- Record data sources with URL and access date in `data/README.md`, and the
  methods summary in `make_figures.py`'s docstring and the post README.
- Keep manual curation (plate maps, exclusions, sample labels) in committed text
  files, not spreadsheet edits.
- Label axes with units and the exact method, e.g. "Functional titer (TU/mL,
  flow, % GFP+)".

## Never commit

- Secrets, `.env` files, tokens, or credentials.
- Personal data: patient or donor identifiers, names in sample sheets, emails.
- Unpublished results that are not part of the post, internal ELN links, or
  internal Notion/Slack URLs.
- Files over 25 MB (see the data size policy).
- Third-party data whose license forbids redistribution. Link to it and fetch
  it via `manifest.tsv` instead.

## Before going public

Run through this before flipping visibility, and again before merging any post
that brings in new data:

1. `gitleaks detect --source . --log-opts="--all"` (scans full history) finds nothing.
2. `git log --all --stat` contains no unpublished data, PII, or internal links.
   If something leaked into history, rewrite it with `git filter-repo` *before*
   going public.
3. `uv run scripts/build_index.py --check` passes.
4. Every published post's Zenodo DOI resolves and `blog-data fetch` succeeds.
5. Licenses: `LICENSE` and `LICENSE-CONTENT.md` are present, and third-party
   data terms are noted per post.
6. In GitHub settings, enable secret scanning, push protection, and branch
   protection on `main`.

## Checks

```bash
uv run scripts/build_index.py --check   # index current, post structure valid, no oversized files
cd shared && uv run pytest               # shared utils
```

CI (`.github/workflows/ci.yml`) runs both on every PR.

## Git

- Main branch `main`; work on branches and merge by PR.
- PR titles: `<type>(<optional-scope>): <subject>`, type in
  `{feat, fix, docs, refactor, chore, ci, build, test}`. Use the post slug or
  `shared` as scope, e.g. `feat(lenti-optimization-protocol): add titer data`.
- Include the exact commands you ran to verify in the PR description.
