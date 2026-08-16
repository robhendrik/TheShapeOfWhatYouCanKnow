# Figure 1 in Blog about higher dimensional RACs"
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pyvista as pv
from scipy.spatial import ConvexHull


OUTPUT = Path(__file__).with_name("Figure_1.png")

FIGURE_SIZE_INCH = (15.36, 10.24)
DPI = 200
PANEL_RENDER_SIZE = (1450, 1250)

LEFT_IMAGE_BOX = [0.025, 0.125, 0.585, 0.73]
RIGHT_LEGEND_BOX = [0.625, 0.47, 0.35, 0.30]
RIGHT_AXIS_BOX = [0.625, 0.08, 0.35, 0.34]
NOTE_BOX = [0.025, 0.025, 0.50, 0.085]

OBJECT_COLOR = "lightblue"
OBJECT_OPACITY = 0.90
EDGE_COLOR = "black"
EDGE_WIDTH = 1.6

CAMERA_POSITION = (3.0, 2.0, 1.0)
CAMERA_FOCAL_POINT = (0.0, 0.0, 0.0)
CAMERA_UP = (0.0, 0.0, 1.0)
CAMERA_ZOOM = 1.05

KEY_LIGHT_POSITION = (4.0, 3.0, 5.0)
FILL_LIGHT_POSITION = (-3.0, -2.0, 2.0)

AXIS_LENGTH = 1.16
AXIS_WIDTH = 1.5
AXIS_COLORS = ("crimson", "green", "royalblue")

VERTEX_SIZE = 20

AXIS_VERTEX_COLOR = "crimson"
MAJORITY_VERTEX_COLOR = "darkorange"

SHOW_WINNING_DIRECTION = False
WINNING_DIRECTION_LENGTH = 0.98
WINNING_DIRECTION_WIDTH = 2.0

AXIS_LABEL_OFFSETS = [
    (-0.12, -0.01),
    ( 0.08, -0.02),
    (-0.02,  0.06),
]
AXIS_LABEL_FONT_SIZE = 15


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
ALL_VERTICES = np.vstack([AXIS_VERTICES, MAJORITY_VERTICES])


def apply_camera(plotter):
    plotter.camera.position = CAMERA_POSITION
    plotter.camera.focal_point = CAMERA_FOCAL_POINT
    plotter.camera.up = CAMERA_UP
    plotter.disable_parallel_projection()
    plotter.camera.zoom(CAMERA_ZOOM)


def apply_lighting(plotter):
    plotter.remove_all_lights()
    plotter.add_light(
        pv.Light(
            position=KEY_LIGHT_POSITION,
            focal_point=CAMERA_FOCAL_POINT,
            intensity=1.0,
        )
    )
    plotter.add_light(
        pv.Light(
            position=FILL_LIGHT_POSITION,
            focal_point=CAMERA_FOCAL_POINT,
            intensity=0.38,
        )
    )


def camera_frame(plotter):
    camera_pos = np.asarray(plotter.camera.position, dtype=float)
    focal = np.asarray(plotter.camera.focal_point, dtype=float)
    up_hint = np.asarray(plotter.camera.up, dtype=float)

    view = focal - camera_pos
    view /= np.linalg.norm(view)

    right = np.cross(view, up_hint)
    right /= np.linalg.norm(right)

    screen_up = np.cross(right, view)
    screen_up /= np.linalg.norm(screen_up)

    return right, screen_up


def make_polytope_mesh():
    hull = ConvexHull(ALL_VERTICES)
    triangles = hull.simplices.astype(np.int64)
    faces = np.column_stack(
        [np.full(len(triangles), 3, dtype=np.int64), triangles]
    ).ravel()
    return pv.PolyData(ALL_VERTICES, faces), hull


def true_edges_from_hull(hull):
    equations = np.asarray(hull.equations, dtype=float)
    normals = equations[:, :3]
    offsets = equations[:, 3]

    lengths = np.linalg.norm(normals, axis=1)
    normals = normals / lengths[:, None]
    offsets = offsets / lengths

    groups = []
    tol = 1e-8

    for tri_id, (n, d) in enumerate(zip(normals, offsets)):
        placed = False
        for group in groups:
            if np.linalg.norm(n - group["normal"]) < tol and abs(d - group["offset"]) < tol:
                group["triangles"].append(tri_id)
                placed = True
                break
        if not placed:
            groups.append({
                "normal": n.copy(),
                "offset": float(d),
                "triangles": [tri_id],
            })

    true_edges = set()

    for group in groups:
        counts = {}
        for tri_id in group["triangles"]:
            tri = hull.simplices[tri_id]
            for a, b in (
                (int(tri[0]), int(tri[1])),
                (int(tri[1]), int(tri[2])),
                (int(tri[2]), int(tri[0])),
            ):
                e = tuple(sorted((a, b)))
                counts[e] = counts.get(e, 0) + 1

        for edge, count in counts.items():
            if count == 1:
                true_edges.add(edge)

    return sorted(true_edges)


