"""Tests for the figure-script tooling, data manifests, and the Zenodo push flow."""

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from deliverome_blog_utils import figures, zenodo
from deliverome_blog_utils.data import main as data_main
from deliverome_blog_utils.data import read_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
POST_TOML = """title = "Demo post"
authors = ["Becca Carlson"]
status = "draft"
version = 1
published = ""
substack_url = ""
data_doi = ""
code_doi = ""
summary = "A demo."
"""


@pytest.fixture
def repo(tmp_path):
    """A minimal repo: assets/fonts, people.toml, and posts/demo/."""
    shutil.copytree(REPO_ROOT / "assets", tmp_path / "assets")
    shutil.copy(REPO_ROOT / "people.toml", tmp_path / "people.toml")
    post = tmp_path / "posts" / "demo"
    (post / "figures").mkdir(parents=True)
    (post / "data" / "external").mkdir(parents=True)
    (post / "post.toml").write_text(POST_TOML)
    return tmp_path


def make_figure(post: Path) -> Path:
    """Scaffold a figure, give it data and a real plot, run it standalone."""
    assert figures.cmd_new(post, "growth") == 0
    script = post / "figures" / "make_growth.py"
    script.write_text(script.read_text().replace('"TODO_x"', '"day"').replace('"TODO_y"', '"titer"'))
    pd.DataFrame({"day": [1, 2, 3], "titer": [1e6, 4e6, 9e6]}).to_csv(
        post / "figures" / "growth.tsv", sep="\t", index=False
    )
    # Run it the way a reader would: this interpreter, no deliverome_blog_utils on the path.
    subprocess.run([sys.executable, "-I", script.name], cwd=script.parent, check=True)
    return script


def test_figure_script_is_standalone_and_embeds_itself(repo):
    post = repo / "posts" / "demo"
    script = make_figure(post)
    text = script.read_text()
    assert "import deliverome_blog_utils" not in text and "from deliverome_blog_utils" not in text
    assert 'RELEASE_TAG = "demo-v1"' in text

    stamped = Image.open(post / "figures" / "growth.png").text
    assert stamped["Script"] == text
    assert stamped["Source"].endswith("/blob/demo-v1/posts/demo/figures/make_growth.py")
    assert Image.open(post / "figures" / "growth.png").width == pytest.approx(1456, abs=3)

    assert figures.check_post(post) == []


def test_figure_outputs_are_byte_stable(repo):
    post = repo / "posts" / "demo"
    script = make_figure(post)
    first = {p.name: p.read_bytes() for p in (post / "figures").glob("growth.*")}
    subprocess.run([sys.executable, "-I", script.name], cwd=script.parent, check=True)
    second = {p.name: p.read_bytes() for p in (post / "figures").glob("growth.*")}
    assert first == second


def test_check_catches_drift_and_stale_png(repo):
    post = repo / "posts" / "demo"
    script = make_figure(post)
    script.write_text(script.read_text().replace('"#BC3C4C",  # maroon-light', '"#000000",  # maroon-light', 1))
    errors = figures.check_post(post)
    assert any("style block differs" in e for e in errors)
    assert any("not made by the current script" in e for e in errors)
    figures.cmd_sync([post])
    assert not any("style block differs" in e for e in figures.check_post(post))


def test_manifest_rejects_escaping_paths(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "manifest.tsv").write_text(
        "path\turl\tsha256\tsize_bytes\tdescription\n../secret\thttps://x\tab\t1\t\n"
    )
    with pytest.raises(ValueError):
        read_manifest(tmp_path)


def test_hash_cli(tmp_path, capsys):
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello")
    assert data_main(["hash", str(f)]) == 0
    assert "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" in capsys.readouterr().out


class FakeZenodo:
    """In-memory stand-in for the Zenodo deposit API."""

    def __init__(self):
        self.stored: dict[str, dict] = {}
        self.metadata: dict = {}
        self.published = False
        self.calls: list[str] = []

    def create(self):
        self.calls.append("create")
        return {"id": 42, "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.42"}}, "links": {"bucket": "B"}}

    def get(self, dep_id):
        return {"id": dep_id, "submitted": self.published, "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.42"}},
                "links": {"bucket": "B"}}

    def new_version(self, dep_id):
        self.calls.append("new_version")
        self.published = False
        return {"id": 43, "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.43"}}, "links": {"bucket": "B"}}

    def set_metadata(self, dep_id, metadata):
        self.metadata = metadata

    def files(self, dep_id):
        return [{"id": k, "filename": k, "checksum": f"md5:{v['md5']}"} for k, v in self.stored.items()]

    def delete_file(self, dep_id, file_id):
        self.calls.append(f"delete:{file_id}")
        del self.stored[file_id]

    def upload(self, bucket, key, path, size):
        self.calls.append(f"upload:{key}")
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        self.stored[key] = {"md5": md5}
        return {"checksum": f"md5:{md5}"}


def test_zenodo_push_creates_draft_writes_manifest_and_is_idempotent(repo):
    post = repo / "posts" / "demo"
    (post / "data" / "external" / "runs").mkdir()
    (post / "data" / "external" / "runs" / "plate1.csv").write_text("a,b\n1,2\n")
    (post / "data" / "external" / "FETCH_LOG.tsv").write_text("ignored")
    fake = FakeZenodo()

    assert zenodo.push(post, fake) == 0
    assert fake.calls == ["create", "upload:runs__plate1.csv"]
    assert fake.metadata["license"] == "cc-zero"
    assert fake.metadata["creators"][0]["orcid"] == "0000-0002-5423-9717"

    with (post / "data" / "manifest.tsv").open() as handle:
        row = next(csv.DictReader(handle, delimiter="\t"))
    assert row["path"] == "runs/plate1.csv"
    assert row["url"] == "https://zenodo.org/records/42/files/runs__plate1.csv?download=1"
    assert 'data_doi = "10.5281/zenodo.42"' in (post / "post.toml").read_text()
    assert json.loads((post / "data" / "zenodo.json").read_text())["deposition_id"] == 42

    fake.calls.clear()
    assert zenodo.push(post, fake) == 0
    assert fake.calls == []  # nothing changed, nothing uploaded

    fake.published = True
    assert zenodo.push(post, fake) == 0
    assert fake.calls[0] == "new_version"


def test_zenodo_push_requires_known_authors(repo):
    post = repo / "posts" / "demo"
    (post / "post.toml").write_text(POST_TOML.replace("Becca Carlson", "Unknown Person"))
    (post / "data" / "external" / "x.bin").write_bytes(b"x")
    with pytest.raises(zenodo.ZenodoError, match="people.toml"):
        zenodo.push(post, FakeZenodo())


def test_load_dotenv_finds_nearest_and_keeps_existing(tmp_path, monkeypatch):
    from deliverome_blog_utils.data import load_dotenv

    (tmp_path / ".env").write_text('# comment\nZENODO_TOKEN="abc"\nZENODO_COMMUNITY=\n')
    nested = tmp_path / "posts" / "demo"
    nested.mkdir(parents=True)
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    monkeypatch.setenv("ZENODO_COMMUNITY", "kept")
    assert load_dotenv(nested) == tmp_path / ".env"
    import os

    assert os.environ["ZENODO_TOKEN"] == "abc"
    assert os.environ["ZENODO_COMMUNITY"] == "kept"
