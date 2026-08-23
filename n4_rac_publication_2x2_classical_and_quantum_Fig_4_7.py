"""
Publication-quality 2x2 comparison of n=4 RAC BIAS-space cross-sections.

PyVista renders each 3D slice; Matplotlib composes the four panels and one
shared vertex legend. Each slice uses a sparse, orthogonal, oriented integer
basis in the original 4D advantage coordinates, labelled on the black axes.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from scipy.spatial import ConvexHull

BASE_SCRIPT = Path(__file__).with_name("n4_rac_cross_section_axis_inset_planar_edges.py")
OUTPUT = Path(__file__).with_name("Figure_4.png")
QUANTUM_OUTPUT = Path(__file__).with_name("Figure_7.png")

# Four slices to compare. Change these freely.
SLICES = [
    ("A", np.array([1., 0., 0., 0.]), 0.0),       # c1 = 0
    ("B", np.array([1., -1., 0., 0.]), 0.0),      # c1 = c2
    ("C", np.array([1., 1., 0., 0.]), 0.0),       # c1 = -c2
    ("D", np.array([1., 1., 1., 1.]), 0.0),       # c1+c2+c3+c4 = 0
]

FIGURE_SIZE_INCH = (15.36, 11.2)
DPI = 200
PANEL_RENDER_SIZE = (1200, 1050)
CAMERA_POSITION = (3.0, 2.0, 1.0)
CAMERA_FOCAL_POINT = (0., 0., 0.)
CAMERA_UP = (0., 0., 1.)
CAMERA_ZOOM = 1.02
PARALLEL_PROJECTION = False
OBJECT_COLOR = "lightblue"
OBJECT_OPACITY = 0.92
QUANTUM_SPHERE_COLOR = "lightblue"
QUANTUM_SPHERE_OPACITY = 0.55
QUANTUM_SPHERE_RESOLUTION = 160

# Quantum sphere coordinate guides.
SHOW_QUANTUM_GUIDES = True
QUANTUM_GUIDE_COLOR = "gray"
QUANTUM_GUIDE_WIDTH = 1.2
QUANTUM_GUIDE_OPACITY = 0.65
QUANTUM_GUIDE_RESOLUTION = 240

# Mark the six ±axis intersections with the sphere.
SHOW_QUANTUM_AXIS_DOTS = True
QUANTUM_AXIS_DOT_COLOR = "black"
QUANTUM_AXIS_DOT_SIZE = 11

# Keep the quantum axes only slightly outside the unit sphere.
QUANTUM_AXIS_LENGTH = 1.08
EDGE_COLOR = "black"
EDGE_WIDTH = 1.6
VERTEX_SIZE = 19
SHOW_MAIN_AXES = True
MAIN_AXIS_LENGTH = 1.25
MAIN_AXIS_WIDTH = 1.35
MAIN_AXIS_LABEL_SCALE = 1.01
MAIN_AXIS_LABEL_FONT_SIZE = 15
SHOW_AXIS_DIRECTION_LABELS = True
KEY_LIGHT_POSITION = (4., 3., 5.)
FILL_LIGHT_POSITION = (-3., -2., 2.)
AXIS_COLORS = ("crimson", "green", "royalblue", "purple")
VERTEX_COLORS = {
    "axis type (1,0,0,0)": "crimson",
    "3/4 + 1/4 type": "royalblue",
    "1/2 + 1/2 + 1/2 type": "darkorange",
}
# Per-axis text offsets: (right/left, up/down)
LABEL_OFFSETS = [
    (   -0.18,  0.0),   # left axis: move left + up
    ( 0.00,  -0.02),   # right axis: move right + up
    ( -0.08,  0.0),   # top axis: move up
]

def load_geometry_module():
    if not BASE_SCRIPT.exists():
        raise FileNotFoundError(f"Geometry script not found: {BASE_SCRIPT}")
    spec = importlib.util.spec_from_file_location("rac_geom", BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_slice(normal, offset):
    normal = np.asarray(normal, dtype=float)
    n = np.linalg.norm(normal)
    if n == 0:
        raise ValueError("Slice normal cannot be zero")
    return normal/n, float(offset)/n


def apply_camera(plotter):
    plotter.camera.position = CAMERA_POSITION
    plotter.camera.focal_point = CAMERA_FOCAL_POINT
    plotter.camera.up = CAMERA_UP
    if PARALLEL_PROJECTION:
        plotter.enable_parallel_projection()
    else:
        plotter.disable_parallel_projection()
    plotter.camera.zoom(CAMERA_ZOOM)


def apply_lighting(plotter):
    plotter.remove_all_lights()
    plotter.add_light(pv.Light(position=KEY_LIGHT_POSITION,
                               focal_point=CAMERA_FOCAL_POINT, intensity=1.0))
    plotter.add_light(pv.Light(position=FILL_LIGHT_POSITION,
                               focal_point=CAMERA_FOCAL_POINT, intensity=0.38))


def rgba_crop(image, pad=18):
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 4:
        return image
    ys, xs = np.where(image[:, :, 3] > 2)
    if not len(xs):
        return image
    return image[max(0,ys.min()-pad):min(image.shape[0],ys.max()+pad+1),
                 max(0,xs.min()-pad):min(image.shape[1],xs.max()+pad+1)]


def slice_label(normal, offset):
    # Use the unnormalised normal for human-readable integer relations.
    n = np.asarray(normal, dtype=float)
    nz = np.flatnonzero(np.abs(n) > 1e-9)
    if len(nz) == 1:
        i = int(nz[0]); return rf"$c_{i+1}={offset/n[i]:g}$"
    if abs(offset) < 1e-9 and len(nz) == 2:
        i, j = map(int, nz)
        if np.isclose(n[i], -n[j]): return rf"$c_{i+1}=c_{j+1}$"
        if np.isclose(n[i], n[j]): return rf"$c_{i+1}=-c_{j+1}$"
    terms = []
    for i, a in enumerate(n):
        if abs(a) < 1e-9: continue
        sign = "+" if a > 0 and terms else ""
        coeff = "" if np.isclose(abs(a),1) else f"{abs(a):g}"
        if a < 0: sign = "-"
        terms.append(f"{sign}{coeff}c_{i+1}")
    return "$" + "".join(terms) + rf"={offset:g}$"



def _primitive_integer_vector(v):
    """Reduce an integer vector without reversing its orientation."""
    v = np.asarray(v, dtype=np.int64)
    nz = np.abs(v[v != 0])
    if len(nz) == 0:
        raise ValueError("Cannot reduce the zero vector.")
    g = int(nz[0])
    for value in nz[1:]:
        g = int(np.gcd(g, int(value)))
    return v // g


def _orient_at_construction(v):
    """
    Choose orientation once, while constructing the basis.

    The first nonzero component is chosen positive. From then on the exact
    same oriented vector is used for projection, drawing and labelling.
    """
    v = np.asarray(v, dtype=np.int64)
    nz = np.flatnonzero(v)
    if len(nz) and v[nz[0]] < 0:
        v = -v
    return v


def integer_slice_normal(raw_normal, max_denominator=64):
    """Convert a simple rational slice normal to a primitive integer tuple."""
    from fractions import Fraction
    from math import gcd, lcm

    vals = [
        Fraction(float(x)).limit_denominator(max_denominator)
        for x in np.asarray(raw_normal, dtype=float)
    ]

    denom = 1
    for f in vals:
        denom = lcm(denom, f.denominator)

    ints = np.array(
        [int(f.numerator * (denom // f.denominator)) for f in vals],
        dtype=np.int64,
    )

    nz = np.abs(ints[ints != 0])
    if len(nz) == 0:
        raise ValueError("Slice normal cannot be zero.")

    g = int(nz[0])
    for value in nz[1:]:
        g = gcd(g, int(value))

    return ints // g


def sparse_oriented_basis_4d(raw_normal):
    """
    Construct three sparse, mutually orthogonal integer directions spanning
    raw_normal · c = 0.

    Zero entries of the normal give ordinary unit axes. Among nonzero entries
    we use a sparse Helmert-type construction. The resulting vectors are
    reduced to primitive integers and their orientation is fixed before any
    rendering is done.
    """
    n = integer_slice_normal(raw_normal)
    active = [int(i) for i in np.flatnonzero(n)]
    zero = [i for i in range(4) if n[i] == 0]

    vectors = []

    if len(active) >= 2:
        previous = [active[0]]
        for j in active[1:]:
            v = np.zeros(4, dtype=np.int64)
            s = 0
            for i in previous:
                v[i] = n[i] * n[j]
                s += int(n[i]) ** 2
            v[j] = -s
            v = _orient_at_construction(_primitive_integer_vector(v))
            vectors.append(v)
            previous.append(j)

    for j in zero:
        v = np.zeros(4, dtype=np.int64)
        v[j] = 1
        vectors.append(v)

    if len(vectors) != 3:
        raise RuntimeError(
            f"Expected three slice axes, got {len(vectors)} for normal {tuple(n)}."
        )

    for v in vectors:
        if int(np.dot(n, v)) != 0:
            raise RuntimeError(f"{v} is not perpendicular to slice normal {n}.")

    for i in range(3):
        for j in range(i + 1, 3):
            if int(np.dot(vectors[i], vectors[j])) != 0:
                raise RuntimeError(
                    f"Basis vectors {vectors[i]} and {vectors[j]} are not orthogonal."
                )

    return vectors


def normalized_basis_matrix(vectors4):
    """
    4x3 orthonormal projection matrix.

    Integer directions keep their orientation; normalization is only internal
    so all three plotted coordinates use the same metric scale.
    """
    return np.column_stack([
        np.asarray(v, dtype=float) / np.linalg.norm(v)
        for v in vectors4
    ])


def format_direction(v):
    return "(" + ",".join(str(int(x)) for x in v) + ")"



def add_oriented_axes(p, axis_vectors4, axis_length=MAIN_AXIS_LENGTH):
    """Draw the same three oriented slice axes used in both figures."""
    if not SHOW_MAIN_AXES:
        return

    for axis_index, (d3, v4) in enumerate(zip(np.eye(3), axis_vectors4)):
        end = d3 * axis_length

        p.add_mesh(
            pv.Line((0, 0, 0), end),
            color="black",
            line_width=MAIN_AXIS_WIDTH,
            lighting=False,
        )

        if SHOW_AXIS_DIRECTION_LABELS:
            label_pos = d3 * (axis_length * MAIN_AXIS_LABEL_SCALE)

            camera_pos = np.asarray(p.camera.position, dtype=float)
            camera_focal = np.asarray(p.camera.focal_point, dtype=float)
            camera_up = np.asarray(p.camera.up, dtype=float)

            view = camera_focal - camera_pos
            view /= np.linalg.norm(view)

            screen_right = np.cross(view, camera_up)
            screen_right /= np.linalg.norm(screen_right)

            screen_up = np.cross(screen_right, view)
            screen_up /= np.linalg.norm(screen_up)

            dx, dy = LABEL_OFFSETS[axis_index]
            label_pos = label_pos + dx * screen_right + dy * screen_up

            p.add_point_labels(
                np.asarray([label_pos]),
                [format_direction(v4)],
                point_size=0,
                font_size=MAIN_AXIS_LABEL_FONT_SIZE,
                bold=False,
                show_points=False,
                always_visible=True,
                shape=None,
                text_color="black",
            )


def render_panel(geom, vertices4, raw_normal, raw_offset):
    """
    Render a slice using three sparse oriented 4D basis directions.

    The labels are the exact integer directions used for the projection.
    """
    normal, offset = normalize_slice(raw_normal, raw_offset)

    # Find the true section vertices in 4D first.
    _, points4, _, _ = geom.compute_section(vertices4, normal, offset)
    x0 = offset * normal

    # Define the slice's three plotted axes in the original 4D coordinates.
    axis_vectors4 = sparse_oriented_basis_4d(raw_normal)
    basis = normalized_basis_matrix(axis_vectors4)

    # Reproject the same 4D section through this basis.
    points3 = geom.to_slice_coordinates(points4, x0, basis)
    hull3 = ConvexHull(points3)
    mesh = geom.make_mesh(points3, hull3)

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

    old = (geom.EDGE_COLOR, geom.EDGE_WIDTH, geom.SHOW_EDGES)
    geom.EDGE_COLOR, geom.EDGE_WIDTH, geom.SHOW_EDGES = EDGE_COLOR, EDGE_WIDTH, True
    geom.add_feature_edges(p, points3, hull3)
    geom.EDGE_COLOR, geom.EDGE_WIDTH, geom.SHOW_EDGES = old

    old_size = geom.ORIGINAL_VERTEX_SIZE
    old_colors = dict(geom.VERTEX_TYPE_COLORS)
    geom.ORIGINAL_VERTEX_SIZE = VERTEX_SIZE
    geom.VERTEX_TYPE_COLORS.update(VERTEX_COLORS)
    geom.add_original_vertices(p, vertices4, normal, offset, x0, basis)
    geom.ORIGINAL_VERTEX_SIZE = old_size
    geom.VERTEX_TYPE_COLORS.clear()
    geom.VERTEX_TYPE_COLORS.update(old_colors)

    add_oriented_axes(p, axis_vectors4)

    print(
        "    oriented slice axes:",
        ", ".join(format_direction(v) for v in axis_vectors4),
    )

    apply_camera(p)
    p.render()
    img = p.screenshot(return_img=True, transparent_background=True)
    p.close()
    return rgba_crop(img, 34)




def closed_polyline(points):
    """Create one closed PyVista polyline through the supplied 3D points."""
    points = np.asarray(points, dtype=float)

    # Repeat the first point so the final segment closes the circle.
    closed = np.vstack([points, points[0]])
    n = len(closed)

    poly = pv.PolyData(closed)
    poly.lines = np.hstack(([n], np.arange(n, dtype=np.int64)))
    return poly


def add_quantum_sphere_guides(p, radius):
    """
    Draw the three mutually orthogonal great circles of the rendered sphere.

    In the sparse orthonormal slice basis these are simply:
      xy plane  -> equator
      xz plane  -> pole-to-pole circle
      yz plane  -> pole-to-pole circle
    """
    if radius <= 0:
        return

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        QUANTUM_GUIDE_RESOLUTION,
        endpoint=False,
    )
    c = radius * np.cos(theta)
    s = radius * np.sin(theta)
    z = np.zeros_like(theta)

    circles = (
        np.column_stack([c, s, z]),  # xy
        np.column_stack([c, z, s]),  # xz
        np.column_stack([z, c, s]),  # yz
    )

    if SHOW_QUANTUM_GUIDES:
        for points in circles:
            p.add_mesh(
                closed_polyline(points),
                color=QUANTUM_GUIDE_COLOR,
                line_width=QUANTUM_GUIDE_WIDTH,
                opacity=QUANTUM_GUIDE_OPACITY,
                lighting=False,
            )

    if SHOW_QUANTUM_AXIS_DOTS:
        # The three axes cross a centred sphere at ±r e_i.
        dots = radius * np.vstack([
            np.eye(3),
            -np.eye(3),
        ])

        p.add_mesh(
            pv.PolyData(dots),
            color=QUANTUM_AXIS_DOT_COLOR,
            point_size=QUANTUM_AXIS_DOT_SIZE,
            render_points_as_spheres=True,
            lighting=False,
        )


def render_quantum_panel(raw_normal, raw_offset):
    """Render the matching 3D section of the 4D quantum unit hypersphere."""
    normal, offset = normalize_slice(raw_normal, raw_offset)

    if abs(offset) > 1.0 + 1e-10:
        raise ValueError("Slice does not intersect the quantum unit hypersphere.")

    axis_vectors4 = sparse_oriented_basis_4d(raw_normal)
    radius = np.sqrt(max(0.0, 1.0 - offset**2))

    p = pv.Plotter(off_screen=True, window_size=PANEL_RENDER_SIZE)
    p.set_background("white")
    p.image_transparent_background = True
    apply_lighting(p)

    sphere = pv.Sphere(
        radius=radius,
        center=(0.0, 0.0, 0.0),
        theta_resolution=QUANTUM_SPHERE_RESOLUTION,
        phi_resolution=QUANTUM_SPHERE_RESOLUTION,
    )

    p.add_mesh(
        sphere,
        color=QUANTUM_SPHERE_COLOR,
        opacity=QUANTUM_SPHERE_OPACITY,
        smooth_shading=True,
        show_edges=False,
    )

    # Great circles and the ±axis/sphere intersection points make the
    # orientation of the 3D section easier to read.
    add_quantum_sphere_guides(p, radius)

    add_oriented_axes(
        p,
        axis_vectors4,
        axis_length=QUANTUM_AXIS_LENGTH,
    )

    apply_camera(p)
    p.render()
    img = p.screenshot(return_img=True, transparent_background=True)
    p.close()
    return rgba_crop(img, 34)


def compose_quantum(images):
    fig = plt.figure(figsize=FIGURE_SIZE_INCH, dpi=DPI, facecolor="white")

    fig.text(
        .035, .965,
        "n=4 quantum cross-sections",
        fontsize=22, fontweight="bold",
        ha="left", va="top",
    )
    fig.text(
        .035, .928,
        "Different 3D cuts through the same 4D quantum hypersphere",
        fontsize=14.5,
        ha="left", va="top",
    )

    boxes = [
        [.035, .505, .455, .385],
        [.51,  .505, .455, .385],
        [.035, .085, .455, .385],
        [.51,  .085, .455, .385],
    ]

    for (letter, normal, offset), image, box in zip(SLICES, images, boxes):
        ax = fig.add_axes(box)
        ax.imshow(image)
        ax.set_axis_off()

        ax.text(
            .015, 1.015, f"{letter}  ",
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=14, fontweight="bold",
        )
        ax.text(
            .09, 1.015, slice_label(normal, offset),
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=14,
        )

    fig.savefig(QUANTUM_OUTPUT, dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig)


def add_shared_legend(fig):
    # One compact horizontal legend across the bottom.
    ax = fig.add_axes([0.08, 0.025, 0.84, 0.075]); ax.set_axis_off()
    entries = [
        ("crimson", r"Axis type $(1,0,0,0)$ and permutations"),
        ("royalblue", r"$3/4+1/4$ type $(0.75,0.25,0.25,0.25)$"),
        ("darkorange", r"$1/2+1/2+1/2$ type $(0.5,0.5,0.5,0)$"),
    ]
    xs = [0.04, 0.36, 0.69]
    for x, (color, label) in zip(xs, entries):
        ax.scatter([x], [.48], s=155, c=[color], edgecolors="black", linewidths=.7,
                   transform=ax.transAxes)
        ax.text(x+.025, .48, label, color=color, fontsize=11.2, va="center",
                transform=ax.transAxes)


def compose(images):
    fig = plt.figure(figsize=FIGURE_SIZE_INCH, dpi=DPI, facecolor="white")
    fig.text(.035, .965, "n=4 cross-sections", fontsize=22,
             fontweight="bold", ha="left", va="top")
    fig.text(.035, .928,
             "Different 3D cuts through the same 4D classical polytope",
             fontsize=14.5, ha="left", va="top")

    # generous panels; legend gets its own bottom strip
    boxes = [[.035,.485,.455,.385], [.51,.485,.455,.385],
             [.035,.085,.455,.385], [.51,.085,.455,.385]]

    for (letter, normal, offset), image, box in zip(SLICES, images, boxes):
        ax = fig.add_axes(box); ax.imshow(image); ax.set_axis_off()
        # Panel labels live in Matplotlib, so they remain crisp and consistent.
        ax.text(.015, 1.015, f"{letter}  ", transform=ax.transAxes, ha="left", va="top",
                fontsize=14, fontweight="bold")
        ax.text(.09, 1.015, slice_label(normal, offset), transform=ax.transAxes,
                ha="left", va="top", fontsize=14)

    add_shared_legend(fig)
    fig.savefig(OUTPUT, dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig)


def main():
    geom = load_geometry_module()
    geom.SHOW_LEGEND = geom.SHOW_TITLE = geom.SHOW_AXIS_INSET = geom.SHOW_AXES = False
    vertices4 = geom.build_vertices()

    classical_images = []
    for letter, normal, offset in SLICES:
        print(f"Rendering classical {letter}: normal={tuple(normal)}, offset={offset:g}")
        classical_images.append(render_panel(geom, vertices4, normal, offset))
    compose(classical_images)
    print(f"Saved classical figure: {OUTPUT}")

    quantum_images = []
    for letter, normal, offset in SLICES:
        print(f"Rendering quantum {letter}: normal={tuple(normal)}, offset={offset:g}")
        quantum_images.append(render_quantum_panel(normal, offset))
    compose_quantum(quantum_images)
    print(f"Saved quantum figure: {QUANTUM_OUTPUT}")

    print(
        f"Final size of each figure: "
        f"{int(FIGURE_SIZE_INCH[0]*DPI)} x "
        f"{int(FIGURE_SIZE_INCH[1]*DPI)} px"
    )


if __name__ == "__main__":
    main()