def add_true_edges(plotter, hull):
    edges = true_edges_from_hull(hull)
    lines = np.asarray([[2, i, j] for i, j in edges], dtype=np.int64).ravel()
    edge_mesh = pv.PolyData(ALL_VERTICES.copy())
    edge_mesh.lines = lines
    plotter.add_mesh(
        edge_mesh,
        color=EDGE_COLOR,
        line_width=EDGE_WIDTH,
        lighting=False,
    )


def add_coordinate_axes(plotter):
    apply_camera(plotter)
    screen_right, screen_up = camera_frame(plotter)

    for i, d in enumerate(np.eye(3)):
        end = d * AXIS_LENGTH

        plotter.add_mesh(
            pv.Line((0, 0, 0), end),
            color=AXIS_COLORS[i],
            line_width=AXIS_WIDTH,
            lighting=False,
        )

        label_pos = end.copy()
        dx, dy = AXIS_LABEL_OFFSETS[i]
        label_pos = label_pos + dx * screen_right + dy * screen_up

        plotter.add_point_labels(
            np.asarray([label_pos]),
            [f"c{i+1}"],
            point_size=0,
            font_size=AXIS_LABEL_FONT_SIZE,
            bold=True,
            show_points=False,
            always_visible=True,
            shape=None,
            text_color=AXIS_COLORS[i],
        )


def add_vertices(plotter):
    """Draw the two genuine n=3 vertex types with equal marker size."""

    # Axis type: (1,0,0) and permutations/signs.
    plotter.add_mesh(
        pv.PolyData(AXIS_VERTICES),
        color=AXIS_VERTEX_COLOR,
        point_size=VERTEX_SIZE,
        render_points_as_spheres=True,
        lighting=True,
    )

    # Majority type: (1/2,1/2,1/2) and all sign variants.
    # The positive diagonal point is intentionally NOT singled out.
    plotter.add_mesh(
        pv.PolyData(MAJORITY_VERTICES),
        color=MAJORITY_VERTEX_COLOR,
        point_size=VERTEX_SIZE,
        render_points_as_spheres=True,
        lighting=True,
    )


def add_winning_direction(plotter):
    if not SHOW_WINNING_DIRECTION:
        return

    d = np.ones(3, dtype=float)
    d /= np.linalg.norm(d)
    end = d * WINNING_DIRECTION_LENGTH

    plotter.add_mesh(
        pv.Line((0, 0, 0), end),
        color="black",
        line_width=WINNING_DIRECTION_WIDTH,
        lighting=False,
    )

    # plotter.add_point_labels(
    #     np.asarray([end + np.array([0.02, 0.02, 0.04])]),
    #     ["(1,1,1)"],
    #     point_size=0,
    #     font_size=14,
    #     bold=False,
    #     show_points=False,
    #     always_visible=True,
    #     shape=None,
    #     text_color="black",
    # )


def rgba_crop(image, pad=24):
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 4:
        return image

    ys, xs = np.where(image[:, :, 3] > 2)
    if not len(xs):
        return image

    return image[
        max(0, ys.min() - pad): min(image.shape[0], ys.max() + pad + 1),
        max(0, xs.min() - pad): min(image.shape[1], xs.max() + pad + 1),
    ]


def render_polytope():
    mesh, hull = make_polytope_mesh()

    p = pv.Plotter(off_screen=True, window_size=PANEL_RENDER_SIZE)
    p.set_background("white")
    p.image_transparent_background = True
    apply_lighting(p)

    p.add_mesh(
        mesh,
        color=OBJECT_COLOR,
        opacity=OBJECT_OPACITY,
        smooth_shading=False,
        show_edges=False,
    )

    add_true_edges(p, hull)
    add_vertices(p)
    add_coordinate_axes(p)
    add_winning_direction(p)

    apply_camera(p)
    p.render()

    image = p.screenshot(return_img=True, transparent_background=True)
    p.close()

    return rgba_crop(image, pad=34)


