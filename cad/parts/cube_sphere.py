"""A sphere centered on a cube, with explicit overlap for a single solid."""
from build123d import Align, Box, Color, Pos, Sphere


def make_cube_sphere(spec):
    side, radius = spec.cube_size_mm, spec.sphere_radius_mm
    cube = Box(side, side, side, align=(Align.MIN,) * 3)
    sphere = Pos(side/2, side/2, side + radius - spec.sphere_embed_mm) * Sphere(radius)
    part = cube + sphere
    part.label = "cube_sphere"
    part.color = Color(0.18, 0.52, 0.75)
    return part
