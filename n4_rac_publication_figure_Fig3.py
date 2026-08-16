"""
Figure 3 in Blog about higher dimensional RACs

Publication-quality n=4 RAC advantage-space cross-section figure
================================================================

Hybrid renderer:
    * PyVista / VTK renders the 3D polytope, true edges, vertices and arrows.
    * Matplotlib composes the publication layout, title, legend and notes.

This script intentionally keeps the geometry engine separate.  Put it next to:

    n4_rac_cross_section_axis_inset_planar_edges.py

The latter remains the single source of truth for the 4D polytope, slicing and
true planar-face edge reconstruction.  This file only handles rendering and
figure composition.

Dependencies
------------
pip install numpy scipy pyvista matplotlib

For headless Linux rendering you may also need an X/VTK backend; on a normal
Windows desktop PyVista generally works directly.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pyvista as pv


# =============================================================================
# USER SETTINGS
# =============================================================================

# Cross-section in original advantage coordinates c=(c1,c2,c3,c4).
SLICE_NORMAL = np.array([1.0, 0.0, 0.0, 0.0])
SLICE_OFFSET = 0.0

# Geometry implementation used by this publication renderer.
BASE_SCRIPT = Path(__file__).with_name(
    "n4_rac_cross_section_axis_inset_planar_edges.py"
)

# Final output.
OUTPUT = Path(__file__).with_name("Figure_3.png")
FIGURE_SIZE_INCH = (15.36, 10.24)   # 3:2, close to the target layout
DPI = 200                            # final image = 3072 x 2048 px

# Internal PyVista render resolution.  Higher values improve 3D antialiasing.
POLYTOPE_RENDER_SIZE = (1900, 1700)
AXIS_RENDER_SIZE = (1000, 850)

# Main 3D camera: exactly one definition reused for both 3D renders.
CAMERA_POSITION = (3.0, 2.0, 1.0)
CAMERA_FOCAL_POINT = (0.0, 0.0, 0.0)
CAMERA_UP = (0.0, 0.0, 1.0)
PARALLEL_PROJECTION = False
CAMERA_ZOOM = 1.04

# Main object appearance.
OBJECT_COLOR = "lightblue"
OBJECT_OPACITY = 0.92
EDGE_COLOR = "black"
EDGE_WIDTH = 2.0
VERTEX_SIZE = 24

# Advantage-coordinate arrows on the large polytope.
SHOW_MAIN_AXES = True
MAIN_AXIS_LENGTH = 1.18

# Small coordinate triad shown at lower right.
AXIS_INSET_LENGTH = 0.82
AXIS_INSET_ORIGIN_RADIUS = 0.032

# Original 4D coordinate colors.  Keep these fixed between all future figures.
AXIS_COLORS = ("crimson", "green", "royalblue", "purple")

# Vertex colors: same convention as the geometry script / current visual.
VERTEX_COLORS = {
    "axis type (1,0,0,0)": "crimson",
    "3/4 + 1/4 type": "royalblue",
    "1/2 + 1/2 + 1/2 type": "darkorange",
}

# Lighting.
KEY_LIGHT_POSITION = (4.0, 3.0, 5.0)
KEY_LIGHT_INTENSITY = 1.0
FILL_LIGHT_POSITION = (-3.0, -2.0, 2.0)
FILL_LIGHT_INTENSITY = 0.38

# Layout in Matplotlib figure coordinates.
LEFT_IMAGE_BOX = [0.025, 0.115, 0.585, 0.755]
RIGHT_LEGEND_BOX = [0.625, 0.435, 0.35, 0.33]
RIGHT_AXIS_BOX = [0.625, 0.025, 0.35, 0.37]
NOTE_BOX = [0.025, 0.025, 0.5, 0.08]

# Title and subtitle
TITLE_POSITION = (0.025, 0.955)
SUBTITLE_POSITION = (0.025, 0.912)

# =============================================================================
# LOAD GEOMETRY ENGINE
# =============================================================================

def load_geometry_module():
    if not BASE_SCRIPT.exists():
        raise FileNotFoundError(
            f"Could not find geometry script:\n{BASE_SCRIPT}\n\n"
            "Place this publication renderer in the same directory as "
            "n4_rac_cross_section_axis_inset_planar_edges.py."
        )

    spec = importlib.util.spec_from_file_location("rac_geom", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {BASE_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# =============================================================================
# SMALL HELPERS
# =============================================================================

def normalize_slice(normal, offset):
    normal = np.asarray(normal, dtype=float)
    norm = np.linalg.norm(normal)
    if norm == 0:
        raise ValueError("SLICE_NORMAL cannot be zero.")
    return normal / norm, float(offset) / norm


def apply_camera(plotter: pv.Plotter):
    plotter.camera.position = CAMERA_POSITION
    plotter.camera.focal_point = CAMERA_FOCAL_POINT
    plotter.camera.up = CAMERA_UP

    if PARALLEL_PROJECTION:
        plotter.enable_parallel_projection()
    else:
        plotter.disable_parallel_projection()

    if CAMERA_ZOOM != 1.0:
        plotter.camera.zoom(CAMERA_ZOOM)


def apply_lighting(plotter: pv.Plotter):
    plotter.remove_all_lights()

    plotter.add_light(
        pv.Light(
            position=KEY_LIGHT_POSITION,
            focal_point=CAMERA_FOCAL_POINT,
            intensity=KEY_LIGHT_INTENSITY,
        )
    )
    plotter.add_light(
        pv.Light(
            position=FILL_LIGHT_POSITION,
            focal_point=CAMERA_FOCAL_POINT,
            intensity=FILL_LIGHT_INTENSITY,
        )
    )


def rgba_crop(image, pad=18):
    """Crop transparent margins around a PyVista RGBA screenshot."""
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 4:
        return image

    alpha = image[:, :, 3]
    ys, xs = np.where(alpha > 2)
    if len(xs) == 0:
        return image

    x0 = max(0, xs.min() - pad)
    x1 = min(image.shape[1], xs.max() + pad + 1)
    y0 = max(0, ys.min() - pad)
    y1 = min(image.shape[0], ys.max() + pad + 1)
    return image[y0:y1, x0:x1]


def slice_label(normal, offset):
    """Pretty equation for common slices."""
    nz = np.flatnonzero(np.abs(normal) > 1e-9)

    # c_i = d
    if len(nz) == 1:
        i = int(nz[0])
        value = offset / normal[i]
        return rf"$c_{i+1}={value:g}$"

    # zero-offset two-coordinate relations, e.g. c1-c2=0.
    if abs(offset) < 1e-9 and len(nz) == 2:
        i, j = map(int, nz)
        a, b = normal[i], normal[j]
        if np.isclose(a, -b):
            return rf"$c_{i+1}=c_{j+1}$"
        if np.isclose(a, b):
            return rf"$c_{i+1}=-c_{j+1}$"

    parts = []
    for i, value in enumerate(normal):
        if abs(value) > 1e-9:
            parts.append(f"{value:+.2g}c{i+1}")
    expr = " ".join(parts).lstrip("+")
    return rf"${expr}={offset:g}$"


def axes_in_slice(normal, basis):
    """Return original coordinate axes e_i that lie exactly in the slice."""
    result = []
    for i in range(4):
        e4 = np.zeros(4)
        e4[i] = 1.0
        if abs(np.dot(normal, e4)) > 1e-8:
            continue
        d3 = e4 @ basis
        nrm = np.linalg.norm(d3)
        if nrm > 1e-10:
            result.append((i, d3 / nrm))
    return result


# =============================================================================
# PYVISTA RENDERS
# =============================================================================

def render_polytope(geom, points3, hull3, vertices4, normal, offset, x0, basis):
    """Render only the large 3D object to an RGBA array."""
    mesh = geom.make_mesh(points3, hull3)

    plotter = pv.Plotter(off_screen=True, window_size=POLYTOPE_RENDER_SIZE)
    plotter.set_background("white")
    plotter.image_transparent_background = True
    apply_lighting(plotter)

    plotter.add_mesh(
        mesh,
        color=OBJECT_COLOR,
        opacity=OBJECT_OPACITY,
        smooth_shading=False,
        show_edges=False,
    )

    # Reuse the robust planar-face boundary extraction from the geometry engine.
    old_edge_color = getattr(geom, "EDGE_COLOR", None)
    old_edge_width = getattr(geom, "EDGE_WIDTH", 1.5)
    old_show_edges = getattr(geom, "SHOW_EDGES", True)
    geom.EDGE_COLOR = EDGE_COLOR
    geom.EDGE_WIDTH = EDGE_WIDTH
    geom.SHOW_EDGES = True
    geom.add_feature_edges(plotter, points3, hull3)
    geom.EDGE_COLOR = old_edge_color
    geom.EDGE_WIDTH = old_edge_width
    geom.SHOW_EDGES = old_show_edges

    # Genuine original 4D vertices lying in the slice.
    old_size = getattr(geom, "ORIGINAL_VERTEX_SIZE", 18)
    old_colors = dict(getattr(geom, "VERTEX_TYPE_COLORS", {}))
    geom.ORIGINAL_VERTEX_SIZE = VERTEX_SIZE
    for key, color in VERTEX_COLORS.items():
        geom.VERTEX_TYPE_COLORS[key] = color
    geom.add_original_vertices(plotter, vertices4, normal, offset, x0, basis)
    geom.ORIGINAL_VERTEX_SIZE = old_size
    geom.VERTEX_TYPE_COLORS.update(old_colors)

    if SHOW_MAIN_AXES:
        for i in range(4):
            e = np.zeros(4)
            e[i] = 1.0

            d3 = geom.project_direction_to_slice(e, normal, basis)
            if d3 is None:
                continue

            end = np.asarray(d3) * MAIN_AXIS_LENGTH

            line = pv.Line((0.0, 0.0, 0.0), end)
            plotter.add_mesh(
                line,
                color="black",
                line_width=2.0,
                lighting=False,
            )

    apply_camera(plotter)
    plotter.render()
    image = plotter.screenshot(
        return_img=True,
        transparent_background=True,
    )
    plotter.close()
    return rgba_crop(image, pad=24)


def add_arrow(plotter, start, direction, length, color):
    arrow = pv.Arrow(
        start=start,
        direction=direction,
        tip_length=0.20,
        tip_radius=0.065,
        shaft_radius=0.018,
        scale=length,
    )
    plotter.add_mesh(arrow, color=color, lighting=True)


def render_axis_triad(normal, basis):
    """
    Render the original advantage axes that lie in the selected slice.

    It uses exactly the same 3D camera orientation as the polytope render.
    """
    axes = axes_in_slice(normal, basis)

    plotter = pv.Plotter(off_screen=True, window_size=AXIS_RENDER_SIZE)
    plotter.set_background("white")
    plotter.image_transparent_background = True
    apply_lighting(plotter)

    origin = np.zeros(3)
    plotter.add_mesh(
        pv.Sphere(radius=AXIS_INSET_ORIGIN_RADIUS, center=origin),
        color="black",
        lighting=False,
    )

    for i, d3 in axes:
        color = AXIS_COLORS[i]
        add_arrow(plotter, origin, d3, AXIS_INSET_LENGTH, color)
        pos = d3 * (AXIS_INSET_LENGTH * 1.13)
        plotter.add_point_labels(
            np.asarray([pos]),
            [f"c{i+1}"],
            point_size=0,
            font_size=22,
            bold=True,
            always_visible=True,
            shape=None,
            text_color=color,
        )

    # Same camera vectors and perspective.  We zoom slightly farther out so
    # labels fit, but do not rotate the camera.
    apply_camera(plotter)
    plotter.camera.zoom(0.82)
    plotter.render()
    image = plotter.screenshot(
        return_img=True,
        transparent_background=True,
    )
    plotter.close()
    return rgba_crop(image, pad=35), axes


# =============================================================================
# MATPLOTLIB COMPOSITION
# =============================================================================

def add_vertex_legend(ax):
    ax.set_axis_off()
    ax.text(
        0.0, 0.99,
        r"Vertex types in advantage coordinates",
        ha="left", va="top", fontsize=14.5, fontweight="bold",
        transform=ax.transAxes,
    )

    rows = [
        (
            "axis type (1,0,0,0)",
            "crimson",
            r"Axis type $(1,0,0,0)$ and permutations",
            r"sign choices and coordinate permutations",
        ),
        (
            "3/4 + 1/4 type",
            "royalblue",
            r"$3/4+1/4$ type $(0.75,0.25,0.25,0.25)$",
            r"sign choices and coordinate permutations",
        ),
        (
            "1/2 + 1/2 + 1/2 type",
            "darkorange",
            r"$1/2+1/2+1/2$ type $(0.5,0.5,0.5,0)$",
            r"sign choices and coordinate permutations",
        ),
    ]

    ys = [0.74, 0.44, 0.14]
    for (_, color, line1, line2), y in zip(rows, ys):
        ax.scatter(
            [0.035], [y + 0.065], s=210,
            c=[color], edgecolors="black", linewidths=0.8,
            transform=ax.transAxes, zorder=3,
        )
        ax.text(
            0.14, y + 0.09, line1,
            color=color, fontsize=12.3, fontweight="bold",
            ha="left", va="center", transform=ax.transAxes,
        )
        ax.text(
            0.14, y - 0.01, line2,
            color="black", fontsize=11.4,
            ha="left", va="center", transform=ax.transAxes,
        )


def add_axis_panel(fig, axis_image, axes, normal):
    ax = fig.add_axes(RIGHT_AXIS_BOX)
    ax.set_axis_off()

    # Rounded panel in Matplotlib: crisp at any output DPI.
    panel = FancyBboxPatch(
        (0.005, 0.005), 1.0, 1.0,
        boxstyle="round,pad=0.018,rounding_size=0.045",
        linewidth=1.25, edgecolor="#315b86", facecolor="white",
        transform=ax.transAxes, clip_on=False, zorder=0,
    )
    ax.add_patch(panel)

    ax.text(
        0.05, 0.93,
        "Axes that lie in this cross-section",
        ha="left", va="top", fontsize=13.2, fontweight="bold",
        transform=ax.transAxes,
    )

    # Inset image occupies upper/middle part of panel.
    img_ax = ax.inset_axes([0.07, 0.25, 0.86, 0.60])
    img_ax.imshow(axis_image)
    img_ax.set_axis_off()

    # Exact original-coordinate vectors, rendered as text below.
    if axes:
        descriptions = []
        for i, _ in axes:
            vec = [0, 0, 0, 0]
            vec[i] = 1
            descriptions.append(rf"$c_{i+1}$: {tuple(vec)}")
        line = "   ·   ".join(descriptions)
        ax.text(
            0.5, 0.15, line,
            ha="center", va="center", fontsize=10.8,
            transform=ax.transAxes,
        )

    missing = [i + 1 for i in range(4) if abs(normal[i]) > 1e-8]
    if len(missing) == 1:
        ax.text(
            0.5, 0.065,
            rf"$c_{missing[0]}$ is perpendicular to this coordinate slice.",
            ha="center", va="center", fontsize=10.5,
            transform=ax.transAxes,
        )


def add_note(fig, normal):
    ax = fig.add_axes(NOTE_BOX)
    ax.set_axis_off()

    border = FancyBboxPatch(
        (0.01, 0.04), 1.0, 1.0,
        boxstyle="round,pad=0.018,rounding_size=0.04",
        linewidth=1.2, edgecolor="purple", facecolor="white",
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(border)

    nz = np.flatnonzero(np.abs(normal) > 1e-8)
    if len(nz) == 1:
        i = int(nz[0]) + 1
        text = (
            rf"We slice perpendicular to $c_{i}$, so $c_{i}$ does not "
            "appear as an axis in this 3D cross-section."
        )
    else:
        text = (
            "The slice removes the direction normal to the hyperplane; "
            "the remaining three directions form its 3D coordinate system."
        )

    ax.text(
        0.055, 0.52, text,
        ha="left", va="center", fontsize=11.2,
        wrap=True, transform=ax.transAxes,
    )


def compose_figure(poly_image, axis_image, axes, normal, offset):
    fig = plt.figure(figsize=FIGURE_SIZE_INCH, dpi=DPI, facecolor="white")

    # Title / subtitle are Matplotlib text rather than VTK text: much crisper.
    fig.text(
        TITLE_POSITION[0], TITLE_POSITION[1],
        "n=4 advantage-space cross-section",
        ha="left", va="top", fontsize=22, fontweight="bold",
    )
    normal_text = "(" + ", ".join(f"{x:g}" for x in SLICE_NORMAL) + ")"
    fig.text(
        SUBTITLE_POSITION[0], SUBTITLE_POSITION[1],
        rf"A 3D cut through the 4D classical advantage-space polytope, "
        rf"normal = {normal_text}, ",
        #rf"offset = {SLICE_OFFSET:g}   ({slice_label(normal, offset)})",
        ha="left", va="top", fontsize=16.5,
    )

    ax_main = fig.add_axes(LEFT_IMAGE_BOX)
    ax_main.imshow(poly_image)
    ax_main.set_axis_off()

    ax_legend = fig.add_axes(RIGHT_LEGEND_BOX)
    add_vertex_legend(ax_legend)

    add_axis_panel(fig, axis_image, axes, normal)
    add_note(fig, normal)

    fig.savefig(OUTPUT, dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig)


# =============================================================================
# MAIN
# =============================================================================

def main():
    geom = load_geometry_module()

    # Force no GUI side effects from geometry engine settings.
    geom.SHOW_LEGEND = False
    geom.SHOW_TITLE = False
    geom.SHOW_AXIS_INSET = False
    geom.SHOW_AXES = False

    normal, offset = normalize_slice(SLICE_NORMAL, SLICE_OFFSET)

    vertices4 = geom.build_vertices()
    points3, points4, basis, hull3 = geom.compute_section(
        vertices4, normal, offset
    )
    x0 = offset * normal

    print("Rendering polytope...")
    poly_image = render_polytope(
        geom, points3, hull3, vertices4, normal, offset, x0, basis
    )

    print("Rendering slice coordinate triad with the same camera...")
    axis_image, axes = render_axis_triad(normal, basis)

    print("Composing final figure in Matplotlib...")
    compose_figure(poly_image, axis_image, axes, normal, offset)

    print(f"Saved: {OUTPUT}")
    print(
        f"Final size: {int(FIGURE_SIZE_INCH[0] * DPI)} x "
        f"{int(FIGURE_SIZE_INCH[1] * DPI)} px"
    )


if __name__ == "__main__":
    main()
