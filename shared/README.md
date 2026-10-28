# deliverome-blog-utils

Shared helpers every post depends on. See the repo [CLAUDE.md](../CLAUDE.md#shared-utilities) for the rules.

- `plotting` -- `setup_plotting_style()`, palettes, `create_figure()`
- `provenance` -- `save_figure(fig, name, source_data=df)` writes PNG + PDF + source TSV + `MANIFEST.tsv`
- `data` -- `blog-data fetch posts/<slug>` / `blog-data hash FILE...` for large external datasets

Fonts: Manrope (SIL Open Font License 1.1, see `src/deliverome_blog_utils/fonts/OFL.txt`).

```bash
cd shared && uv run pytest
```
