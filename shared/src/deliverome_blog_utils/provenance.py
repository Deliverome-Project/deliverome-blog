"""Save a figure together with the data it plots and a provenance record.

Every figure in a post is saved through :func:`save_figure`, which writes into
``posts/<slug>/figures/``:

- ``<name>.png``  -- 2x Substack column width (1456 px), for upload to Substack
- ``<name>.pdf``  -- vector copy for print / reuse
- ``<name>.tsv``  -- the exact values plotted (one TSV per panel for dicts)
- ``MANIFEST.tsv`` -- one row per figure: generator script, source-data
  SHA256, and the git commit + dirty flag of the tree that generated it

PNG and PDF carry a link back to the post folder on GitHub in their metadata
(PNG ``Source`` chunk, PDF ``Subject``), so a figure found out of context still
points to its code. Creation dates are stripped so unchanged inputs give
unchanged files.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import warnings
from pathlib import Path

import pandas as pd

from deliverome_blog_utils.plotting import WEB_WIDTH_PX

REPO_URL = "https://github.com/Deliverome-Project/deliverome-blog"
MANIFEST_COLUMNS = ["figure", "generator", "source_data", "source_data_sha256", "git_commit", "git_dirty"]


def find_post_dir(start: Path) -> Path:
    """Return the nearest ancestor of ``start`` that contains ``post.toml``."""
    for parent in [start, *start.parents]:
        if (parent / "post.toml").is_file():
            return parent
    raise FileNotFoundError(f"No post.toml above {start}; figure scripts must live inside posts/<slug>/")


def _git(args: list[str], cwd: Path) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest_rows(manifest: Path, rows: list[dict]) -> None:
    """Upsert rows keyed on (figure, source_data); keep the file sorted."""
    existing: dict[tuple[str, str], dict] = {}
    if manifest.exists():
        with manifest.open(newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                existing[(row["figure"], row["source_data"])] = row
    for row in rows:
        existing[(row["figure"], row["source_data"])] = row
    with manifest.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow(existing[key])


def save_figure(
    fig,
    name: str,
    *,
    source_data: pd.DataFrame | dict[str, pd.DataFrame],
    script: str | Path | None = None,
    formats: tuple[str, ...] = ("png", "pdf"),
) -> Path:
    """Save ``fig`` and its source data into the post's ``figures/`` folder.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save.
    name : str
        Base filename, kebab- or snake-case, no extension (e.g. ``"titer-vs-moi"``).
    source_data : DataFrame or dict of DataFrames
        The values plotted, in tidy form. Required: a reader must be able to
        re-plot or re-analyse the figure without re-running the pipeline. Pass
        a dict ``{"a": df_a, "b": df_b}`` for multi-panel figures.
    script : path, optional
        The generator script. Defaults to the running ``__main__`` script.
    formats : tuple of str
        Image formats. PNG is sized for Substack; PDF/SVG are vector.

    Returns
    -------
    Path
        The ``figures/`` directory written to.
    """
    script_path = Path(script or sys.argv[0]).resolve()
    post_dir = find_post_dir(script_path.parent)
    out_dir = post_dir / "figures"
    out_dir.mkdir(exist_ok=True)

    repo_root = Path(_git(["rev-parse", "--show-toplevel"], post_dir) or post_dir)
    commit = _git(["rev-parse", "HEAD"], repo_root)
    dirty = bool(_git(["status", "--porcelain", "--", str(post_dir.relative_to(repo_root))], repo_root))
    if dirty:
        warnings.warn(
            f"{post_dir.name} has uncommitted changes; commit and re-run before publishing so "
            "MANIFEST.tsv points at the exact code that made this figure.",
            stacklevel=2,
        )

    source_url = f"{REPO_URL}/tree/main/{post_dir.relative_to(repo_root).as_posix()}"
    width_in = fig.get_size_inches()[0]
    for fmt in formats:
        kwargs: dict = {"format": fmt}
        if fmt == "png":
            kwargs["dpi"] = WEB_WIDTH_PX / width_in
            kwargs["metadata"] = {"Source": source_url}
        elif fmt == "pdf":
            kwargs["metadata"] = {"Subject": source_url, "CreationDate": None, "ModDate": None}
        elif fmt == "svg":
            kwargs["metadata"] = {"Source": source_url, "Date": None}
        elif fmt in {"jpg", "jpeg"}:
            raise ValueError("JPEG drops the transparent background; use png")
        fig.savefig(out_dir / f"{name}.{fmt}", **kwargs)

    tables = source_data if isinstance(source_data, dict) else {"": source_data}
    rows = []
    for panel, frame in tables.items():
        tsv = out_dir / (f"{name}__{panel}.tsv" if panel else f"{name}.tsv")
        frame.to_csv(tsv, sep="\t", index=False, lineterminator="\n")
        rows.append(
            {
                "figure": name,
                "generator": script_path.relative_to(post_dir).as_posix()
                if script_path.is_relative_to(post_dir)
                else script_path.name,
                "source_data": tsv.name,
                "source_data_sha256": _sha256(tsv),
                "git_commit": commit,
                "git_dirty": str(dirty).lower(),
            }
        )
    _write_manifest_rows(out_dir / "MANIFEST.tsv", rows)
    print(f"  Saved {name} ({', '.join(formats)} + source data) -> {out_dir}")
    return out_dir
