"""Regenerate every figure in this post.

Methods summary (keep current): data sources, mapping strategy, filters,
thresholds, and limitations.

Usage, from the post folder:
    uv run python code/make_figures.py
"""

from pathlib import Path

import pandas as pd

from deliverome_blog_utils import create_figure, save_figure, setup_plotting_style

POST_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = POST_DIR / "data"


def load_data() -> pd.DataFrame:
    """Load and validate the inputs; print row counts at each step."""
    raise NotImplementedError("Read inputs from DATA_DIR (or DATA_DIR / 'external').")


def plot_example(df: pd.DataFrame) -> None:
    """One function per figure; pass exactly the plotted values as source_data."""
    fig, ax = create_figure()
    ax.plot(df["x"], df["y"])
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    save_figure(fig, "example", source_data=df[["x", "y"]])


def main() -> None:
    setup_plotting_style()
    df = load_data()
    plot_example(df)


if __name__ == "__main__":
    main()
