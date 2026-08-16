"""
Figure 2 — two 2D cross-sections of the n=3 RAC classical polytope
===================================================================

The figure is designed to follow the full n=3 polytope figure and to prepare
the reader for the n=4 cross-sections.

Panels
------
A: plane perpendicular to (1,0,0), i.e. c1 = 0
B: plane perpendicular to (1,-1,0), i.e. c1 = c2

The underlying 3D polytope is the same as in Figure 1:
- axis vertices: ±(1,0,0) and permutations
- majority vertices: all sign choices of (1/2,1/2,1/2)

The two plotted coordinate axes in each section are genuine directions in the
original 3D advantage space. They are internally normalized for plotting, but
their labels are shown as sparse primitive integer vectors.

Dependencies
------------
pip install numpy scipy matplotlib
"""

from __future__ import annotations

from pathlib import Path
from math import gcd

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull


# ============================================================================
# OUTPUT / LAYOUT
# ============================================================================

OUTPUT = Path(__file__).with_name("Figure_2.png")

FIGURE_SIZE_INCH = (15.36, 8.7)
DPI = 200

SLICES = [
    ("A", np.array([1, 0, 0], dtype=int), 0.0),      # c1 = 0
    ("B", np.array([1, -1, 0], dtype=int), 0.0),     # c1 = c2
]

PANEL_BOXES = [
    [0.055, 0.18, 0.41, 0.68],
    [0.535, 0.18, 0.41, 0.68],
]

LEGEND_BOX = [0.08, 0.035, 0.84, 0.075]


# ============================================================================
# APPEARANCE
# ============================================================================

OBJECT_COLOR = "lightblue"
OBJECT_ALPHA = 0.72
EDGE_COLOR = "black"
EDGE_WIDTH = 1.5

AXIS_LINE_COLOR = "black"
AXIS_LINE_WIDTH = 1.25
AXIS_LENGTH_SCALE = 1.12

AXIS_LABEL_FONT_SIZE = 12.5
AXIS_LABEL_PAD = 0.06

# Vertex colors encode vertex TYPE, not coordinate direction.
AXIS_TYPE_COLOR = "crimson"
MAJORITY_TYPE_COLOR = "darkorange"

AXIS_VERTEX_SIZE = 70
MAJORITY_VERTEX_SIZE = 60

# The positive symmetric optimum is one member of the majority-type family.
# It is emphasized only by marker size / outline, not by a third type color.
MARK_OPTIMUM = False
OPTIMUM_VERTEX_SIZE = 110
OPTIMUM_EDGE_COLOR = "darkorange"
OPTIMUM_EDGE_WIDTH = 2.0

SHOW_SECTION_INTERSECTION_POINTS = False
SECTION_POINT_SIZE = 28
SECTION_POINT_COLOR = "black"


# ============================================================================
# n=3 POLYTOPE
# ============================================================================

AXIS_VERTICES = np.array([
    [ 1.0,  0.0,  0.0],
    [-1.0,  0.0,  0.0],
    [ 0.0,  1.0,  0.0],
    [ 0.0, -1.0,  0.0],
    [ 0.0,  0.0,  1.0],
    [ 0.0,  0.0, -1.0],
])

MAJORITY_VERTICES = 0.5 * np.array([
    [sx, sy, sz]
    for sx in (-1.0, 1.0)
    for sy in (-1.0, 1.0)
    for sz in (-1.0, 1.0)
])

OPTIMUM = np.array([0.5, 0.5, 0.5])

ALL_VERTICES = np.vstack([
    AXIS_VERTICES,
    MAJORITY_VERTICES,
])

TOL = 1e-9


# ============================================================================
# GEOMETRY
# ============================================================================

def primitive_integer_vector(v):
    """Reduce an integer vector by its positive gcd without flipping sign."""
    v = np.asarray(v, dtype=int)
    nz = np.abs(v[v != 0])

    if len(nz) == 0:
        raise ValueError("Zero vector has no direction.")

    g = int(nz[0])
    for value in nz[1:]:
        g = gcd(g, int(value))

    return v // g


