"""Fetch and verify a post's large external datasets.

Large files (anything over ~25 MB) are never committed. Each post lists them in
``posts/<slug>/data/manifest.tsv``:

    path            url                                         sha256  size_bytes  description
    raw/run1.fcs.gz https://zenodo.org/records/123/files/...    ab12..  3812331520  Flow run 1

``blog-data fetch posts/<slug>`` downloads every row into
``posts/<slug>/data/external/<path>`` (gitignored), verifies size and SHA256,
skips files already present and valid, and appends to
``data/external/FETCH_LOG.tsv`` (URL, local path, UTC time, size, SHA256,
downloaded/reused).

``blog-data hash FILE...`` prints manifest rows for files you are about to
upload, so the checksums are computed from the local originals.

``blog-data zenodo push posts/<slug>`` uploads ``data/external/`` to a Zenodo
draft and writes the manifest for you; see :mod:`deliverome_blog_utils.zenodo`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_COLUMNS = ["path", "url", "sha256", "size_bytes", "description"]
LOG_COLUMNS = ["url", "local_path", "captured_utc", "size_bytes", "sha256", "status"]


def sha256_file(path: Path) -> str:
    """Return the hex SHA256 of ``path``, streaming in 1 MiB chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(post_dir: Path) -> list[dict]:
    """Read and validate ``data/manifest.tsv``; fail fast on malformed rows."""
    manifest = post_dir / "data" / "manifest.tsv"
    if not manifest.exists():
        return []
    with manifest.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MANIFEST_COLUMNS:
            raise ValueError(f"{manifest}: header must be {MANIFEST_COLUMNS}, got {reader.fieldnames}")
        rows = list(reader)
    for i, row in enumerate(rows, start=2):
        if not all(row[c] for c in ("path", "url", "sha256", "size_bytes")):
            raise ValueError(f"{manifest}:{i}: path, url, sha256 and size_bytes are required")
        if Path(row["path"]).is_absolute() or ".." in Path(row["path"]).parts:
            raise ValueError(f"{manifest}:{i}: path must be relative and stay inside data/external/")
    return rows


def read_manifest_descriptions(post_dir: Path) -> dict[str, str]:
    """Map manifest path -> description, so regenerating the manifest keeps them."""
    manifest = post_dir / "data" / "manifest.tsv"
    if not manifest.exists():
        return {}
    with manifest.open(newline="") as handle:
        return {row["path"]: row.get("description", "") for row in csv.DictReader(handle, delimiter="\t")}


def write_manifest(post_dir: Path, rows: list[dict]) -> None:
    """Write ``data/manifest.tsv`` sorted by path."""
    with (post_dir / "data" / "manifest.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["path"]))


def _valid(path: Path, row: dict) -> bool:
    return path.exists() and path.stat().st_size == int(row["size_bytes"]) and sha256_file(path) == row["sha256"]


def fetch(post_dir: Path) -> int:
    """Download and verify every manifest row. Returns the number of failures."""
    rows = read_manifest(post_dir)
    external = post_dir / "data" / "external"
    log_path = external / "FETCH_LOG.tsv"
    failures = 0
    for row in rows:
        dest = external / row["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if _valid(dest, row):
            status = "reused"
        else:
            print(f"  Downloading {row['url']} ({int(row['size_bytes']) / 1e9:.2f} GB)")
            partial = dest.with_name(dest.name + ".partial")
            with urllib.request.urlopen(row["url"]) as response, partial.open("wb") as out:
                shutil.copyfileobj(response, out, length=1 << 20)
            partial.replace(dest)
            if not _valid(dest, row):
                print(f"  FAILED checksum/size: {dest}", file=sys.stderr)
                failures += 1
                continue
            status = "downloaded"
        print(f"  {status}: {dest.relative_to(post_dir)}")
        new_log = not log_path.exists()
        with log_path.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=LOG_COLUMNS, delimiter="\t", lineterminator="\n")
            if new_log:
                writer.writeheader()
            writer.writerow(
                {
                    "url": row["url"],
                    "local_path": str(dest.relative_to(post_dir)),
                    "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "size_bytes": row["size_bytes"],
                    "sha256": row["sha256"],
                    "status": status,
                }
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``blog-data fetch POST_DIR`` or ``blog-data hash FILE...``."""
    parser = argparse.ArgumentParser(prog="blog-data", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    fetch_p = sub.add_parser("fetch", help="download + verify a post's data/manifest.tsv")
    fetch_p.add_argument("post_dir", type=Path)
    hash_p = sub.add_parser("hash", help="print manifest rows (path, sha256, size) for local files")
    hash_p.add_argument("files", nargs="+", type=Path)
    zen_p = sub.add_parser("zenodo", help="create/update the post's Zenodo data draft (never publishes)")
    zen_p.add_argument("action", choices=["push"])
    zen_p.add_argument("post_dir", type=Path)
    zen_p.add_argument("--sandbox", action="store_true", help="use sandbox.zenodo.org (ZENODO_SANDBOX_TOKEN)")
    zen_p.add_argument("--dry-run", action="store_true", help="show metadata and files; no network calls")
    args = parser.parse_args(argv)

    if args.command == "zenodo":
        from deliverome_blog_utils import zenodo

        return zenodo.run(args)

    if args.command == "fetch":
        failures = fetch(args.post_dir.resolve())
        return 1 if failures else 0
    print("\t".join(MANIFEST_COLUMNS))
    for path in args.files:
        print("\t".join([path.name, "<url>", sha256_file(path), str(path.stat().st_size), "<description>"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
