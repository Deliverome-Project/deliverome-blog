# Data

- **Committed here:** small inputs (< 25 MB each) such as plate maps, summary
  tables, and processed TSVs. List each one below with source and date.
- **Hosted externally:** anything larger is listed in `manifest.tsv` (URL,
  SHA256, size) and fetched into `external/` (gitignored) with
  `uv run blog-data fetch .` from the post folder. `uv run blog-data zenodo push .`
  creates or updates the Zenodo draft and writes `manifest.tsv` for you.

Data we produce is released under **CC0 1.0** (public domain). Third-party
data keeps its own license: note it in the table below, and do not commit it
if its terms forbid redistribution (link it from `manifest.tsv` instead).

| File | Source / how produced | Date | License | Description |
|---|---|---|---|---|
