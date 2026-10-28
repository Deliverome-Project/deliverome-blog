"""``blog-figure``: scaffold, sync, check, and extract standalone figure scripts.

Each figure lives in ``posts/<slug>/figures/`` as one reproduction unit:

    make_<name>.py     standalone script (PEP 723 header, inlined brand style)
    <name>.tsv         the exact values plotted (read sibling-first)
    <name>.png/.pdf    outputs; the PNG embeds the script's URL and full source
    <name>.caption.md  caption pasted under the figure on Substack

Commands::

    blog-figure new posts/<slug> <name>   # write make_<name>.py + caption stub
    blog-figure sync [posts/<slug> ...]   # refresh style block + RELEASE_TAG in drafts
    blog-figure check [posts/<slug> ...]  # CI: every rule above, plus PNG metadata current
    blog-figure extract <name>.png        # print the script embedded in a PNG
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from PIL import Image

from deliverome_blog_utils import brand_style

REPO = "Deliverome-Project/deliverome-blog"
START = "# ---- Deliverome brand style"
END = "# ---- end Deliverome brand style ----"
NAME_RE = re.compile(r"^[a-z0-9]+([_-][a-z0-9]+)*$")
PINNED = ("matplotlib", "pandas", "seaborn")


def canonical_block() -> str:
    """The style block exactly as it appears in brand_style.py, sentinels included."""
    return extract_block(Path(brand_style.__file__).read_text())


def extract_block(text: str) -> str:
    start, end = text.find(START), text.find(END)
    if start < 0 or end < 0:
        return ""
    return text[start : end + len(END)]


def release_tag(post_dir: Path) -> str:
    meta = tomllib.loads((post_dir / "post.toml").read_text())
    return f"{post_dir.name}-v{meta['version']}"


def script_url(post: str, tag: str, name: str) -> str:
    return f"https://github.com/{REPO}/blob/{tag}/posts/{post}/figures/make_{name}.py"


SCRIPT_TEMPLATE = '''# /// script
# requires-python = ">=3.14"
# dependencies = [
{deps}
# ]
# ///
"""TODO: one paragraph -- what the figure shows, the n behind it, and the method.

