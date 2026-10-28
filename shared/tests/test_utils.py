"""Smoke tests: style applies, save_figure writes the full bundle, manifests validate."""

import csv

import pandas as pd
import pytest
from matplotlib import font_manager

from deliverome_blog_utils import create_figure, save_figure, setup_plotting_style
from deliverome_blog_utils.data import main as data_main
from deliverome_blog_utils.data import read_manifest


def test_manrope_resolves():
    setup_plotting_style()
    assert "Manrope" in font_manager.findfont("Manrope")


def test_save_figure_writes_bundle(tmp_path):
    post = tmp_path / "posts" / "demo"
    (post / "code").mkdir(parents=True)
    (post / "post.toml").write_text('title = "Demo"\n')
    script = post / "code" / "make_figures.py"
    script.write_text("")

    setup_plotting_style()
    df = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 8]})
    fig, ax = create_figure()
    ax.plot(df.x, df.y)
    save_figure(fig, "demo", source_data=df, script=script)

    figures = post / "figures"
    for name in ("demo.png", "demo.pdf", "demo.tsv", "MANIFEST.tsv"):
        assert (figures / name).exists(), name
    with (figures / "MANIFEST.tsv").open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert rows[0]["generator"] == "code/make_figures.py"
    assert len(rows[0]["source_data_sha256"]) == 64


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
