from pathlib import Path

from build123d import Pos, Rot
import pytest
from pydantic import ValidationError

from cad.parts.indicator_disc import make_body, make_markers
from mech_lab.disc_build import inspect_disc
from mech_lab.geometry import GeometryPolicy
from mech_lab.schema import IndicatorDiscSpec, load_spec, load_yaml, readiness

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])


@pytest.fixture(scope="module")
def spec():
    return load_spec(ROOT / "specs/indicator_disc_v1.yaml")


@pytest.fixture(scope="module")
def body(spec):
    return make_body(spec)


def failed(report):
    return {c["check_id"] for c in report["checks"] if c["status"] == "FAIL"}


def test_disc_markers_fill_pockets_at_quadrants(spec, body):
    report = inspect_disc(body, make_markers(spec), spec, POLICY)
    assert report["status"] == "PASS"
    assert not readiness(spec, "build")
    assert readiness(spec, "release")


def test_rotated_marker_set_is_detected(spec, body):
    # Markers rotated 90 degrees: every shape lands on a pocket of a different shape.
    markers = [Rot(0, 0, 90) * m for m in make_markers(spec)]
    assert {"marker_0deg_circle.position_mm", "marker_0deg_circle.no_body_overlap"} <= failed(
        inspect_disc(body, markers, spec, POLICY))


def test_proud_or_shifted_marker_is_detected(spec, body):
    markers = make_markers(spec)
    proud = [Pos(0, 0, 0.2) * markers[0], *markers[1:]]
    assert "marker_0deg_circle.flush_depth_mm" in failed(inspect_disc(body, proud, spec, POLICY))
    shifted = [*markers[:2], Pos(0.3, 0, 0) * markers[2], markers[3]]
    assert {"marker_180deg_square.position_mm", "marker_180deg_square.no_body_overlap"} <= failed(
        inspect_disc(body, shifted, spec, POLICY))


def test_missing_marker_leaves_unfilled_pocket(spec, body):
    report = inspect_disc(body, make_markers(spec)[:3], spec, POLICY)
    assert {"marker.count", "body_plus_markers.fills_disc_mm3"} <= failed(report)


@pytest.mark.parametrize("updates", [
    {"marker_shapes": ["circle", "circle", "square", "cross"]},
    {"marker_angles_deg": [0.0, 90.0, 180.0]},
    {"marker_radius_mm": 27.0},
    {"marker_radius_mm": 14.0},
    {"screw_clearance_mm": 2.4},
    {"countersink_diameter_mm": 2.8},
    {"marker_depth_mm": 3.5},
    {"trial_assumptions_authorized": False},
])
def test_infeasible_disc_specs_rejected(updates):
    data = load_yaml(ROOT / "specs/indicator_disc_v1.yaml")
    with pytest.raises(ValidationError):
        IndicatorDiscSpec.model_validate({**data, **updates})
