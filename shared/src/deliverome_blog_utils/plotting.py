"""Deliverome plotting style for blog figures.

Adapted from ``accessible-surfaceome``'s ``_plotting_config.py`` so blog figures
match the papers and the website: same palette tokens, same bundled Manrope
font, transparent backgrounds, no in-figure titles (Substack captions do that
job).

Importing this module has no side effects. Call :func:`setup_plotting_style`
once at the top of every figure script, before creating any axes.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_fonts_registered = False

# Core Deliverome palette tokens (Deliverome Design System).
COLORS = {
    # Brand anchors
    "primary": "#BC3C4C",  # maroon-light
    "secondary": "#3D6B60",  # teal-mid
    "accent": "#F4AA28",  # amber-bright
    "quaternary": "#8878C8",  # lavender-bright
    # Semantic / utility
    "success": "#2E7A55",
    "warning": "#8C4210",  # amber-dark
    "danger": "#6E1428",  # maroon-dark
    "info": "#5848A8",  # lavender-mid
    "neutral": "#6F5D5A",  # muted
    "light": "#F3ECE5",  # bg-warm
    "dark": "#1F1718",  # ink
    "line": "#E6DAD4",
}

# Categorical palette, in the order series should take colours.
CATEGORICAL_PALETTE = [
    "#BC3C4C",  # maroon-light
    "#3D6B60",  # teal-mid
    "#F4AA28",  # amber-bright
    "#8878C8",  # lavender-bright
    "#6E1428",  # maroon-dark
    "#7AAB9F",  # teal-light
]

# Sequential palettes by hue family (deep -> light).
SEQUENTIAL_PALETTES = {
    "maroon": ["#3E0A18", "#6E1428", "#922038", "#BC3C4C", "#F0A098", "#FDE8E6"],
    "teal": ["#152E28", "#244840", "#3D6B60", "#4D8A80", "#7AAB9F", "#CCE8E4"],
    "amber": ["#5A2608", "#8C4210", "#C07830", "#F4AA28", "#F4C070", "#FAECD4"],
    "lavender": ["#1E1450", "#3A2888", "#5848A8", "#8878C8", "#A090D4", "#E4E0F8"],
}

_DIVERGING_ANCHORS = ["#8878C8", "#FFFFFF", "#BC3C4C"]  # lavender <-> white <-> maroon

# Substack's article column is 728 px wide; export PNGs at 2x for retina.
WEB_WIDTH_PX = 1456


def register_bundled_fonts() -> None:
    """Add the bundled Manrope weights to matplotlib's font manager (idempotent).

    matplotlib cannot pick a weight inside a variable font, so each weight
    ships as its own static file.
    """
    global _fonts_registered
    if _fonts_registered:
        return
    for ttf in sorted(_FONTS_DIR.glob("*.ttf")):
        fm.fontManager.addfont(str(ttf))
    _fonts_registered = True


def setup_plotting_style(context: str = "notebook", font_scale: float = 1.0) -> None:
    """Apply the Deliverome style to all subsequent figures.

    Parameters
    ----------
    context : str
        Seaborn context (``paper``, ``notebook``, ``talk``, ``poster``).
    font_scale : float
        Extra scale on top of the context's font sizes.
    """
    register_bundled_fonts()
    sns.set_theme(style="whitegrid", context=context, font_scale=font_scale)
    sns.set_palette(CATEGORICAL_PALETTE)

    plt.rcParams.update(
        {
            # Figure
            "figure.figsize": (7, 4.5),
            "figure.dpi": 100,
            "figure.facecolor": "none",
            "savefig.facecolor": "none",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.1,
            # Deterministic output: the same inputs give byte-identical SVG/PDF.
            "svg.hashsalt": "deliverome-blog",
            # Font. An explicit family list (not the 'sans-serif' alias) turns
            # on per-glyph fallback, so a glyph Manrope lacks (e.g. Greek mu)
            # comes from DejaVu Sans instead of rendering as a box.
            "font.family": ["Manrope", "DejaVu Sans"],
            "font.weight": "semibold",
            "font.size": 13,
            # Axes. Titles are suppressed: posts caption figures instead.
            "axes.titlesize": 0,
            "axes.titlepad": 0,
            "axes.labelsize": 14,
            "axes.labelweight": "semibold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.edgecolor": COLORS["line"],
            "axes.labelcolor": COLORS["dark"],
            "axes.facecolor": "none",
            "text.color": COLORS["dark"],
            # Grid
            "grid.alpha": 0.35,
            "grid.linewidth": 0.7,
            "grid.color": COLORS["line"],
            # Ticks
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "xtick.color": COLORS["dark"],
            "ytick.color": COLORS["dark"],
            # Legend
            "legend.frameon": False,
            "legend.fontsize": 12,
            "legend.title_fontsize": 12,
            # Lines and patches
            "lines.linewidth": 2,
            "lines.markersize": 7,
            "patch.edgecolor": "none",
        }
    )


def create_figure(nrows: int = 1, ncols: int = 1, figsize=None, **kwargs):
    """Create a figure sized for the Substack column and despine every axes.

    Returns ``(fig, axes)`` exactly like :func:`matplotlib.pyplot.subplots`.
    """
    if figsize is None:
        figsize = (7 if ncols == 1 else 3.6 * ncols, 4.5 * nrows if nrows > 1 else 4.5)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, **kwargs)
    for ax in fig.axes:
        sns.despine(ax=ax, top=True, right=True)
    return fig, axes


def get_color(name: str) -> str:
    """Return a palette colour by token name (see :data:`COLORS`)."""
    if name not in COLORS:
        raise KeyError(f"Unknown colour {name!r}; choose from {sorted(COLORS)}")
    return COLORS[name]


def get_categorical_colors(n: int | None = None) -> list:
    """Return the first ``n`` categorical colours (blends beyond six)."""
    if n is None or n <= len(CATEGORICAL_PALETTE):
        return CATEGORICAL_PALETTE[:n]
    return sns.blend_palette(CATEGORICAL_PALETTE, n_colors=n)


def get_sequential_palette(family: str = "maroon", n: int = 6) -> list:
    """Return ``n`` colours from a sequential family (maroon, teal, amber, lavender)."""
    if family not in SEQUENTIAL_PALETTES:
        raise KeyError(f"Unknown family {family!r}; choose from {sorted(SEQUENTIAL_PALETTES)}")
    palette = SEQUENTIAL_PALETTES[family]
    return palette[:n] if n <= len(palette) else sns.blend_palette(palette, n_colors=n)


def get_diverging_palette(n: int = 11) -> list:
    """Return an ``n``-colour lavender-white-maroon diverging palette."""
    return sns.blend_palette(_DIVERGING_ANCHORS, n_colors=n)