def rounded_box(ax, edgecolor, linewidth=1.4):
    patch = FancyBboxPatch(
        (0.01, 0.01),
        0.98,
        0.98,
        boxstyle="round,pad=0.012,rounding_size=0.035",
        transform=ax.transAxes,
        facecolor="white",
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(patch)


def add_legend(fig):
    ax = fig.add_axes(RIGHT_LEGEND_BOX)
    ax.set_axis_off()

    ax.text(
        0.02, 0.95,
        "Vertex types in advantage coordinates",
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        ha="left",
        va="top",
    )

    ax.scatter(
        [0.055], [0.64],
        s=170,
        c=[AXIS_VERTEX_COLOR],
        edgecolors="black",
        linewidths=0.8,
        transform=ax.transAxes,
    )
    ax.text(
        0.13, 0.68,
        "Axis type",
        transform=ax.transAxes,
        color=AXIS_VERTEX_COLOR,
        fontsize=13,
        fontweight="bold",
        va="center",
    )
    ax.text(
        0.13, 0.56,
        r"$(\pm1,0,0)$ and permutations",
        transform=ax.transAxes,
        fontsize=11.5,
        va="center",
    )

    ax.scatter(
        [0.055], [0.28],
        s=170,
        c=[MAJORITY_VERTEX_COLOR],
        edgecolors="black",
        linewidths=0.8,
        transform=ax.transAxes,
    )
    ax.text(
        0.13, 0.32,
        r"$1/2+1/2+1/2$ type",
        transform=ax.transAxes,
        color=MAJORITY_VERTEX_COLOR,
        fontsize=13,
        fontweight="bold",
        va="center",
    )
    ax.text(
        0.13, 0.20,
        r"$(\pm\frac{1}{2},\pm\frac{1}{2},\pm\frac{1}{2})$",
        transform=ax.transAxes,
        fontsize=11.5,
        va="center",
    )


def add_axis_box(fig):
    ax = fig.add_axes(RIGHT_AXIS_BOX)
    ax.set_axis_off()
    rounded_box(ax, edgecolor="steelblue")

    ax.text(
        0.06, 0.91,
        "Advantage axes",
        transform=ax.transAxes,
        fontsize=14.5,
        fontweight="bold",
        ha="left",
        va="top",
    )

    origin = np.array([0.43, 0.36])
    directions = [
        np.array([-0.23, -0.10]),
        np.array([ 0.28, -0.07]),
        np.array([ 0.00,  0.34]),
    ]
    labels = [
        ("c1", "(1, 0, 0)", "crimson"),
        ("c2", "(0, 1, 0)", "green"),
        ("c3", "(0, 0, 1)", "royalblue"),
    ]

    ax.scatter([origin[0]], [origin[1]], s=30, c=["black"],
               transform=ax.transAxes, zorder=3)

    for d, (name, vec, color) in zip(directions, labels):
        tip = origin + d
        ax.annotate(
            "",
            xy=tip,
            xytext=origin,
            xycoords=ax.transAxes,
            textcoords=ax.transAxes,
            arrowprops=dict(
                arrowstyle="-|>",
                lw=2.0,
                color=color,
                mutation_scale=17,
            ),
        )
        ax.text(
            tip[0] + 0.02,
            tip[1] + 0.02,
            rf"${name}$" + "\n" + vec,
            transform=ax.transAxes,
            fontsize=10.5,
            color=color,
            ha="left",
            va="bottom",
        )

    # ax.text(
    #     0.06, 0.08,
    #     r"The black diagonal in the main figure is the winning direction $(1,1,1)$.",
    #     transform=ax.transAxes,
    #     fontsize=10.8,
    #     ha="left",
    #     va="bottom",
    #     wrap=True,
    # )


def add_note_box(fig):
    ax = fig.add_axes(NOTE_BOX)
    ax.set_axis_off()
    rounded_box(ax, edgecolor="darkorange")

    ax.text(
        0.05, 0.50,
        r"The $(1,1,1)$ line marks the winning direction; the point "
        r"$(\frac{1}{2},\frac{1}{2},\frac{1}{2})$ is one of the dark-orange majority-type vertices.",
        transform=ax.transAxes,
        fontsize=11.5,
        ha="left",
        va="center",
    )


def compose(image):
    fig = plt.figure(figsize=FIGURE_SIZE_INCH, dpi=DPI, facecolor="white")

    fig.text(
        0.025, 0.955,
        "n=3 advantage-space polytope",
        fontsize=22,
        fontweight="bold",
        ha="left",
        va="top",
    )

    fig.text(
        0.025, 0.915,
        "Classical one-bit RAC geometry in three advantage coordinates",
        fontsize=14.5,
        ha="left",
        va="top",
    )

    ax_image = fig.add_axes(LEFT_IMAGE_BOX)
    ax_image.imshow(image)
    ax_image.set_axis_off()

    add_legend(fig)
    add_axis_box(fig)
    #add_note_box(fig)

    fig.savefig(OUTPUT, dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig)


def main():
    print("Rendering n=3 RAC advantage-space polytope...")
    image = render_polytope()
    compose(image)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()