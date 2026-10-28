# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Create posts/<slug>/ from posts/_template/.

Usage: uv run scripts/new_post.py <kebab-case-slug> --title "Title" --author "Full Name" [--author ...]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug")
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", action="append", required=True, dest="authors")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.slug):
        parser.error("slug must be kebab-case, e.g. lenti-titer-optimization")
    dest = ROOT / "posts" / args.slug
    if dest.exists():
        parser.error(f"{dest.relative_to(ROOT)} already exists")
    shutil.copytree(ROOT / "posts" / "_template", dest)

    toml = dest / "post.toml"
    text = toml.read_text()
    text = text.replace('title = "TODO: post title"', f"title = {json.dumps(args.title)}")
    text = text.replace('authors = ["TODO: Full Name"]', f"authors = {json.dumps(args.authors)}")
    toml.write_text(text)
    pyproject = dest / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace('name = "post-template"', f'name = "post-{args.slug}"'))
    readme = dest / "README.md"
    readme.write_text(readme.read_text().replace("# TODO: Post title", f"# {args.title}", 1).replace("<slug>", args.slug))
    print(f"Created {dest.relative_to(ROOT)}; next: uv run scripts/build_index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
