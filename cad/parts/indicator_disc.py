"""Rotor indicator disc: body with flush inlaid position markers for a second filament.

Assembly frame: disc bottom on the rotor face at Z=0, marker face at Z=thickness,
angles counter-clockwise from +X viewed from +Z (looking down on the rotor face).
"""
import math

from build123d import (Align, Box, Color, Cone, Cylinder, Polygon, Pos, Rot, extrude)

SHAPES = ("circle", "triangle", "square", "cross")


def shape_area(kind, size):
    """Analytic face area of one marker shape whose nominal size is `size`."""
    if kind == "circle":
        return math.pi * size * size / 4
    if kind == "triangle":
        return math.sqrt(3) / 4 * size * size
    if kind == "square":
        return size * size
    bar = size / 3
    return 2 * size * bar - bar * bar


def _profile(kind, size, depth):
    """One marker centered on the origin, extending -Z from Z=0, pointing toward +X."""
    if kind == "circle":
        return Cylinder(size / 2, depth, align=(Align.CENTER, Align.CENTER, Align.MAX))
    if kind == "square":
        return Box(size, size, depth, align=(Align.CENTER, Align.CENTER, Align.MAX))
    if kind == "cross":
        bar = size / 3
        return (Box(size, bar, depth, align=(Align.CENTER, Align.CENTER, Align.MAX))
                + Box(bar, size, depth, align=(Align.CENTER, Align.CENTER, Align.MAX)))
    # Equilateral triangle, centroid at the origin, apex pointing radially outward (+X).
    r = size / math.sqrt(3)
    points = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (0, 120, 240)]
    return extrude(Polygon(*points, align=None), amount=-depth)


def marker_centers(spec):
    return [(spec.marker_radius_mm * math.cos(math.radians(a)),
             spec.marker_radius_mm * math.sin(math.radians(a))) for a in spec.marker_angles_deg]


def make_markers(spec):
    t, size, depth = spec.thickness_mm, spec.marker_size_mm, spec.marker_depth_mm
    markers = []
    for kind, angle, (x, y) in zip(spec.marker_shapes, spec.marker_angles_deg, marker_centers(spec)):
        solid = Pos(x, y, t) * Rot(0, 0, angle) * _profile(kind, size, depth)
        solid.label = f"marker_{angle:g}deg_{kind}"
        solid.color = Color(0.05, 0.05, 0.05)
        markers.append(solid)
    return markers


def make_body(spec):
    t = spec.thickness_mm
    body = Cylinder(spec.diameter_mm / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Cylinder(spec.center_hole_mm / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole_r, sink_r = spec.screw_clearance_mm / 2, spec.countersink_diameter_mm / 2
    sink_depth = sink_r - hole_r  # 90 degree included angle
    for a in spec.screw_angles_deg:
        x = spec.screw_circle_mm / 2 * math.cos(math.radians(a))
        y = spec.screw_circle_mm / 2 * math.sin(math.radians(a))
        body -= Pos(x, y, 0) * Cylinder(hole_r, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body -= Pos(x, y, t - sink_depth) * Cone(hole_r, sink_r, sink_depth,
                                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    for marker in make_markers(spec):
        body -= marker
    body.label = "indicator_disc_body"
    body.color = Color(1.0, 0.56, 0.09)
    return body
