# Deliverome blog: code and data

**[Deliverome](https://deliverome.org)** is building an open map of how to
deliver therapeutics into specific human cells. We write up our experiments,
protocols and analyses on our Substack,
**[deliverome.substack.com](https://deliverome.substack.com)**.

This repository holds everything behind those posts: for each post, the
scripts that make every figure, the data they plot, and any protocols. You can
regenerate any figure, check any number, or reuse the data in your own work.

## Posts

<!-- POSTS:START -->
| Date | Post | Authors | Code & figures | Code DOI | Data (CC0) |
|---|---|---|---|---|---|
| | _First post coming soon_ | | | | |

**In progress**

- [Optimizing lentivirus production](posts/lenti-optimization-protocol) — Maria ter Weele
<!-- POSTS:END -->

## Regenerate a figure

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/Deliverome-Project/deliverome-blog.git
cd deliverome-blog/posts/<post>/figures
uv run make_<figure>.py
```

Each figure script is standalone. It lists its own pinned dependencies, so
`uv run` sets up the right environment, and it plots the `<figure>.tsv` table
next to it. You can also download a single script and run it anywhere; it
fetches its table from this repository.

**Found a figure out of context?** Every PNG we publish carries the script
that made it and a link back here in its metadata. Read it with
`exiftool -Script figure.png` or any online EXIF viewer (look for the `Script`
and `Source` fields). Some sites, including Substack, strip image metadata, so
each post also links its folder here.

## Get the data

Small tables live in each post's `data/` and `figures/` folders. Larger
datasets are on [Zenodo](https://zenodo.org) with a DOI, and each post's
`data/manifest.tsv` lists them with checksums. To download and verify them:

```bash
cd posts/<post>
uv run blog-data fetch .
```

## Cite

Each post is archived on Zenodo as a GitHub release (`<post>-v1`) with its own
DOI, shown in the table above and on the post's page. Please cite the post and,
if you use the code or data, those DOIs.

## Licenses

| What | License |
|---|---|
| Data we produce | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): public domain, no permission needed |
| Code | [MIT](LICENSE) |
| Text, figures, protocols | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Third-party data | Its original license, noted in each post's `data/README.md` |

See [LICENSE-CONTENT.md](LICENSE-CONTENT.md) for details.

## Repository layout

```
posts/<post>/        one folder per Substack post
  figures/           make_<figure>.py + <figure>.tsv + .png/.pdf + caption, per figure
  code/              processing from raw data to figure tables
  data/              small inputs; manifest.tsv lists large files on Zenodo
  protocol/          bench protocols, for wet-lab posts
shared/              tooling: brand figure style, blog-figure and blog-data commands
scripts/             new_post.py, build_index.py, promote_post.py, release_post.py
docs/                WRITING_A_POST.md: guide for Deliverome scientists
assets/fonts/        Manrope, the brand font (SIL Open Font License)
```

Contributors: start with [CLAUDE.md](CLAUDE.md). Deliverome scientists writing a post:
see [docs/WRITING_A_POST.md](docs/WRITING_A_POST.md).

## Contact

Questions, corrections, or want to build on something here? Open an issue, or
reach us through [deliverome.org](https://deliverome.org).
