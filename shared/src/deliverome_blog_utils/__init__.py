"""Shared helpers for Deliverome blog posts.

- :mod:`.brand_style` -- canonical figure style, inlined into every standalone figure script
- :mod:`.figures`     -- ``blog-figure`` CLI: scaffold, sync, check, and extract figure scripts
- :mod:`.data`        -- ``blog-data`` CLI: fetch/verify large data; push it to a Zenodo draft
"""

from deliverome_blog_utils.brand_style import (
    CATEGORICAL_PALETTE,
    COLORS,
    SEQUENTIAL_PALETTES,
    apply_brand_style,
    create_figure,
    diverging_palette,
    load_source_data,
    save_figure,
    sequential_palette,
)

__all__ = [
    "CATEGORICAL_PALETTE",
    "COLORS",
    "SEQUENTIAL_PALETTES",
    "apply_brand_style",
    "create_figure",
    "diverging_palette",
    "load_source_data",
    "save_figure",
    "sequential_palette",
]