def sparse_oriented_basis_3d(raw_normal):
    """
    Return two sparse, mutually orthogonal integer directions in the slice.

    The construction is deterministic. Orientation is chosen once while the
    basis is constructed and is then used consistently for coordinates,
    plotting and labels.
    """
    n = primitive_integer_vector(raw_normal)

    active = [int(i) for i in np.flatnonzero(n)]
    zero = [i for i in range(3) if n[i] == 0]

    vectors = []

    # Sparse direction among active coordinates.
    if len(active) >= 2:
        i, j = active[0], active[1]

        v = np.zeros(3, dtype=int)
        v[i] = n[j]
        v[j] = -n[i]

        # Choose orientation at construction time only.
        first = np.flatnonzero(v)
        if len(first) and v[first[0]] < 0:
            v = -v

        vectors.append(primitive_integer_vector(v))

    # Any coordinate absent from the normal lies directly in the slice.
    for j in zero:
        v = np.zeros(3, dtype=int)
        v[j] = 1
        vectors.append(v)

    # For a 3D hyperplane we need exactly two independent directions.
    # If all three normal entries are nonzero, construct a second vector by
    # cross product, then reduce to primitive integers.
    if len(vectors) == 1:
        v1 = vectors[0]
        v2 = np.cross(n, v1)

        first = np.flatnonzero(v2)
        if len(first) and v2[first[0]] < 0:
            v2 = -v2

        vectors.append(primitive_integer_vector(v2))

    if len(vectors) != 2:
        raise RuntimeError(
            f"Expected two slice axes, got {len(vectors)} for normal {tuple(n)}."
        )

    if np.dot(vectors[0], vectors[1]) != 0:
        raise RuntimeError("Constructed section axes are not orthogonal.")

    for v in vectors:
        if np.dot(n, v) != 0:
            raise RuntimeError("Constructed axis is not in the slice.")

    return vectors


def normalized_basis_matrix(vectors3):
    """3x2 orthonormal basis matrix used for actual projection."""
    return np.column_stack([
        np.asarray(v, dtype=float) / np.linalg.norm(v)
        for v in vectors3
    ])


def hull_candidate_edges(vertices):
    """
    Candidate edges from scipy's triangulated convex hull.

    Extra coplanar diagonals are harmless: after intersection we take a 2D
    convex hull, which removes non-boundary candidates.
    """
    hull = ConvexHull(vertices)
    edges = set()

    for tri in hull.simplices:
        for a, b in (
            (int(tri[0]), int(tri[1])),
            (int(tri[1]), int(tri[2])),
            (int(tri[2]), int(tri[0])),
        ):
            edges.add(tuple(sorted((a, b))))

    return sorted(edges)


def unique_rows(points, decimals=10):
    p = np.asarray(points, dtype=float)
    rounded = np.round(p, decimals)
    _, idx = np.unique(rounded, axis=0, return_index=True)
    return p[np.sort(idx)]


def section_points_3d(vertices, normal, offset):
    """Intersect the 3D polytope boundary candidate edges with a plane."""
    normal = np.asarray(normal, dtype=float)
    normal /= np.linalg.norm(normal)
    offset = float(offset)

    signed = vertices @ normal - offset
    points = []

    for i, j in hull_candidate_edges(vertices):
        vi, vj = vertices[i], vertices[j]
        fi, fj = signed[i], signed[j]

        if abs(fi) <= TOL and abs(fj) <= TOL:
            points.extend((vi, vj))
        elif abs(fi) <= TOL:
            points.append(vi)
        elif abs(fj) <= TOL:
            points.append(vj)
        elif fi * fj < 0:
            t = fi / (fi - fj)
            points.append(vi + t * (vj - vi))

    if not points:
        raise ValueError("Selected plane does not intersect the polytope.")

    return unique_rows(np.asarray(points), decimals=9)


def project_to_slice(points3, normal, offset, basis):
    normal = np.asarray(normal, dtype=float)
    normal /= np.linalg.norm(normal)
    x0 = float(offset) * normal
    return (points3 - x0) @ basis


def compute_section(raw_normal, raw_offset):
    normal = np.asarray(raw_normal, dtype=float)
    normal /= np.linalg.norm(normal)
    offset = float(raw_offset)

    axis_vectors = sparse_oriented_basis_3d(raw_normal)
    basis = normalized_basis_matrix(axis_vectors)

    points3 = section_points_3d(ALL_VERTICES, normal, offset)
    points2 = project_to_slice(points3, normal, offset, basis)

    hull2 = ConvexHull(points2)
    boundary = points2[hull2.vertices]

    return normal, offset, axis_vectors, basis, points3, points2, boundary


# ============================================================================
# LABELS / CLASSIFICATION
# ============================================================================

def format_direction(v):
    return "(" + ",".join(str(int(x)) for x in v) + ")"


