"""Canonical Deliverome figure style, copied verbatim into every figure script.

Figures follow accessible-surfaceome's final-figure convention: each figure is
made by one **standalone** ``make_<figure>.py`` that a reader can run with
``uv run make_<figure>.py`` and nothing else. So the style cannot be imported.
``blog-figure new`` pastes everything between the two sentinel lines below
into the script, and ``blog-figure check`` (CI) fails if an unreleased post's
copy has drifted from this file. To change the style, edit this file, bump the
sentinel version, and run ``blog-figure sync``.

Notebooks and exploratory code can import the same functions:
``from deliverome_blog_utils import apply_brand_style, COLORS, ...``.
"""

# ---- Deliverome brand style (sentinel: deliverome-blog-style-v1) ----
# Copied from shared/src/deliverome_blog_utils/brand_style.py; do not edit here.
import logging
from pathlib import Path

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

COLORS = {
    "primary": "#BC3C4C",  # maroon-light
    "secondary": "#3D6B60",  # teal-mid
    "accent": "#F4AA28",  # amber-bright
    "quaternary": "#8878C8",  # lavender-bright
    "success": "#2E7A55",
    "warning": "#8C4210",  # amber-dark
    "danger": "#6E1428",  # maroon-dark
    "info": "#5848A8",  # lavender-mid
    "neutral": "#6F5D5A",  # muted
    "light": "#F3ECE5",  # bg-warm
    "dark": "#1F1718",  # ink
    "line": "#E6DAD4",
}
CATEGORICAL_PALETTE = ["#BC3C4C", "#3D6B60", "#F4AA28", "#8878C8", "#6E1428", "#7AAB9F"]
SEQUENTIAL_PALETTES = {  # deep -> light
    "maroon": ["#3E0A18", "#6E1428", "#922038", "#BC3C4C", "#F0A098", "#FDE8E6"],
    "teal": ["#152E28", "#244840", "#3D6B60", "#4D8A80", "#7AAB9F", "#CCE8E4"],
    "amber": ["#5A2608", "#8C4210", "#C07830", "#F4AA28", "#F4C070", "#FAECD4"],
    "lavender": ["#1E1450", "#3A2888", "#5848A8", "#8878C8", "#A090D4", "#E4E0F8"],
}
# DejaVu Sans (the per-glyph fallback) has no semibold; silence its warning.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
DIVERGING_ANCHORS = ["#8878C8", "#FFFFFF", "#BC3C4C"]  # lavender <-> white <-> maroon
WEB_WIDTH_PX = 1456  # 2x Substack's 728 px article column


def register_brand_fonts(start: Path) -> bool:
    """Register Manrope from the nearest ``assets/fonts/`` above ``start``."""
    for parent in [start, *start.parents]:
        fonts_dir = parent / "assets" / "fonts"
        if fonts_dir.is_dir():
            for ttf in sorted(fonts_dir.glob("*.ttf")):
                font_manager.fontManager.addfont(str(ttf))
            return True
    return False


def apply_brand_style(script: Path) -> None:
    """Apply the Deliverome style. Call before creating any axes."""
    if not register_brand_fonts(script.parent):
        print("Manrope not found (run inside a deliverome-blog checkout for brand fonts); using DejaVu Sans")
    sns.set_theme(style="whitegrid", context="notebook")
    sns.set_palette(CATEGORICAL_PALETTE)
    plt.rcParams.update(
        {
            "figure.figsize": (7, 4.5),
            "figure.facecolor": "none",
            "savefig.facecolor": "none",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.1,
            "svg.hashsalt": "deliverome-blog",
            # Explicit family list (not the 'sans-serif' alias) enables per-glyph
            # fallback, so a glyph Manrope lacks (e.g. Greek mu) comes from DejaVu.
            "font.family": ["Manrope", "DejaVu Sans"],
            "font.weight": "semibold",
            "font.size": 13,
            "axes.titlesize": 0,  # no in-figure titles; the post captions figures
            "axes.titlepad": 0,
            "axes.labelsize": 14,
            "axes.labelweight": "semibold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.axisbelow": True,
            "axes.edgecolor": COLORS["line"],
            "axes.labelcolor": COLORS["dark"],
            "axes.facecolor": "none",
            "text.color": COLORS["dark"],
            "grid.alpha": 0.35,
            "grid.linewidth": 0.7,
            "grid.color": COLORS["line"],
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "xtick.color": COLORS["dark"],
            "ytick.color": COLORS["dark"],
            "legend.frameon": False,
            "legend.fontsize": 12,
            "lines.linewidth": 2,
            "lines.markersize": 7,
            "patch.edgecolor": "none",
        }
    )


def create_figure(nrows: int = 1, ncols: int = 1, figsize=None, **kwargs):
    """``plt.subplots`` sized for the Substack column, with every axes despined."""
    if figsize is None:
        figsize = (7 if ncols == 1 else 3.6 * ncols, 4.5 * max(nrows, 1))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, **kwargs)
    for ax in fig.axes:
        sns.despine(ax=ax, top=True, right=True)
    return fig, axes


def sequential_palette(family: str = "maroon", n: int = 6) -> list:
    """``n`` colours from a sequential family (maroon, teal, amber, lavender)."""
    palette = SEQUENTIAL_PALETTES[family]
    return palette[:n] if n <= len(palette) else sns.blend_palette(palette, n_colors=n)


def diverging_palette(n: int = 11) -> list:
    """``n``-colour lavender-white-maroon diverging palette."""
    return sns.blend_palette(DIVERGING_ANCHORS, n_colors=n)


def load_source_data(script: Path, filename: str, fallback_url: str) -> pd.DataFrame:
    """Sibling-first loader: the TSV next to the script, else the released copy."""
    sibling = script.parent / filename
    if sibling.exists():
        return pd.read_csv(sibling, sep="\t")
    print(f"{filename} not next to the script; downloading {fallback_url}")
    return pd.read_csv(fallback_url, sep="\t")


def save_figure(fig, script: Path, name: str, script_url: str) -> None:
    """Write ``<name>.png`` + ``<name>.pdf`` next to ``script``, stamped with provenance.

    The PNG carries the script URL (``Source``) and the script's full source
    (``Script``), so the image alone is enough to regenerate it. The PDF
    carries the URL (``Subject``). Dates are stripped so reruns are byte-stable.
    """
    note = f"Regenerate: save the Script text as {script.name}, then `uv run {script.name}`."
    # Size the PNG to WEB_WIDTH_PX after the tight-bbox crop, not before.
    tight_width_in = fig.get_tightbbox().width + 2 * plt.rcParams["savefig.pad_inches"]
    fig.savefig(
        script.parent / f"{name}.png",
        dpi=WEB_WIDTH_PX / tight_width_in,
        metadata={"Source": script_url, "Description": note, "Script": script.read_text()},
    )
    fig.savefig(
        script.parent / f"{name}.pdf",
        metadata={"Subject": script_url, "Keywords": note, "CreationDate": None, "ModDate": None},
    )
    print(f"Saved {name}.png and {name}.pdf -> {script.parent}")


# ---- end Deliverome brand style ----
