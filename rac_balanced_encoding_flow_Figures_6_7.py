"""
Figures 6 and 7 — balanced deterministic encodings for n=4 and n=6
===================================================================

Pure Matplotlib script. It creates:

    Figure_6.png   n=4 flow
    Figure_7.png   n=6 flow

The layout follows the supplied flow-diagram concept:

all balanced encodings
        |
        +--> dominators (axis strategies)
        |
        +--> majority-optimal encodings
                  |
                  +--> distinct advantage-space points
                  +--> permutation types
                  +--> vertex types

and also shows the remaining balanced encodings that are neither dominators
nor majority-optimal.

The numbers used here are:

n=4:
    all balanced              C(16,8)  = 12,870
    dominators                          = 8
    majority-optimal          C(6,3)   = 20
    distinct advantage points           = 14
    permutation types                    = 3
    vertex types                         = 2

n=6:
    all balanced              C(64,32)
    dominators                          = 12
    majority-optimal          C(20,10) = 184,756
    distinct advantage points           = 4,733
    permutation types                    = 41
    vertex types                         = 6

Dependencies:
    pip install matplotlib
"""

from __future__ import annotations

from math import comb
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ============================================================================
# OUTPUT
# ============================================================================

HERE = Path(__file__).resolve().parent
OUTPUT_4 = HERE / "Figure_6.png"
OUTPUT_6 = HERE / "Figure_7.png"

DPI = 200
FIGSIZE = (15.36, 10.24)


# ============================================================================
# STYLE
# ============================================================================

FONT = "DejaVu Sans"

TITLE_SIZE = 23
SUBTITLE_SIZE = 15

BIG_NUMBER_SIZE = 24
BOX_TITLE_SIZE = 15
BOX_TEXT_SIZE = 12
SMALL_TEXT_SIZE = 10.5
BOTTOM_TEXT_SIZE = 13.5

BLUE = "#163b7a"
BLUE_EDGE = "#1f4e99"
BLUE_FILL = "#eef4ff"

RED = "#9f0d0d"
RED_EDGE = "#b21d1d"
RED_FILL = "#fff2f2"

GREEN = "#0b5d20"
GREEN_EDGE = "#2d7f3d"
GREEN_FILL = "#f2fbf3"

GRAY = "#666666"
GRAY_EDGE = "#8a8a8a"
GRAY_FILL = "#fbfbfb"

GOLD_EDGE = "#c89a37"
GOLD_FILL = "#fff9e8"

BLACK = "#111111"


# ============================================================================
# DATA
# ============================================================================

DATA = {
    4: {
        "inputs": 16,
        "balanced_choose": (16, 8),
        "dominators": 8,
        "tie_strings": 6,
        "tie_choose": 3,
        "majority_optimal": 20,
        "non_tied": 10,
        "distinct_points": 14,
        "permutation_types": 3,
        "vertex_types": 2,
        "axis_vector": r"$(\pm 1,0,0,0)$ and permutations",
        "catalogue_note": "3 permutation types",
    },
    6: {
        "inputs": 64,
        "balanced_choose": (64, 32),
        "dominators": 12,
        "tie_strings": 20,
        "tie_choose": 10,
        "majority_optimal": 184_756,
        "non_tied": 44,
        "distinct_points": 4_733,
        "permutation_types": 41,
        "vertex_types": 6,
        "axis_vector": r"$(\pm 1,0,0,0,0,0)$ and permutations",
        "catalogue_note": "41 permutation types",
    },
}


# ============================================================================
# DRAWING HELPERS
# ============================================================================

def add_box(
    ax,
    xywh,
    *,
    facecolor,
    edgecolor,
    linewidth=1.4,
    linestyle="-",
    rounding=0.018,
):
    """Add a rounded box in axes coordinates and return the patch."""
    x, y, w, h = xywh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        transform=ax.transAxes,
        boxstyle=f"round,pad=0.008,rounding_size={rounding}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=1,
    )
    ax.add_patch(patch)
    return patch


