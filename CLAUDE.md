# CLAUDE.md

Instructions for Claude Code and other agents working in this repository.
`AGENTS.md` is a symlink to this file.

## What this repo is

The code and data behind every data-bearing post on the Deliverome Substack
(<https://deliverome.substack.com>; site <https://deliverome.org>).
**One post = one folder under `posts/<slug>/`**, complete enough that a stranger
can regenerate every figure and check every number in the post from that
folder alone.

The repo starts **private** and will be made **public**. Write everything as if
it is already public: git history becomes public with it, so anything committed
once is published (see [Before going public](#before-going-public)).

## Layout

```
README.md            visitor-facing intro + post index (generated between POSTS markers)
CLAUDE.md            this file (AGENTS.md -> CLAUDE.md)
LICENSE              MIT (code)
LICENSE-CONTENT.md   CC0 (data), CC BY 4.0 (text/figures/protocols)
CITATION.cff         repo-level citation; per-post DOIs are in the index
.zenodo.json         Zenodo metadata for the next release (written by release_post.py prepare)
people.toml          author name -> Zenodo creator (Family, Given / affiliation / ORCID)
assets/fonts/        Manrope (OFL); figure scripts find it by walking up from themselves
shared/              deliverome-blog-utils: brand_style, blog-figure, blog-data (+ zenodo)
scripts/
  new_post.py        scaffold posts/<slug>/ from posts/_template/
  build_index.py     regenerate the README index; --check validates every post (CI)
  release_post.py    prepare .zenodo.json, then tag a post's GitHub release
posts/
  _template/         copied by new_post.py; edit it to change future posts
  <slug>/
    README.md        what the post shows, links, how to reproduce, methods, citation
    post.toml        metadata: status, version, DOIs, Substack URL
    pyproject.toml   post environment for code/ and the blog-* commands; uv.lock committed
    figures/         per figure: make_<name>.py, <name>.tsv, .png, .pdf, .caption.md; README.md
    code/            processing from data/ to figures/<name>.tsv (never plots)
    data/
      README.md      every input: source URL, date, license
      manifest.tsv   large files on Zenodo: path, url, sha256, size_bytes, description
      zenodo.json    the post's Zenodo data deposition (written by blog-data zenodo push)
      external/      large files, local only (gitignored)
    protocol/        wet-lab posts only: protocol.md + reagents.tsv
```

## Adding a post

1. `uv run scripts/new_post.py <slug> --title "..." --author "Full Name"`.
   Slugs are kebab-case, have no date, and **never change** once published
   (they are in links, tags, and DOIs). Add any new author to `people.toml`.
2. Inputs: small ones in `data/`, large ones in `data/external/` (see
   [Data](#data)). Document each in `data/README.md`.
3. Processing scripts in `code/` write one tidy table per figure,
   `figures/<name>.tsv`. Commit those tables.
4. For each figure, `uv run blog-figure new . <name>` (from the post folder),
   fill in its docstring and `plot()`, then `cd figures && uv run make_<name>.py`.
   Write `<name>.caption.md` and list the figure in `figures/README.md`.
5. Fill in the post README (methods, `n`s, limitations), then
   `uv run scripts/build_index.py` and open a PR.

Wet-lab protocol posts also get `protocol/protocol.md` (numbered bench steps
with volumes, timings, and the reason for any non-standard step) and
`protocol/reagents.tsv` (item, vendor, catalog_number, amount_per_prep, notes).

## Figures

Figures follow accessible-surfaceome's final-figure convention. **Each figure is
one standalone reproduction unit** in `posts/<slug>/figures/`:

| File | Rule |
|---|---|
| `make_<name>.py` | Runs with `uv run make_<name>.py` and nothing else: a PEP 723 header pins its dependencies, and the brand style block is **pasted in, never imported** from `shared/`. It only plots. |
| `<name>.tsv` | The exact values plotted, tidy, read **sibling-first**: the TSV beside the script, else the copy at the post's release tag on GitHub (`DATA_URL`). |
| `<name>.png` | 1456 px wide (2x the Substack column), for upload to Substack. Its metadata carries `Source` (the script's URL at the release tag) and `Script` (the script's **full source**), so the image alone is enough to regenerate it. |
| `<name>.pdf` | Vector copy, with the script URL in `Subject`. |
| `<name>.caption.md` | The caption as it appears on Substack. Figures carry no in-figure titles. |

Rules:

- Scaffold with `blog-figure new`; it pastes the current style block and fills
  `POST`, `FIGURE`, `RELEASE_TAG` (`<slug>-v<version>`), and the URLs.
- Always generate outputs with `uv run make_<name>.py` (the script's own pinned
  environment), from a committed script. The release step re-runs every script
  and refuses to release if any output changes.
- Use the block's `COLORS`, `CATEGORICAL_PALETTE`, `sequential_palette()` and
  `diverging_palette()`, never ad hoc hex codes. Use seaborn on a tidy
  DataFrame. Label axes with units and method, e.g. "Functional titer (TU/mL,
  flow, % GFP+)".
- Heavy computation belongs in `code/`, which writes the TSV; the figure script
  only reads it, so re-plotting is fast and needs no raw data.
- `blog-figure check` (CI) enforces all of this. It also requires PNG metadata
  to match the current script, so edit a script and you must re-run it.
- `blog-figure extract <name>.png` prints the script embedded in a PNG.

**Changing the style:** edit the block in
`shared/src/deliverome_blog_utils/brand_style.py`, bump its sentinel version,
then run `uv run --project shared blog-figure sync` and re-run the affected
figure scripts. Sync touches draft posts only. Published posts keep the style
they were released with, because their scripts are frozen at their tag.

## Data

GitHub warns at 50 MB and rejects files over 100 MB, and clones should stay
fast. `build_index.py --check` fails CI on any tracked file over 25 MB.

| Size per file | Where it goes |
|---|---|
| < 25 MB | Commit it in `posts/<slug>/data/` (or `figures/` for figure tables). |
| 25 MB – ~50 GB per post (the usual "multi-GB" case) | A **Zenodo data record**, one per post, CC0, via `blog-data zenodo push`. |
| Raw data with a standard archive | The domain repository: SRA/ENA (sequencing), GEO (processed expression), PRIDE (proteomics), BioImage Archive (imaging). Link it from the post README. |
| > 50 GB, or needs streaming/range reads (e.g. Zarr) | Public Cloudflare R2 bucket, listed in `data/manifest.tsv` the same way. Ask before creating one. |

**Licensing:** data we produce is **CC0 1.0** (Astera open-science guidelines),
both in this repo and on Zenodo. Third-party data keeps its license: record it
in `data/README.md`, and if redistribution isn't allowed, don't commit or
upload it; list its original URL in `manifest.tsv` instead.

**Why Zenodo:** it is free (50 GB and 100 files per record), permanent (run by
CERN), and gives a citable DOI per version. Readers download from it without
logging in, and published files are immutable, so manifest checksums stay
valid.

**Why not Git LFS:** in a public repo, every clone, fork, and CI run downloads
LFS objects against the org's paid bandwidth quota. LFS also gives no DOI, caps
file size at a few GB, and cannot cleanly purge a file from history.

**Make figures work without the big download.** Commit the figure tables
(small), so every figure regenerates from a fresh clone; the large files are
only needed to re-run `code/`. Optionally commit a small subsample so the
processing code can be exercised.

### Zenodo data record workflow

Auth: a Zenodo personal access token with `deposit:write` and `deposit:actions`
in `ZENODO_TOKEN`. Never commit it. To rehearse, use `ZENODO_SANDBOX_TOKEN`
with `--sandbox` (sandbox.zenodo.org, separate account).

1. Put the large files in `posts/<slug>/data/external/` (gitignored). Tar any
   directory with many files; Zenodo allows 100 files per record and stores them flat.
2. `uv run blog-data zenodo push . --dry-run` (from the post folder) shows the metadata and files.
3. `uv run blog-data zenodo push .` creates the draft with a reserved DOI on the
   first run; later runs update it, uploading only changed files. It writes
   `data/manifest.tsv` (URLs, SHA256, sizes), `data/zenodo.json`, and
   `post.toml` `data_doi`. Fill in the manifest descriptions and commit.
   Metadata: CC0 dataset, creators from `people.toml`, linked to the post folder
   and the Substack post. Set `ZENODO_COMMUNITY` to also request a community.
4. **Never publish from code.** Publishing is irreversible: files freeze and the
   DOI registers. A person reviews the draft on zenodo.org and clicks Publish
   when the post goes live. Manifest URLs resolve only after that.
5. A correction after publication: `push` again. It opens a new version of the
   same record (same concept DOI, new version DOI).

Readers (and you, to verify) run `uv run blog-data fetch .`, which downloads,
checks size and SHA256, and logs to `data/external/FETCH_LOG.tsv`.

## Releasing a post (code DOI)

Every post gets its own GitHub release, tagged `<slug>-v<version>`. The
GitHub-Zenodo integration archives each release as a new version of this
repo's Zenodo **software** record, with its own DOI. Only published GitHub
releases are archived, not drafts.

**One-time setup** (needs a person; see [Before going public](#before-going-public)):
the repo must be public, then on <https://zenodo.org/account/settings/github/>
click "Sync now" and toggle `Deliverome-Project/deliverome-blog` on. Check
that it worked with `gh api repos/Deliverome-Project/deliverome-blog/hooks`,
which should list a zenodo.org hook.

When the post is ready to go live:

1. Final PR: set `status = "published"`, `published`, and `substack_url` in
   `post.toml` (the Substack draft URL is known before publishing). Remove
   every TODO. Run `uv run scripts/release_post.py prepare <slug>`, which
   writes `.zenodo.json` (authors, version tag, links to the post and data
   DOI), and commit it. Merge.
2. Publish the Zenodo data record, if the post has one.
3. On an up-to-date main: `uv run scripts/release_post.py tag <slug>` (dry
   run). It checks the tree is clean, the post and figures pass, every figure
   re-runs byte-identically, and every data URL downloads. Then run it again
   with `--execute` to create the GitHub release. Ask the user before
   `--execute`: releases are public and archived permanently.
4. Within minutes Zenodo mints the version DOI. Put it in `post.toml`
   `code_doi`, run `uv run scripts/build_index.py`, and merge. Add both DOIs
   to the Substack post.

**Corrections after publication:** fix the post folder, bump `version` in
`post.toml`, and run `blog-figure sync` to update `RELEASE_TAG`. Re-run the
figures, add a dated `## Changelog` entry to the post README, and release
again (`prepare` → merge → `tag`). Earlier releases stay citable.

Once the repo is public, unpublished drafts stay on branches until their post
goes live, because anything on `main` is visible. While it is private, drafts
may merge to `main` with `status = "draft"`.

## Analysis standards

Posts are public scientific claims, so hold them to the same bar as
deliverome-internal:

- Join on stable identifiers (Ensembl, UniProt, HGNC IDs); use gene symbols only
  as a documented fallback.
- Print counts at every step (rows in, after filtering, final `n` per test), and
  keep `n` visible in figures or their TSVs.
- Record data sources with URL and access date in `data/README.md`. Put the
  methods summary in the figure script docstrings and the post README.
- Keep manual curation (plate maps, exclusions, sample labels) in committed text
  files, not spreadsheet edits.

## Never commit

- Secrets, `.env` files, tokens (including `ZENODO_TOKEN`), or credentials.
- Personal data: patient or donor identifiers, names in sample sheets, emails.
- Unpublished results outside the post, internal ELN links, or internal Notion/Slack URLs.
- Files over 25 MB (see [Data](#data)).
- Third-party data whose license forbids redistribution.

## Before going public

Run through this before flipping visibility:

1. `gitleaks detect --source . --log-opts="--all"` (scans full history) finds nothing.
2. `git log --all --stat` shows no unpublished data, PII, or internal links. If
   something leaked into history, rewrite it with `git filter-repo` *before*
   going public.
3. `uv run scripts/build_index.py --check` and `uv run --project shared blog-figure check` pass.
4. In GitHub settings, enable secret scanning, push protection, and branch protection on `main`.
5. Enable the Zenodo GitHub integration (above), then release any posts
   already published.

## Checks

```bash
uv run scripts/build_index.py --check                 # index, post structure, file sizes
uv run --project shared blog-figure check             # figure rules + PNG metadata current
cd shared && uv run pytest                            # shared tooling
```

CI (`.github/workflows/ci.yml`) runs all three on every PR.

## Git

- Main branch `main`; work on branches and merge by PR.
- PR titles: `<type>(<optional-scope>): <subject>`, type in
  `{feat, fix, docs, refactor, chore, ci, build, test}`. Use the post slug or
  `shared` as scope, e.g. `feat(lenti-optimization-protocol): add titer data`.
- Include the exact commands you ran to verify in the PR description.
