"""One chart style for every static figure (matplotlib), based on a validated palette.

Rules applied: single series uses one colour; emphasis = one highlighted entity with the
rest in grey; solid hairline grid; no dual axes; direct labels only where they help.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
MUTED = "#b9b7b0"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE, ORANGE = SERIES[0], SERIES[1]


def apply() -> None:
    mpl.rcParams.update({
        "font.family": ["Inter", "DejaVu Sans"],
        "font.size": 10,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 12, "axes.titlepad": 22, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": INK_2, "ytick.color": INK_2, "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "legend.fontsize": 9,
        "figure.dpi": 110, "text.parse_math": False, "savefig.dpi": 200, "savefig.bbox": "tight",
    })


def subtitle(ax, text: str) -> None:
    ax.text(0, 1.02, text, transform=ax.transAxes, fontsize=9, color=INK_2, va="bottom")


def source(fig, text: str) -> None:
    fig.text(0.01, -0.035, "Source: " + text, fontsize=7.5, color=INK_2, ha="left", va="top")


def save(fig, path) -> None:
    fig.savefig(path)
    plt.close(fig)