def add_arrow(
    ax,
    start,
    end,
    *,
    color=BLACK,
    linewidth=2.0,
    mutation_scale=18,
    linestyle="-",
):
    """Arrow in axes coordinates."""
    arrow = FancyArrowPatch(
        start,
        end,
        transform=ax.transAxes,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=linewidth,
        color=color,
        linestyle=linestyle,
        shrinkA=0,
        shrinkB=0,
        zorder=0,
    )
    ax.add_patch(arrow)


def fmt_int(value):
    return f"{int(value):,}"


def draw_top_box(ax, n, d):
    total = comb(*d["balanced_choose"])
    N, K = d["balanced_choose"]

    add_box(
        ax,
        (0.28, 0.73, 0.44, 0.12),
        facecolor=BLUE_FILL,
        edgecolor=BLUE_EDGE,
    )

    ax.text(
        0.50, 0.810,
        fmt_int(total),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BIG_NUMBER_SIZE,
        fontweight="bold",
        color=BLUE,
    )
    ax.text(
        0.50, 0.760,
        "balanced deterministic encodings",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOX_TITLE_SIZE,
        fontweight="bold",
        color=BLUE,
    )
    # ax.text(
    #     0.44, 0.748,
    #     rf"$=\binom{{{N}}}{{{K}}}$",
    #     transform=ax.transAxes,
    #     ha="center", va="center",
    #     fontsize=19,
    #     color=BLACK,
    # )


def draw_dominator_box(ax, n, d):
    add_box(
        ax,
        (0.065, 0.465, 0.25, 0.19),
        facecolor=RED_FILL,
        edgecolor=RED_EDGE,
    )

    ax.text(
        0.19, 0.615,
        fmt_int(d["dominators"]),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=23,
        fontweight="bold",
        color=RED,
    )
    ax.text(
        0.19, 0.572,
        "dominators (axis strategies)",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOX_TITLE_SIZE,
        fontweight="bold",
        color=RED,
    )
    ax.text(
        0.19, 0.515,
        "Alice outputs one chosen bit\n(or its complement)",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOX_TEXT_SIZE,
        color=BLACK,
        linespacing=1.35,
    )
    ax.text(
        0.19, 0.452,
        "Advantage vectors:  " + d["axis_vector"],
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=11.2,
        color=RED,
        fontstyle="italic",
    )


def draw_majority_box(ax, n, d):
    add_box(
        ax,
        (0.375, 0.465, 0.25, 0.19),
        facecolor=GREEN_FILL,
        edgecolor=GREEN_EDGE,
    )

    ax.text(
        0.50, 0.615,
        fmt_int(d["majority_optimal"]),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=23,
        fontweight="bold",
        color=GREEN,
    )
    ax.text(
        0.50, 0.572,
        "majority-optimal encodings",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOX_TITLE_SIZE,
        fontweight="bold",
        color=GREEN,
    )

    ax.text(
        0.50, 0.515,
        f"Majority fixed on {d['non_tied']} non-tied strings;\n"
        f"choose {d['tie_choose']} of the {d['tie_strings']} tied strings to send as 1",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOX_TEXT_SIZE,
        color=BLACK,
        linespacing=1.4,
    )

    # ax.text(
    #     0.50, 0.475,
    #     rf"$\binom{{{d['tie_strings']}}}{{{d['tie_choose']}}}"
    #     rf"={fmt_int(d['majority_optimal'])}$",
    #     transform=ax.transAxes,
    #     ha="center", va="center",
    #     fontsize=17,
    #     color=BLACK,
    # )