Standalone: ``uv run make_{name}.py``, inside or outside the repo. Reads
``{name}.tsv`` next to this script, else downloads it from the post's release
on GitHub. Writes ``{name}.png`` / ``{name}.pdf`` next to itself; the PNG
embeds this script's URL and full source in its metadata.
"""

REPO = "{repo}"
POST = "{post}"
FIGURE = "{name}"
RELEASE_TAG = "{tag}"  # <slug>-v<version>; kept current by `blog-figure sync`
SCRIPT_URL = f"https://github.com/{{REPO}}/blob/{{RELEASE_TAG}}/posts/{{POST}}/figures/make_{{FIGURE}}.py"
DATA_URL = f"https://raw.githubusercontent.com/{{REPO}}/{{RELEASE_TAG}}/posts/{{POST}}/figures/{{FIGURE}}.tsv"

{block}


def plot(df: pd.DataFrame):
    """Draw the figure from the tidy source table."""
    fig, ax = create_figure()
    sns.scatterplot(data=df, x="TODO_x", y="TODO_y", ax=ax)
    ax.set_xlabel("TODO (units, method)")
    ax.set_ylabel("TODO (units, method)")
    return fig


def main() -> None:
    script = Path(__file__).resolve()
    apply_brand_style(script)
    df = load_source_data(script, f"{{FIGURE}}.tsv", DATA_URL)
    print(f"{{FIGURE}}: n = {{len(df)}} rows")
    save_figure(plot(df), script, FIGURE, SCRIPT_URL)


if __name__ == "__main__":
    main()
'''


def cmd_new(post_dir: Path, name: str) -> int:
    if not NAME_RE.match(name):
        print("figure name must be lowercase snake/kebab case, e.g. titer_vs_moi", file=sys.stderr)
        return 2
    figures = post_dir / "figures"
    script = figures / f"make_{name}.py"
    if script.exists():
        print(f"{script} already exists", file=sys.stderr)
        return 2
    deps = "\n".join(f'#   "{pkg}=={metadata.version(pkg)}",' for pkg in PINNED)
    figures.mkdir(exist_ok=True)
    script.write_text(
        SCRIPT_TEMPLATE.format(
            deps=deps, name=name, repo=REPO, post=post_dir.name, tag=release_tag(post_dir), block=canonical_block()
        )
    )
    (figures / f"{name}.caption.md").write_text("**Figure N.** TODO: caption as it appears on Substack.\n")
    print(f"Wrote {script.relative_to(post_dir)} and {name}.caption.md.")
    print(f"Next: write figures/{name}.tsv (from a script in code/), fill in plot(), then `uv run {script.name}`.")
    return 0


def _is_draft(post_dir: Path) -> bool:
    return tomllib.loads((post_dir / "post.toml").read_text()).get("status") != "published"


def cmd_sync(post_dirs: list[Path]) -> int:
    block = canonical_block()
    for post_dir in post_dirs:
        tag = release_tag(post_dir)
        for script in sorted((post_dir / "figures").glob("make_*.py")):
            text = script.read_text()
            new = re.sub(r'(?m)^RELEASE_TAG = "[^"]*"', f'RELEASE_TAG = "{tag}"', text, count=1)
            if _is_draft(post_dir) and extract_block(new):
                new = new.replace(extract_block(new), block)
            if new != text:
                script.write_text(new)
                print(f"Updated {script}; re-run it to refresh its outputs")
    return 0


def check_post(post_dir: Path) -> list[str]:
    """Return every rule violation for the figures in one post."""
    errors: list[str] = []
    slug, tag, draft, block = post_dir.name, release_tag(post_dir), _is_draft(post_dir), canonical_block()
    for script in sorted((post_dir / "figures").glob("make_*.py")):
        name = script.stem.removeprefix("make_")
        where = f"{slug}/figures/{script.name}"
        text = script.read_text()
        if not text.startswith("# /// script"):
            errors.append(f"{where}: must start with a PEP 723 '# /// script' header")
        if re.search(r"(?m)^\s*(from|import)\s+deliverome_blog_utils", text):
            errors.append(f"{where}: must be standalone; inline the style block instead of importing it")
        for const, want in (("POST", slug), ("FIGURE", name), ("RELEASE_TAG", tag)):
            if f'{const} = "{want}"' not in text:
                errors.append(f'{where}: expected {const} = "{want}" (run blog-figure sync)')
        if draft and extract_block(text) != block:
            errors.append(f"{where}: style block differs from shared brand_style.py (run blog-figure sync)")
        for suffix in (".tsv", ".png", ".pdf", ".caption.md"):
            if not (script.parent / f"{name}{suffix}").exists():
                errors.append(f"{where}: missing sibling {name}{suffix}")
        png = script.parent / f"{name}.png"
        if png.exists():
            stamped = Image.open(png).text
            if stamped.get("Script") != text or stamped.get("Source") != script_url(slug, tag, name):
                errors.append(f"{where}: {png.name} was not made by the current script; re-run it")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="blog-figure", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    new_p = sub.add_parser("new", help="scaffold a standalone figure script")
    new_p.add_argument("post_dir", type=Path)
    new_p.add_argument("name")
    for cmd in ("sync", "check"):
        p = sub.add_parser(cmd)
        p.add_argument("post_dirs", nargs="*", type=Path, help="default: every post")
    ext_p = sub.add_parser("extract", help="print the script embedded in a figure PNG")
    ext_p.add_argument("png", type=Path)
    args = parser.parse_args(argv)

    if args.command == "new":
        return cmd_new(args.post_dir.resolve(), args.name)
    if args.command == "extract":
        script = Image.open(args.png).text.get("Script")
        if script is None:
            print(f"{args.png} has no embedded Script", file=sys.stderr)
            return 1
        sys.stdout.write(script)
        return 0
    posts = [p.resolve() for p in args.post_dirs] or sorted(
        p for p in (Path(__file__).resolve().parents[3] / "posts").iterdir() if p.is_dir() and not p.name.startswith("_")
    )
    if args.command == "sync":
        return cmd_sync(posts)
    errors = [e for p in posts for e in check_post(p)]
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)
    print(f"Checked figures in {len(posts)} post(s): {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
