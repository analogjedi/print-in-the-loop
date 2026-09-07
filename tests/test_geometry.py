from pathlib import Path

from build123d import Align, Box, Compound, Pos
import pytest

from cad.interfaces.features import Frame, bearing_seat_tool, fastener_hole_tool, mounting_frames, shaft_envelope
from cad.parts.smoke_test import make_smoke_part
from mech_lab.build import register_part
from mech_lab.geometry import GeometryPolicy, inspect, measure
from mech_lab.schema import Dimensions, load_yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])
DIMS = Dimensions(x_mm=10, y_mm=20, z_mm=5)


@pytest.mark.parametrize("sizes", [(10, 20, 5), (12, 18, 7), (0.5, 1.5, 2.5)])
def test_parameter_rebuild(sizes):
    dimensions = Dimensions(**dict(zip(("x_mm", "y_mm", "z_mm"), sizes)))
    assert inspect(make_smoke_part(dimensions), dimensions, POLICY)["status"] == "PASS"


@pytest.mark.parametrize("defect", ["wrong_size", "translated", "empty", "extra_solid", "removed_volume"])
def test_seeded_geometry_defects(defect):
    part = make_smoke_part(DIMS)
    if defect == "wrong_size":
        part = Box(9, 20, 5, align=(Align.MIN,) * 3)
    elif defect == "translated":
        part = Pos(1, 0, 0) * part
    elif defect == "empty":
        part = part - part
    elif defect == "extra_solid":
        part = Compound(children=[part, Pos(30, 0, 0) * Box(1, 1, 1)])
    elif defect == "removed_volume":
        part = part - Pos(5, 10, 2.5) * Box(1, 1, 10)
    try:
        result = inspect(part, DIMS, POLICY)
    except ValueError:
        assert defect == "empty"
    else:
        assert result["status"] == "FAIL"


def test_duplicate_part_identity():
    registry = {}
    register_part(registry, "part", make_smoke_part(DIMS))
    with pytest.raises(ValueError, match="duplicate"):
        register_part(registry, "part", make_smoke_part(DIMS))


def test_interfaces_use_explicit_compensation_and_frames():
    frame = Frame("synthetic_axis", (2, 3, 4))
    shaft = shaft_envelope(4, 6, frame)
    hole = fastener_hole_tool(4, 6, 0.4, frame)
    seat = bearing_seat_tool(8, 2, -0.1, frame)
    assert measure(shaft)["dimensions_mm"] == pytest.approx([4, 4, 6])
    assert measure(hole)["dimensions_mm"] == pytest.approx([4.4, 4.4, 6])
    assert measure(seat)["dimensions_mm"] == pytest.approx([7.9, 7.9, 2])
    assert measure(shaft)["minimum_mm"] == pytest.approx([0, 1, 4])
    rotated = shaft_envelope(4, 6, Frame("along_y", z_direction=(0, 1, 0)))
    assert measure(rotated)["dimensions_mm"] == pytest.approx([4, 6, 4])


def test_invalid_interfaces():
    with pytest.raises(ValueError):
        Frame("bad", x_direction=(0, 0, 1))
    with pytest.raises(ValueError):
        bearing_seat_tool(8, 2, -9, Frame("test"))
    with pytest.raises(ValueError):
        mounting_frames("mount", [(0, 0, 0), (0, 0, 0)])