def slice_label(raw_normal, raw_offset):
    n = np.asarray(raw_normal, dtype=float)
    nz = np.flatnonzero(np.abs(n) > 1e-9)

    if len(nz) == 1 and abs(raw_offset) < TOL:
        return rf"$c_{nz[0] + 1}=0$"

    if len(nz) == 2 and abs(raw_offset) < TOL:
        i, j = map(int, nz)

        if np.isclose(n[i], -n[j]):
            return rf"$c_{i+1}=c_{j+1}$"

        if np.isclose(n[i], n[j]):
            return rf"$c_{i+1}=-c_{j+1}$"

    return rf"$n\cdot c={raw_offset:g}$"


def original_vertices_in_slice(normal, offset):
    mask = np.abs(ALL_VERTICES @ normal - offset) <= 1e-8
    return ALL_VERTICES[mask]


def is_axis_vertex(v):
    return np.isclose(np.sum(np.abs(v)), 1.0) and np.count_nonzero(np.abs(v) > 1e-8) == 1


def coordinate_index_of_axis_vertex(v):
    return int(np.flatnonzero(np.abs(v) > 1e-8)[0])


def is_optimum(v):
    return np.allclose(v, OPTIMUM, atol=1e-8, rtol=0.0)


# ============================================================================
# PLOTTING
# ============================================================================

def draw_panel(ax, letter, raw_normal, raw_offset):
    normal, offset, axis_vectors, basis, points3, points2, boundary = compute_section(
        raw_normal,
        raw_offset,
    )

    # Filled section polygon.
    ax.fill(
        boundary[:, 0],
        boundary[:, 1],
        facecolor=OBJECT_COLOR,
        alpha=OBJECT_ALPHA,
        edgecolor=EDGE_COLOR,
        linewidth=EDGE_WIDTH,
        zorder=1,
    )

    # Draw the two true section axes through the origin.
    extent = max(np.max(np.abs(boundary[:, 0])), np.max(np.abs(boundary[:, 1])))
    axis_length = AXIS_LENGTH_SCALE * extent

    for axis_index, v in enumerate(axis_vectors):
        d2 = np.eye(2)[axis_index]

        # Full line through the slice helps convey "cross-section coordinates".
        ax.plot(
            [-axis_length * d2[0], axis_length * d2[0]],
            [-axis_length * d2[1], axis_length * d2[1]],
            color=AXIS_LINE_COLOR,
            linewidth=AXIS_LINE_WIDTH,
            zorder=3,
        )

        # Label only the positive oriented direction.
        tip = d2 * axis_length

        if axis_index == 0:
            ha, va = "left", "bottom"
            xytext = (AXIS_LABEL_PAD, AXIS_LABEL_PAD)
        else:
            ha, va = "center", "bottom"
            xytext = (0.0, AXIS_LABEL_PAD)

        ax.text(
            tip[0] + xytext[0],
            tip[1] + xytext[1],
            format_direction(v),
            fontsize=AXIS_LABEL_FONT_SIZE,
            color="black",
            ha=ha,
            va=va,
            zorder=6,
        )

    # Original 3D vertices that genuinely lie in this plane.
    original = original_vertices_in_slice(normal, offset)

    for v in original:
        p2 = project_to_slice(np.asarray([v]), normal, offset, basis)[0]

        if is_optimum(v) and MARK_OPTIMUM:
            # Same majority-type color; only the orange outline/size marks
            # this particular vertex as the symmetric optimum.
            ax.scatter(
                [p2[0]], [p2[1]],
                s=OPTIMUM_VERTEX_SIZE,
                c=[MAJORITY_TYPE_COLOR],
                edgecolors=OPTIMUM_EDGE_COLOR,
                linewidths=OPTIMUM_EDGE_WIDTH,
                zorder=8,
            )
        elif is_axis_vertex(v):
            ax.scatter(
                [p2[0]], [p2[1]],
                s=AXIS_VERTEX_SIZE,
                c=[AXIS_TYPE_COLOR],
                edgecolors="black",
                linewidths=0.7,
                zorder=7,
            )
        else:
            ax.scatter(
                [p2[0]], [p2[1]],
                s=MAJORITY_VERTEX_SIZE,
                c=[MAJORITY_TYPE_COLOR],
                edgecolors="black",
                linewidths=0.6,
                zorder=7,
            )

    if SHOW_SECTION_INTERSECTION_POINTS:
        ax.scatter(
            points2[:, 0],
            points2[:, 1],
            s=SECTION_POINT_SIZE,
            c=SECTION_POINT_COLOR,
            zorder=5,
        )

    ax.scatter([0], [0], s=20, c=["black"], zorder=9)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # Give both panels comparable breathing room.
    lim = axis_length * 1.18
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    ax.text(
        0.015, 1.02,
        f"{letter}",
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        ha="left",
        va="top",
    )
    ax.text(
        0.095, 1.02,
        slice_label(raw_normal, raw_offset),
        transform=ax.transAxes,
        fontsize=15,
        ha="left",
        va="top",
    )

    # Small line listing the actual oriented basis.
    basis_text = "In plane directions: " + "   ·   ".join(format_direction(v) for v in axis_vectors)
    ax.text(
        0.5, -0.02,
        basis_text,
        transform=ax.transAxes,
        fontsize=10.8,
        ha="center",
        va="top",
        color="black",
    )