def draw_other_box(ax, d):
    total = comb(*d["balanced_choose"])
    other = total - d["dominators"] - d["majority_optimal"]

    add_box(
        ax,
        (0.685, 0.465, 0.25, 0.19),
        facecolor=GRAY_FILL,
        edgecolor=GRAY_EDGE,
        linestyle=(0, (6, 4)),
    )

    ax.text(
        0.81, 0.615,
        fmt_int(other),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=18,
        fontweight="bold",
        color=GRAY,
    )
    ax.text(
        0.81, 0.572,
        "other balanced encodings",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=13.5,
        fontweight="bold",
        color=GRAY,
    )
    ax.text(
        0.81, 0.515,
        "(neither dominators\nnor majority-optimal)",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=11.3,
        color=BLACK,
        linespacing=1.4,
    )


def draw_compression_chain(ax, n, d):
    boxes = [
        (0.25, 0.165, 0.14, 0.195),
        (0.43, 0.165, 0.14, 0.195),
        (0.61, 0.165, 0.14, 0.195),
        #(0.72, 0.165, 0.16, 0.195),
    ]

    for b in boxes:
        add_box(
            ax,
            b,
            facecolor=GREEN_FILL,
            edgecolor=GREEN_EDGE,
            linewidth=1.5,
        )

    # First
    ax.text(
        0.32, 0.325,
        fmt_int(d["distinct_points"]),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=19,
        fontweight="bold",
        color=GREEN,
    )
    ax.text(
        0.32, 0.275,
        "distinct points\nin advantage space",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=11.5,
        fontweight="bold",
        color=GREEN,
        linespacing=1.25,
    )
    ax.text(
        0.32, 0.205,
        "Different encodings\ncan give the same point",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=10.6,
        color=BLACK,
        linespacing=1.35,
    )

    # Second
    ax.text(
        0.50, 0.325,
        fmt_int(d["permutation_types"]),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=19,
        fontweight="bold",
        color=GREEN,
    )
    ax.text(
        0.50, 0.275,
        "permutation\ntypes",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=11.5,
        fontweight="bold",
        color=GREEN,
        linespacing=1.25,
    )
    ax.text(
        0.50, 0.205,
        "Points grouped under\ncoordinate permutations",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=10.6,
        color=BLACK,
        linespacing=1.35,
    )

    # Third
    ax.text(
        0.67, 0.325,
        fmt_int(d["vertex_types"]),
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=19,
        fontweight="bold",
        color=GREEN,
    )
    ax.text(
        0.67, 0.275,
        "vertex types\n(up to permutation)",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=11.2,
        fontweight="bold",
        color=GREEN,
        linespacing=1.25,
    )
    ax.text(
        0.67, 0.205,
        "Distinct vertex shapes\nof the optimal face",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=10.6,
        color=BLACK,
        linespacing=1.35,
    )

    # # Fourth
    # ax.text(
    #     0.80, 0.292,
    #     d["catalogue_note"],
    #     transform=ax.transAxes,
    #     ha="center", va="center",
    #     fontsize=12.0,
    #     fontweight="bold",
    #     color=GREEN,
    #     linespacing=1.3,
    # )

    # if n == 6:
    #     ax.text(
    #         0.80, 0.215,
    #         "41 permutation classes\ncollapse to 6 vertex types",
    #         transform=ax.transAxes,
    #         ha="center", va="center",
    #         fontsize=10.6,
    #         color=BLACK,
    #         linespacing=1.35,
    #     )
    # else:
    #     ax.text(
    #         0.80, 0.215,
    #         "All three types can be\nshown explicitly in the text",
    #         transform=ax.transAxes,
    #         ha="center", va="center",
    #         fontsize=10.6,
    #         color=BLACK,
    #         linespacing=1.35,
    #     )

    # arrows along chain
    add_arrow(
        ax, (0.39, 0.26), (0.43, 0.26),
        color=GREEN_EDGE, linewidth=1.8
    )
    add_arrow(
        ax, (0.57, 0.26), (0.61, 0.26),
        color=GREEN_EDGE, linewidth=1.8
    )
    # add_arrow(
    #     ax, (0.68, 0.26), (0.72, 0.26),
    #     color=GREEN_EDGE, linewidth=1.8
    # )

    # Majority branch continues into the green compression chain.
    add_arrow(
        ax, (0.50, 0.465), (0.50, 0.365),
        color=GREEN_EDGE, linewidth=2.2
    )


