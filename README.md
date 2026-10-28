# Deliverome blog: code and data

Every post on the [Deliverome Substack](https://deliverome.substack.com) that
shows data has a folder here with the complete code and data behind it, so any
figure can be regenerated and any number checked.

## Posts

<!-- POSTS:START -->
| Date | Post | Authors | Code & data | Large data |
|---|---|---|---|---|
| | _No posts published yet_ | | | |

**In progress**

- [Optimizing lentivirus production](posts/lenti-optimization-protocol) — Maria ter Weele
<!-- POSTS:END -->

## Reproducing a post

Each post folder is a self-contained [uv](https://docs.astral.sh/uv/) project.

```bash
git clone https://github.com/Deliverome-Project/deliverome-blog.git
cd deliverome-blog/posts/<slug>
uv sync                              # installs the post's pinned environment
uv run blog-data fetch .             # downloads large data, if the post has any
uv run python code/make_figures.py   # regenerates every figure in figures/
```

Each figure in `figures/` sits next to a `.tsv` of the exact values plotted,
and `figures/MANIFEST.tsv` records the script and commit that produced it. To
see a post exactly as published, check out the `published_commit` in its
`post.toml`.

Large datasets live on [Zenodo](https://zenodo.org) (or a domain repository
such as SRA or the BioImage Archive) and are listed with checksums in each
post's `data/manifest.tsv`.

## Repository layout

```
posts/<slug>/   one folder per post: README, code/, data/, figures/
posts/_template/  starting point for new posts
shared/         deliverome-blog-utils: plotting style, save_figure, data fetching
scripts/        repo tooling: new_post.py, build_index.py
```

## License

Code is [MIT](LICENSE). Text, figures, and data are
[CC BY 4.0](LICENSE-CONTENT.md) unless a post's README says otherwise.
Third-party data keeps its original license, noted in each post's
`data/README.md`.
