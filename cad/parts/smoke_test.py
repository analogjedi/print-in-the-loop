from build123d import Align, Box


def make_smoke_part(dimensions):
    """Lower corner is the global origin; Z is the build direction."""
    part = Box(dimensions.x_mm, dimensions.y_mm, dimensions.z_mm,
               align=(Align.MIN, Align.MIN, Align.MIN))
    part.label = "smoke_block"
    return part
