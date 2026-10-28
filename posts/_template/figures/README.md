# Figures

Each figure is a self-contained reproduction unit:

| File | What it is |
|---|---|
| `make_<name>.py` | Standalone script: `uv run make_<name>.py` (no repo install needed) |
| `<name>.tsv` | The exact values plotted |
| `<name>.png` / `.pdf` | Outputs; the PNG embeds the script's URL and full source |
| `<name>.caption.md` | The caption used on Substack |

Recover the script from a PNG with `uv run --project ../../../shared blog-figure extract <name>.png`
(or any EXIF viewer: the `Script` and `Source` text fields).

| Figure | Caption |
|---|---|
