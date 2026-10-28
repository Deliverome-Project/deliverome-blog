# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Promote a post from the private drafts repo to the public repo as one clean commit.

Run from a checkout of ``Deliverome-Project/deliverome-blog-drafts`` (private), where
posts are written. The drafts repo tracks the public repo as its ``upstream`` remote,
just as a fork would. Promoting copies **only the committed state of ``posts/<slug>/``**
(plus ``people.toml`` if the post's authors were added there) onto a fresh branch of
the public repo, as a single commit. It then opens a PR there, where public CI runs.
Draft history (abandoned data, old figures, WIP commits) never reaches the public repo.

    uv run scripts/promote_post.py <slug>            # dry run: checks + shows the diff
    uv run scripts/promote_post.py <slug> --execute  # push the branch, open the PR

Running it again for the same post updates the public copy: files deleted in drafts
are deleted publicly too. Merge the public PR when the Substack post goes live.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = "Deliverome-Project/deliverome-blog"
PUBLIC_URL = f"https://github.com/{PUBLIC}.git"


def sh(*args: str, cwd: Path = ROOT, check: bool = True) -> str:
    print(f"$ {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"Failed ({result.returncode}):\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def ensure_upstream() -> None:
    """Add the public repo as `upstream` if this checkout doesn't have it yet."""
    remotes = sh("git", "remote").split()
    if "upstream" not in remotes:
        sh("git", "remote", "add", "upstream", PUBLIC_URL)
    sh("git", "fetch", "--quiet", "upstream", "main")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug")
    parser.add_argument("--execute", action="store_true", help="push the branch and open the public PR")
    args = parser.parse_args()
    slug = args.slug
    post = Path("posts") / slug

    origin = sh("git", "remote", "get-url", "origin")
    if PUBLIC in origin and "drafts" not in origin:
        sys.exit("Run this from the private deliverome-blog-drafts checkout, not the public repo.")
    if not (ROOT / post / "post.toml").exists():
        sys.exit(f"No post at {post}")
    if sh("git", "status", "--porcelain", "--", str(post), "people.toml"):
        sys.exit(f"Commit your changes to {post} first; only committed files are promoted.")
    meta = tomllib.loads((ROOT / post / "post.toml").read_text())

    # The post must pass the same checks public CI will run.
    sh("uv", "run", "--project", "shared", "blog-figure", "check", str(ROOT / post))
    ensure_upstream()

    branch = f"post/{slug}"
    with tempfile.TemporaryDirectory(prefix="promote-") as tmp:
        work = Path(tmp) / "public"
        sh("git", "worktree", "add", "--quiet", "--detach", str(work), "upstream/main")
        try:
            sh("git", "switch", "--quiet", "-c", branch, cwd=work)
            # Replace the public copy with the committed drafts copy (handles deletions).
            shutil.rmtree(work / post, ignore_errors=True)
            archive = subprocess.run(["git", "archive", "HEAD", str(post)], cwd=ROOT, capture_output=True, check=True)
            subprocess.run(["tar", "-x", "-C", str(work)], input=archive.stdout, check=True)

            authors_missing = [
                a for a in meta["authors"] if a not in tomllib.loads((work / "people.toml").read_text())
            ]
            if authors_missing:
                shutil.copy(ROOT / "people.toml", work / "people.toml")
                print(f"  people.toml: adding {', '.join(authors_missing)}")

            sh("uv", "run", "scripts/build_index.py", cwd=work)
            sh("git", "add", "-A", cwd=work)
            if not sh("git", "status", "--porcelain", cwd=work):
                print(f"\nThe public repo already matches drafts for {slug}; nothing to promote.")
                return
            exists = sh("git", "ls-tree", "--name-only", "upstream/main", str(post))
            verb = "update" if exists else "add"
            sh("git", "commit", "--quiet", "-m", f"feat({slug}): {verb} post", cwd=work)
            sh("uv", "run", "scripts/build_index.py", "--check", cwd=work)
            print("\nChanges that would go public:\n" + sh("git", "show", "--stat", "--format=", "HEAD", cwd=work))
            if meta["status"] == "draft":
                print('\nNote: status is "draft". Merge the public PR only when the post goes live.')

            if not args.execute:
                print("\nDry run. Re-run with --execute to push the branch and open the public PR.")
                return
            sh("git", "push", "--force", "upstream", f"HEAD:refs/heads/{branch}", cwd=work)
            existing = sh("gh", "pr", "list", "--repo", PUBLIC, "--head", branch, "--json", "url", "-q", ".[0].url")
            if existing:
                print(f"\nUpdated the open public PR: {existing}")
                return
            body = (
                f"Promotes `posts/{slug}/` ({meta['title']}; {', '.join(meta['authors'])}) from the private "
                "drafts repo as one commit.\n\nMerge when the Substack post goes live, then follow "
                "\"Releasing a post\" in CLAUDE.md."
            )
            url = sh(
                "gh", "pr", "create", "--repo", PUBLIC, "--head", branch, "--base", "main",
                "--title", f"feat({slug}): {verb} post", "--body", body, cwd=work,
            )
            print(f"\nOpened {url}")
        finally:
            sh("git", "worktree", "remove", "--force", str(work), check=False)
            sh("git", "branch", "-D", branch, check=False)


if __name__ == "__main__":
    main()