def draw_big_picture(ax, n, d):
    total = comb(*d["balanced_choose"])

    add_box(
        ax,
        (0.08, 0.018, 0.82, 0.11),
        facecolor=GOLD_FILL,
        edgecolor=GOLD_EDGE,
        linewidth=1.1,
    )

    if n == 4:
        line1 = (
            f"Out of {fmt_int(total)} balanced encodings, "
            f"only {d['dominators']} are dominators and "
            f"{fmt_int(d['majority_optimal'])} achieve majority-optimal performance."
        )
        line2 = (
            f"Geometry and symmetry collapse those "
            f"{fmt_int(d['majority_optimal'])} optimal encodings to "
            f"{d['vertex_types']} vertex types."
        )
    else:
        line1 = (
            rf"Out of $\sim 1.83\times10^{{18}}$ balanced encodings, "
            f"only {d['dominators']} are dominators and "
            f"{fmt_int(d['majority_optimal'])} achieve majority-optimal performance."
        )
        line2 = (
            f"Geometry and symmetry collapse those optimal encodings to "
            f"{d['vertex_types']} vertex types."
        )

    ax.text(
        0.12, 0.090,
        "Big picture:",
        transform=ax.transAxes,
        ha="left", va="center",
        fontsize=BOTTOM_TEXT_SIZE,
        fontweight="bold",
        color=BLACK,
    )
    ax.text(
        0.23, 0.090,
        line1,
        transform=ax.transAxes,
        ha="left", va="center",
        fontsize=BOTTOM_TEXT_SIZE,
        color=BLACK,
    )
    ax.text(
        0.49, 0.048,
        line2,
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=BOTTOM_TEXT_SIZE,
        color=BLACK,
    )


def draw_flow(n, output):
    d = DATA[n]

    fig = plt.figure(
        figsize=FIGSIZE,
        dpi=DPI,
        facecolor="white",
    )
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()

    # Title
    ax.text(
        0.1, 0.965,
        rf"$n={n}$: From All Balanced Encodings to the Key Families",
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=TITLE_SIZE,
        fontweight="bold",
        color=BLACK,
    )

    ax.text(
        0.1, 0.912,
        f"One-bit deterministic encodings of the {d['inputs']} input strings "
        f"({d['inputs']//2} sent as 1, {d['inputs']//2} sent as 0)",
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=SUBTITLE_SIZE,
        color=BLACK,
    )

    # Main boxes
    draw_top_box(ax, n, d)
    draw_dominator_box(ax, n, d)
    draw_majority_box(ax, n, d)
    draw_other_box(ax, d)
    draw_compression_chain(ax, n, d)
    draw_big_picture(ax, n, d)

    # Top split arrows.
    add_arrow(
        ax, (0.50, 0.71), (0.19, 0.67),
        color=RED_EDGE, linewidth=2.2
    )
    add_arrow(
        ax, (0.50, 0.71), (0.50, 0.67),
        color=GREEN_EDGE, linewidth=2.2
    )
    add_arrow(
        ax, (0.50, 0.71), (0.81, 0.67),
        color=GRAY_EDGE, linewidth=2.2
    )

    # # Majority -> other branch is dashed to emphasize "everything else".
    # add_arrow(
    #     ax,
    #     (0.625, 0.56),
    #     (0.685, 0.56),
    #     color=GRAY,
    #     linewidth=1.5,
    #     mutation_scale=15,
    #     linestyle=(0, (5, 4)),
    # )

    fig.savefig(
        output,
        dpi=DPI,
        facecolor="white",
        bbox_inches=None,
    )
    plt.close(fig)

    print(f"Saved: {output}")


def main():
    draw_flow(4, OUTPUT_4)
    draw_flow(6, OUTPUT_6)


if __name__ == "__main__":
    main()
