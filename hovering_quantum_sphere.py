"""
Interactive PyVista quantum sphere.

What it does:
- renders a translucent blue sphere
- adds simple latitude and longitude lines
- uses glossy lighting
- lets you rotate/zoom interactively
- press "s" to:
    1. save the current view as PNG
    2. print the current camera position
- pressing "s" again overwrites the same PNG with the latest view

Requirements:
    pip install pyvista vtk numpy
"""

from __future__ import annotations

import math
import numpy as np
import pyvista as pv


# ============================================================
# Settings
# ============================================================

RADIUS = 1.0
N_CIRCLE_POINTS = 360

SPHERE_COLOR = "#55BFFF"
GRID_COLOR = "#D6F5FF"
BACKGROUND_COLOR = "white"

OUTPUT_FILE = "hovering_quantum_sphere_final.png"

SPHERE_CENTER = np.array([0.0, 0.0, 0.0])

SPHERE_OPACITY = 0.48
GRID_OPACITY = 0.72
GRID_LINE_WIDTH = 2.5

WINDOW_SIZE = (1400, 1400)

# Initial camera position.
# You can replace this later with the camera position printed after pressing "s".
CAMERA_POSITION = [
    (3.6, -3.2, 2.2),
    (0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
]


# ============================================================
# Geometry helpers
# ============================================================

def polyline_from_points(
    points: np.ndarray,
    close: bool = True,
) -> pv.PolyData:
    """Create a PyVista polyline from ordered points."""

    pts = points.copy()

    if close:
        pts = np.vstack([pts, pts[0]])

    return pv.lines_from_points(
        pts,
        close=False,
    )


def latitude_circle(
    radius: float,
    z_relative: float,
    center: np.ndarray,
    n_points: int = 360,
) -> pv.PolyData:
    """Create an east-west latitude circle."""

    circle_radius = math.sqrt(
        max(radius**2 - z_relative**2, 0.0)
    )

    t = np.linspace(
        0.0,
        2.0 * np.pi,
        n_points,
        endpoint=False,
    )

    x = circle_radius * np.cos(t)
    y = circle_radius * np.sin(t)
    z = np.full_like(t, z_relative)

    points = np.column_stack([x, y, z])
    points += center

    return polyline_from_points(
        points,
        close=True,
    )


def longitude_circle(
    radius: float,
    azimuth_deg: float,
    center: np.ndarray,
    n_points: int = 360,
) -> pv.PolyData:
    """Create a north-south great circle."""

    t = np.linspace(
        0.0,
        2.0 * np.pi,
        n_points,
        endpoint=False,
    )

    x0 = radius * np.cos(t)
    y0 = np.zeros_like(t)
    z0 = radius * np.sin(t)

    phi = np.deg2rad(azimuth_deg)

    x = x0 * np.cos(phi) - y0 * np.sin(phi)
    y = x0 * np.sin(phi) + y0 * np.cos(phi)
    z = z0

    points = np.column_stack([x, y, z])
    points += center

    return polyline_from_points(
        points,
        close=True,
    )


def add_surface_line(
    plotter: pv.Plotter,
    line: pv.PolyData,
    width: float = GRID_LINE_WIDTH,
    opacity: float = GRID_OPACITY,
) -> None:
    """Render a simple line, not a tube."""

    plotter.add_mesh(
        line,
        color=GRID_COLOR,
        opacity=opacity,
        line_width=width,
        render_lines_as_tubes=False,
        lighting=False,
    )


# ============================================================
# Build geometry
# ============================================================

sphere = pv.Sphere(
    radius=RADIUS,
    center=SPHERE_CENTER,
    theta_resolution=240,
    phi_resolution=240,
)


latitudes = [
    latitude_circle(
        RADIUS,
        z_relative=-0.50,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
    latitude_circle(
        RADIUS,
        z_relative=0.00,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
    latitude_circle(
        RADIUS,
        z_relative=0.50,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
]


longitudes = [
    longitude_circle(
        RADIUS,
        azimuth_deg=0,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
    longitude_circle(
        RADIUS,
        azimuth_deg=60,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
    longitude_circle(
        RADIUS,
        azimuth_deg=120,
        center=SPHERE_CENTER,
        n_points=N_CIRCLE_POINTS,
    ),
]


# ============================================================
# Plotter
# ============================================================

plotter = pv.Plotter(
    off_screen=False,
    window_size=WINDOW_SIZE,
)

plotter.set_background(
    BACKGROUND_COLOR
)


# ============================================================
# Sphere
# ============================================================

plotter.add_mesh(
    sphere,
    color=SPHERE_COLOR,
    opacity=SPHERE_OPACITY,
    smooth_shading=True,
    ambient=0.18,
    diffuse=0.72,
    specular=1.0,
    specular_power=45,
)


# ============================================================
# Surface lines
# ============================================================

for latitude in latitudes:
    add_surface_line(
        plotter,
        latitude,
        width=GRID_LINE_WIDTH,
        opacity=GRID_OPACITY,
    )

for longitude in longitudes:
    add_surface_line(
        plotter,
        longitude,
        width=GRID_LINE_WIDTH,
        opacity=GRID_OPACITY,
    )


# ============================================================
# Lighting
# ============================================================

plotter.remove_all_lights()


key_light = pv.Light(
    position=(4.0, -3.0, 4.0),
    focal_point=tuple(SPHERE_CENTER),
    color="white",
    intensity=1.15,
)

plotter.add_light(
    key_light
)


fill_light = pv.Light(
    position=(-3.0, 3.0, 1.5),
    focal_point=tuple(SPHERE_CENTER),
    color="#DCEEFF",
    intensity=0.50,
)

plotter.add_light(
    fill_light
)


rim_light = pv.Light(
    position=(-2.0, -4.0, 4.5),
    focal_point=tuple(SPHERE_CENTER),
    color="#E7FAFF",
    intensity=0.35,
)

plotter.add_light(
    rim_light
)


# ============================================================
# Camera
# ============================================================

plotter.camera_position = CAMERA_POSITION
plotter.camera.zoom(1.25)


# ============================================================
# Save current interactive view
# ============================================================

def save_current_view() -> None:
    """
    Save the current interactive camera view and print
    the camera position so it can be reused later.
    """

    plotter.screenshot(
        OUTPUT_FILE
    )

    print("\nSaved current view:")
    print(f"  {OUTPUT_FILE}")

    print("\nCurrent camera position:")
    print(plotter.camera_position)

    print(
        "\nCopy the camera position above into CAMERA_POSITION "
        "if you want this exact view next time."
    )


plotter.add_key_event(
    "s",
    save_current_view,
)


# ============================================================
# Interactive window
# ============================================================

print()
print("Interactive controls:")
print("  Rotate / zoom until you like the view.")
print("  Press 's' to save the current PNG and print the camera position.")
print("  Press 's' again after changing the view to overwrite the PNG.")
print("  Close the PyVista window when finished.")
print()

plotter.show()