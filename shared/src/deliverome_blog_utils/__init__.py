"""Shared helpers for Deliverome blog posts.

- :mod:`.plotting`   -- brand style, palettes, figure creation
- :mod:`.provenance` -- ``save_figure``: figure + source data + provenance stamp
- :mod:`.data`       -- fetch and verify large external datasets from a manifest
"""

from deliverome_blog_utils.plotting import (
    CATEGORICAL_PALETTE,
    COLORS,
    SEQUENTIAL_PALETTES,
    create_figure,
    get_categorical_colors,
    get_color,
    get_diverging_palette,
    get_sequential_palette,
    setup_plotting_style,
)
from deliverome_blog_utils.provenance import save_figure

__all__ = [
    "CATEGORICAL_PALETTE",
    "COLORS",
    "SEQUENTIAL_PALETTES",
    "create_figure",
    "get_categorical_colors",
    "get_color",
    "get_diverging_palette",
    "get_sequential_palette",
    "save_figure",
    "setup_plotting_style",
]
