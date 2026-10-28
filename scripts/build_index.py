# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build the post index in README.md and check every post folder's structure.

Stdlib only (Python 3.11+): ``uv run scripts/build_index.py`` rewrites the
index between the POSTS markers; ``--check`` (used in CI) fails instead of
writing if the index is stale or any post breaks the rules in CLAUDE.md.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "posts"
README = ROOT / "README.md"
START, END = "<!-- POSTS:START -->", "<!-- POSTS:END -->"
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED_FILES = ["README.md", "post.toml", "pyproject.toml", "data/README.md", "data/manifest.tsv"]
REQUIRED_KEYS = ["title", "authors", "status", "published", "substack_url", "data_doi", "published_commit", "summary"]
MANIFEST_HEADER = ["path", "url", "sha256", "size_bytes", "description"]
MAX_TRACKED_BYTES = 25 * 1024 * 1024


def load_posts() -> tuple[list[dict], list[str]]:
    """Return (posts, errors) for every posts/<slug>/ except _template."""
    posts, errors = [], []
    for post_dir in sorted(p for p in POSTS.iterdir() if p.is_dir() and not p.name.startswith("_")):
        slug = post_dir.name
        if not SLUG_RE.match(slug):
            errors.append(f"{slug}: folder name must be kebab-case")
        missing = [f for f in REQUIRED_FILES if not (post_dir / f).exists()]
        if missing:
            errors.append(f"{slug}: missing {', '.join(missing)}")
            continue
        meta = tomllib.loads((post_dir / "post.toml").read_text())
        absent = [k for k in REQUIRED_KEYS if k not in meta]
        if absent:
            errors.append(f"{slug}: post.toml missing {', '.join(absent)}")
            continue
        if meta["status"] not in {"draft", "published"}:
            errors.append(f"{slug}: status must be draft or published")
        if meta["status"] == "published":
            for key in ("published", "substack_url", "published_commit"):
                if not meta[key]:
                    errors.append(f"{slug}: published posts need {key}")
            for f in ("README.md", "post.toml"):
                if "TODO" in (post_dir / f).read_text():
                    errors.append(f"{slug}: {f} still contains TODO")
        with (post_dir / "data" / "manifest.tsv").open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != MANIFEST_HEADER:
                errors.append(f"{slug}: data/manifest.tsv header must be {MANIFEST_HEADER}")
            else:
                for i, row in enumerate(reader, start=2):
                    if not all(row[c] for c in ("path", "url", "sha256", "size_bytes")):
                        errors.append(f"{slug}: data/manifest.tsv:{i} incomplete row")
        posts.append({"slug": slug, **meta})
    return posts, errors


def oversized_tracked_files() -> list[str]:
    """Tracked files over the in-repo size limit (they belong in manifest.tsv)."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    paths = [ROOT / p for p in out.decode().split("\0") if p]
    return [
        f"{p.relative_to(ROOT)}: {p.stat().st_size / 1e6:.0f} MB > 25 MB; host it externally"
        for p in paths
        if p.is_file() and p.stat().st_size > MAX_TRACKED_BYTES
    ]


def render_index(posts: list[dict]) -> str:
    """Markdown for the index: published posts newest first, then drafts."""
    published = sorted((p for p in posts if p["status"] == "published"), key=lambda p: p["published"], reverse=True)
    drafts = sorted((p for p in posts if p["status"] == "draft"), key=lambda p: p["title"].lower())
    lines = ["| Date | Post | Authors | Code & data | Large data |", "|---|---|---|---|---|"]
    for p in published:
        doi = f"[{p['data_doi']}](https://doi.org/{p['data_doi']})" if p["data_doi"] else "—"
        lines.append(
            f"| {p['published']} | [{p['title']}]({p['substack_url']}) | {', '.join(p['authors'])} "
            f"| [`posts/{p['slug']}`](posts/{p['slug']}) | {doi} |"
        )
    if not published:
        lines.append("| | _No posts published yet_ | | | |")
    if drafts:
        lines += ["", "**In progress**", ""]
        lines += [f"- [{p['title']}](posts/{p['slug']}) — {', '.join(p['authors'])}" for p in drafts]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting README.md")
    args = parser.parse_args()

    posts, errors = load_posts()
    errors += oversized_tracked_files()
    text = README.read_text()
    if START not in text or END not in text:
        errors.append(f"README.md must contain {START} and {END}")
    else:
        head, rest = text.split(START, 1)
        _, tail = rest.split(END, 1)
        updated = f"{head}{START}\n{render_index(posts)}\n{END}{tail}"
        if updated != text:
            if args.check:
                errors.append("README.md post index is stale; run uv run scripts/build_index.py")
            else:
                README.write_text(updated)
                print("Updated README.md index")
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)
    print(f"{len(posts)} post(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