def add_shared_legend(fig):
    """One shared legend: only the two genuine n=3 vertex types."""
    ax = fig.add_axes(LEGEND_BOX)
    ax.set_axis_off()

    entries = [
        (
            AXIS_TYPE_COLOR,
            r"Axis type $(1,0,0)$ and permutations/signs",
            125,
            "black",
            0.7,
        ),
        (
            MAJORITY_TYPE_COLOR,
            r"$1/2+1/2+1/2$ type $(0.5,0.5,0.5)$ and sign variants",
            125,
            "black",
            0.7,
        ),
    ]

    xs = [0.12, 0.55]

    for x, (color, label, size, edge, lw) in zip(xs, entries):
        ax.scatter(
            [x], [0.55],
            s=size,
            c=[color],
            edgecolors=edge,
            linewidths=lw,
            transform=ax.transAxes,
        )
        ax.text(
            x + 0.03,
            0.55,
            label,
            color=color,
            fontsize=11.0,
            va="center",
            transform=ax.transAxes,
        )
    if MARK_OPTIMUM:
        ax.scatter(
            [0.12], [0.18],
            s=OPTIMUM_VERTEX_SIZE,
            c=[MAJORITY_TYPE_COLOR],
            edgecolors=OPTIMUM_EDGE_COLOR,
            linewidths=OPTIMUM_EDGE_WIDTH,
            transform=ax.transAxes,
        )
        ax.text(
            0.15,
            0.18,
            r"orange outline: symmetric optimum $(\frac{1}{2},\frac{1}{2},\frac{1}{2})$",
            fontsize=10.4,
            va="center",
            color="black",
            transform=ax.transAxes,
        )
        # Small annotation, deliberately not presented as a third vertex type.
        ax.scatter(
            [0.74], [0.18],
            s=145,
            c=[MAJORITY_TYPE_COLOR],
            edgecolors=OPTIMUM_EDGE_COLOR,
            linewidths=OPTIMUM_EDGE_WIDTH,
            transform=ax.transAxes,
        )
        ax.text(
            0.77,
            0.18,
            r"orange outline: symmetric optimum $(\frac{1}{2},\frac{1}{2},\frac{1}{2})$",
            fontsize=10.4,
            va="center",
            color="black",
            transform=ax.transAxes,
        )


def compose():
    fig = plt.figure(
        figsize=FIGURE_SIZE_INCH,
        dpi=DPI,
        facecolor="white",
    )

    fig.text(
        0.035, 0.965,
        "n=3 cross-sections",
        fontsize=22,
        fontweight="bold",
        ha="left",
        va="top",
    )

    fig.text(
        0.035, 0.922,
        "Two 2D cuts through the same 3D classical advantage-space polytope",
        fontsize=14.5,
        ha="left",
        va="top",
    )

    for (letter, normal, offset), box in zip(SLICES, PANEL_BOXES):
        ax = fig.add_axes(box)
        draw_panel(ax, letter, normal, offset)

    add_shared_legend(fig)

    fig.savefig(
        OUTPUT,
        dpi=DPI,
        facecolor="white",
        bbox_inches=None,
    )
    plt.close(fig)


def main():
    for letter, normal, offset in SLICES:
        _, _, axis_vectors, _, _, _, boundary = compute_section(normal, offset)
        print(
            f"{letter}: normal={tuple(normal)}, offset={offset:g}, "
            f"section vertices={len(boundary)}, "
            f"axes={', '.join(format_direction(v) for v in axis_vectors)}"
        )

    compose()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()