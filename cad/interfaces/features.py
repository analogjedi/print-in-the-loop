"""Local +Z cylindrical axes; all inputs are explicit synthetic/design values.

These functions construct tools/envelopes, not verified purchased components.
No fit, bearing size, fastener clearance, or insertion allowance is implicit.
"""
from dataclasses import dataclass
from math import isfinite

from build123d import Align, Cylinder, Location, Vector


def positive(*values):
    if any(isinstance(v, bool) or not isfinite(v) or v <= 0 for v in values):
        raise ValueError("dimensions must be finite and positive")


@dataclass(frozen=True)
class Frame:
    id: str
    origin_mm: tuple[float, float, float] = (0, 0, 0)
    x_direction: tuple[float, float, float] = (1, 0, 0)
    z_direction: tuple[float, float, float] = (0, 0, 1)

    def __post_init__(self):
        for value in (self.origin_mm, self.x_direction, self.z_direction):
            if len(value) != 3 or not all(isfinite(v) for v in value):
                raise ValueError("frame vectors need three finite coordinates")
        x, z = Vector(self.x_direction), Vector(self.z_direction)
        if abs(x.length - 1) > 1e-9 or abs(z.length - 1) > 1e-9 or abs(x.dot(z)) > 1e-9:
            raise ValueError("frame X and Z must be orthogonal unit vectors")
        if not self.id:
            raise ValueError("frame needs a stable ID")

    def location(self):
        from build123d import Plane
        return Location(Plane(origin=self.origin_mm, x_dir=self.x_direction, z_dir=self.z_direction))


def shaft_envelope(diameter_mm, length_mm, frame):
    positive(diameter_mm, length_mm)
    return frame.location() * Cylinder(diameter_mm / 2, length_mm, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cylindrical_cut_tool(nominal_diameter_mm, depth_mm, diametral_compensation_mm, frame):
    positive(nominal_diameter_mm, depth_mm)
    if not isfinite(diametral_compensation_mm):
        raise ValueError("compensation must be finite")
    diameter = nominal_diameter_mm + diametral_compensation_mm
    positive(diameter)
    return shaft_envelope(diameter, depth_mm, frame)


def bearing_seat_tool(outer_diameter_mm, seat_depth_mm, diametral_compensation_mm, frame):
    return cylindrical_cut_tool(outer_diameter_mm, seat_depth_mm, diametral_compensation_mm, frame)


def fastener_hole_tool(nominal_diameter_mm, depth_mm, diametral_compensation_mm, frame):
    return cylindrical_cut_tool(nominal_diameter_mm, depth_mm, diametral_compensation_mm, frame)


def mounting_frames(pattern_id, positions_mm):
    if not positions_mm or len(set(positions_mm)) != len(positions_mm):
        raise ValueError("mounting positions must be nonempty and unique")
    return [Frame(f"{pattern_id}_{index:02d}", position) for index, position in enumerate(positions_mm)]
