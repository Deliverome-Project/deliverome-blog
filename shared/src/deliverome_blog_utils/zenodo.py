"""Create or update a post's Zenodo data record as a draft. Never publishes.

``blog-data zenodo push posts/<slug>`` does, in order:

1. Collects every file under ``data/external/`` (except ``FETCH_LOG.tsv``),
   hashing each one (SHA256 for the manifest, MD5 to compare with Zenodo).
2. Creates a draft deposition with a pre-reserved DOI the first time. Later
   runs reuse the draft recorded in ``data/zenodo.json``. If that record is
   already published, they open a new-version draft.
3. Sets metadata from ``post.toml`` and the repo's ``people.toml``: a CC0 dataset,
   creators with affiliation and ORCID, and links to the post and its code folder.
4. Uploads files missing from the draft or changed since the last push, and
   removes draft files that no longer exist locally.
5. Writes ``data/manifest.tsv`` (record URLs + SHA256 + size, keeping your
   descriptions), ``data/zenodo.json``, and ``data_doi`` in ``post.toml``.

Publishing is irreversible: files become immutable and the DOI is registered.
So it is left to a person, who reviews the draft on zenodo.org and clicks
Publish when the Substack post goes live. Manifest URLs resolve only after that.

Auth: a personal access token with scopes ``deposit:write`` and
``deposit:actions``, in ``ZENODO_TOKEN`` (or ``ZENODO_SANDBOX_TOKEN`` with
``--sandbox``, which targets sandbox.zenodo.org for rehearsals).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from deliverome_blog_utils.data import read_manifest_descriptions, write_manifest

REPO_URL = "https://github.com/Deliverome-Project/deliverome-blog"
HOSTS = {False: "https://zenodo.org", True: "https://sandbox.zenodo.org"}
MAX_FILES = 100  # Zenodo per-record limit; tar directories with many files
SKIP = {"FETCH_LOG.tsv"}
STATE_FILE = Path("data") / "zenodo.json"


class ZenodoError(RuntimeError):
    """A Zenodo API call failed or the post is not ready to push."""


# --------------------------------------------------------------------------- local


def hash_file(path: Path) -> tuple[str, str]:
    """Return ``(sha256, md5)`` hex digests of ``path`` in one streaming pass."""
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
            md5.update(chunk)
    return sha.hexdigest(), md5.hexdigest()


def local_files(post_dir: Path) -> dict[str, dict]:
    """Map Zenodo key -> file info for everything under ``data/external/``.

    Zenodo records are flat, so ``sub/dir/file`` uploads as ``sub__dir__file``;
    the manifest keeps the original relative path.
    """
    external = post_dir / "data" / "external"
    files: dict[str, dict] = {}
    for path in sorted(p for p in external.rglob("*") if p.is_file()):
        rel = path.relative_to(external).as_posix()
        if path.name in SKIP or path.name.endswith(".partial") or path.name.startswith("."):
            continue
        key = rel.replace("/", "__")
        if key in files:
            raise ZenodoError(f"{rel} and {files[key]['path']} both flatten to {key}; rename one")
        sha256, md5 = hash_file(path)
        files[key] = {"path": rel, "local": path, "sha256": sha256, "md5": md5, "size": path.stat().st_size}
    if not files:
        raise ZenodoError(f"No files under {external}; put the post's large data there first")
    if len(files) > MAX_FILES:
        raise ZenodoError(f"{len(files)} files > Zenodo's {MAX_FILES}-file limit; tar related files together")
    return files


def creators(authors: list[str], people_file: Path) -> list[dict]:
    """Zenodo creators for ``authors`` from ``people.toml``; fail fast on unknowns."""
    people = tomllib.loads(people_file.read_text()) if people_file.exists() else {}
    missing = [a for a in authors if a not in people]
    if missing:
        raise ZenodoError(f"Add {', '.join(missing)} to {people_file.name} (zenodo_name, affiliation, orcid)")
    out = []
    for author in authors:
        person = people[author]
        entry = {"name": person["zenodo_name"]}
        for field in ("affiliation", "orcid"):
            if person.get(field):
                entry[field] = person[field]
        out.append(entry)
    return out


def build_metadata(post_dir: Path, repo_root: Path) -> dict:
    """Deposition metadata for a post: a CC0 dataset linked to the post and its code."""
    meta = tomllib.loads((post_dir / "post.toml").read_text())
    folder_url = f"{REPO_URL}/tree/main/posts/{post_dir.name}"
    related = [{"identifier": folder_url, "relation": "isSupplementTo", "scheme": "url"}]
    if meta.get("substack_url"):
        related.append({"identifier": meta["substack_url"], "relation": "isSupplementTo", "scheme": "url"})
    description = (
        f"<p>{meta['summary']}</p>"
        f"<p>Data behind the Deliverome blog post <em>{meta['title']}</em>. "
        f'Code to reproduce every figure: <a href="{folder_url}">{folder_url}</a> (MIT). '
        "File checksums are listed in that folder's <code>data/manifest.tsv</code>; "
        "<code>uv run blog-data fetch .</code> downloads and verifies them.</p>"
    )
    metadata = {
        "upload_type": "dataset",
        "title": f'Data for "{meta["title"]}" (Deliverome blog)',
        "creators": creators(meta["authors"], repo_root / "people.toml"),
        "description": description,
        "access_right": "open",
        "license": "cc-zero",
        "keywords": ["Deliverome"],
        "related_identifiers": related,
    }
    community = os.environ.get("ZENODO_COMMUNITY")
    if community:
        metadata["communities"] = [{"identifier": community}]
    return metadata


def set_data_doi(post_dir: Path, doi: str) -> None:
    """Rewrite the ``data_doi = "..."`` line of post.toml in place."""
    toml = post_dir / "post.toml"
    text, n = re.subn(r'(?m)^data_doi = "[^"]*"', f'data_doi = "{doi}"', toml.read_text())
    if n != 1:
        raise ZenodoError(f"{toml}: expected exactly one data_doi line")
    toml.write_text(text)


# --------------------------------------------------------------------------- API


class Client:
    """Minimal Zenodo deposit API client (stdlib only)."""

    def __init__(self, token: str, sandbox: bool = False):
        self.base = HOSTS[sandbox]
        self.auth = {"Authorization": f"Bearer {token}"}

    def request(self, method: str, url: str, body=None, *, raw=None, size: int | None = None):
        if not url.startswith("http"):
            url = f"{self.base}/api{url}"
        headers = dict(self.auth)
        data = None
        if raw is not None:
            data, headers["Content-Type"], headers["Content-Length"] = raw, "application/octet-stream", str(size)
        elif body is not None:
            data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                payload = response.read()
        except urllib.error.HTTPError as err:
            raise ZenodoError(f"{method} {url} -> {err.code}: {err.read().decode(errors='replace')[:500]}") from err
        return json.loads(payload) if payload else None

    def create(self) -> dict:
        return self.request("POST", "/deposit/depositions", {"metadata": {"prereserve_doi": True}})

    def get(self, dep_id: int) -> dict:
        return self.request("GET", f"/deposit/depositions/{dep_id}")

    def new_version(self, dep_id: int) -> dict:
        record = self.request("POST", f"/deposit/depositions/{dep_id}/actions/newversion")
        return self.request("GET", record["links"]["latest_draft"])

    def set_metadata(self, dep_id: int, metadata: dict) -> dict:
        return self.request("PUT", f"/deposit/depositions/{dep_id}", {"metadata": metadata})

    def files(self, dep_id: int) -> list[dict]:
        return self.request("GET", f"/deposit/depositions/{dep_id}/files")

    def delete_file(self, dep_id: int, file_id: str) -> None:
        self.request("DELETE", f"/deposit/depositions/{dep_id}/files/{file_id}")

    def upload(self, bucket: str, key: str, path: Path, size: int) -> dict:
        with path.open("rb") as handle:
            return self.request("PUT", f"{bucket}/{key}", raw=handle, size=size)


# --------------------------------------------------------------------------- push


def push(post_dir: Path, client: Client | None, *, sandbox: bool = False, dry_run: bool = False) -> int:
    """Sync ``data/external/`` to the post's Zenodo draft. Returns an exit code."""
    post_dir = post_dir.resolve()
    repo_root = post_dir.parents[1]
    files = local_files(post_dir)
    metadata = build_metadata(post_dir, repo_root)
    state_path = post_dir / STATE_FILE
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if state and state.get("sandbox", False) != sandbox:
        raise ZenodoError(f"{state_path} belongs to {'sandbox' if state['sandbox'] else 'production'} Zenodo")

    total_gb = sum(f["size"] for f in files.values()) / 1e9
    print(f"{post_dir.name}: {len(files)} file(s), {total_gb:.2f} GB -> {HOSTS[sandbox]}")
    if dry_run:
        print(json.dumps(metadata, indent=2))
        for key, f in files.items():
            print(f"  {key}  {f['size']:,} B  sha256:{f['sha256'][:12]}")
        return 0
    assert client is not None

    if not state:
        dep = client.create()
        print(f"  Created draft {dep['id']}")
    else:
        dep = client.get(state["deposition_id"])
        if dep.get("submitted"):
            dep = client.new_version(dep["id"])
            print(f"  Record {state['deposition_id']} is published; opened new-version draft {dep['id']}")
    dep_id = dep["id"]
    doi = dep["metadata"].get("prereserve_doi", {}).get("doi") or dep.get("doi", "")
    client.set_metadata(dep_id, {**metadata, "prereserve_doi": True} if not doi else metadata)

    remote = {f["filename"]: f for f in client.files(dep_id)}
    for key, f in files.items():
        if key in remote and remote[key]["checksum"].removeprefix("md5:") == f["md5"]:
            print(f"  unchanged: {key}")
            continue
        if key in remote:
            client.delete_file(dep_id, remote[key]["id"])
        print(f"  uploading: {key} ({f['size'] / 1e9:.2f} GB)")
        result = client.upload(dep["links"]["bucket"], key, f["local"], f["size"])
        if result["checksum"].removeprefix("md5:") != f["md5"]:
            raise ZenodoError(f"{key}: Zenodo checksum {result['checksum']} != local md5:{f['md5']}")
    for key in sorted(set(remote) - set(files)):
        print(f"  removing from draft (no longer local): {key}")
        client.delete_file(dep_id, remote[key]["id"])

    record_url = f"{HOSTS[sandbox]}/records/{dep_id}"
    descriptions = read_manifest_descriptions(post_dir)
    write_manifest(
        post_dir,
        [
            {
                "path": f["path"],
                "url": f"{record_url}/files/{key}?download=1",
                "sha256": f["sha256"],
                "size_bytes": str(f["size"]),
                "description": descriptions.get(f["path"], ""),
            }
            for key, f in files.items()
        ],
    )
    state = {"deposition_id": dep_id, "doi": doi, "record_url": record_url, "sandbox": sandbox}
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    if not sandbox:
        set_data_doi(post_dir, doi)
    print(
        f"\nDraft ready: {HOSTS[sandbox]}/uploads/{dep_id}  (DOI {doi}, registered on publish)\n"
        f"Updated data/manifest.tsv{'' if sandbox else ', post.toml data_doi'} and {STATE_FILE}.\n"
        "Fill in any empty manifest descriptions, commit, then publish the draft on Zenodo\n"
        "when the Substack post goes live. Manifest URLs resolve only after publishing."
    )
    return 0


def run(args) -> int:
    """Entry point for ``blog-data zenodo push``."""
    client = None
    if not args.dry_run:
        var = "ZENODO_SANDBOX_TOKEN" if args.sandbox else "ZENODO_TOKEN"
        token = os.environ.get(var)
        if not token:
            print(f"{var} is not set: add it to the repo's .env (see .env.example)", file=sys.stderr)
            return 2
        client = Client(token, sandbox=args.sandbox)
    try:
        return push(args.post_dir, client, sandbox=args.sandbox, dry_run=args.dry_run)
    except ZenodoError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1


__all__ = ["Client", "ZenodoError", "push", "run"]
