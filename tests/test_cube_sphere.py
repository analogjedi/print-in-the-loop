from pathlib import Path
import math

from build123d import Align, Box, Pos, Sphere
import pytest
from pydantic import ValidationError

from cad.parts.cube_sphere import make_cube_sphere
from mech_lab.geometry import GeometryPolicy, inspect
from mech_lab.schema import CubeSphereSpec, load_spec, load_yaml, readiness

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])


def test_cube_sphere_is_connected_and_matches_analytic_geometry():
    spec = load_spec(ROOT / "specs/cube_sphere.yaml")
    part = make_cube_sphere(spec)
    report = inspect(part, spec, POLICY)
    assert report["status"] == "PASS"
    assert report["measurements"]["dimensions_mm"] == pytest.approx([20, 20, 35])
    assert report["measurements"]["volume_mm3"] == pytest.approx(8000 + 4*math.pi*512/3 - math.pi*(8-1/3))
    assert readiness(spec, "release")


def test_shifted_sphere_fails_even_when_envelope_and_volume_are_unchanged():
    spec = load_spec(ROOT / "specs/cube_sphere.yaml")
    defective = Box(20,20,20,align=(Align.MIN,)*3) + Pos(11,10,27)*Sphere(8)
    report = inspect(defective, spec, POLICY)
    assert report["status"] == "FAIL"
    assert next(c for c in report["checks"] if c["check_id"].endswith("sphere_center_mm"))["status"] == "FAIL"


@pytest.mark.parametrize("updates", [{"sphere_embed_mm": 0}, {"sphere_embed_mm": 8}, {"sphere_radius_mm": 11}])
def test_invalid_sphere_connections_rejected(updates):
    data = load_yaml(ROOT / "specs/cube_sphere.yaml")
    with pytest.raises(ValidationError):
        CubeSphereSpec.model_validate({**data, **updates})
