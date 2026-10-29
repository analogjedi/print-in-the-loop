from pathlib import Path

import pytest
from pydantic import ValidationError

from cad.parts import rotor_dial as rd
from mech_lab.dial_build import angle_error, angle_of, inspect_dial
from mech_lab.geometry import GeometryPolicy
from mech_lab.schema import RotorDialSpec, load_spec, load_yaml, readiness

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])
SPEC_PATH = ROOT / "specs/bldc_2804_dial_v1.yaml"


@pytest.fixture(scope="module")
def spec():
    return load_spec(SPEC_PATH)


@pytest.fixture(scope="module")
def ps(spec):
    return load_spec(ROOT / spec.plate_spec)


@pytest.fixture(scope="module")
def ss(ps):
    return load_spec(ROOT / ps.stand_spec)


@pytest.fixture(scope="module")
def parts(spec, ps, ss):
    return rd.make_dial(spec, ps), rd.make_marks(spec, ps), rd.make_pointer(spec, ps, ss)


def failed(parts, spec, ps, ss):
    report = inspect_dial(*parts, spec, ps, ss, POLICY)
    return {c["check_id"] for c in report["checks"] if c["status"] == "FAIL"}


def variant(**updates):
    return RotorDialSpec.model_validate({**load_yaml(SPEC_PATH), **updates})


def test_dial_passes_scale_fit_and_clearance_checks(spec, ps, ss, parts):
    assert not failed(parts, spec, ps, ss)
    assert not readiness(spec, "build")
    assert readiness(spec, "release")


def test_scale_has_nested_ticks_and_twelve_numbers(spec, ps):
    kinds = [rd.tick_kind(spec, v) for v in rd.tick_values(spec)]
    assert (kinds.count("major"), kinds.count("mid"), kinds.count("minor")) == (12, 24, 36)
    assert [v for v in rd.label_values(spec)] == [30.0 * i for i in range(12)]


def test_numbers_run_clockwise_seen_from_above(spec, ps, parts):
    labels = {m.label: m for m in parts[1] if m.label.startswith("label_")}
    a0, _ = angle_of(labels["label_0deg"])
    a30, _ = angle_of(labels["label_30deg"])
    assert angle_error(a0, spec.zero_angle_deg) <= 2.0
    assert angle_error(a30, spec.zero_angle_deg - 30.0) <= 2.0  # clockwise = decreasing math angle


def test_reversed_scale_is_detected(spec, ps, ss, parts):
    ccw = variant(scale_direction="counterclockwise")
    bad = failed((rd.make_dial(ccw, ps), rd.make_marks(ccw, ps), parts[2]), spec, ps, ss)
    assert "label_30deg.angle_deg" in bad and "tick_5deg_minor.angle_deg" in bad
    assert "label_0deg.angle_deg" not in bad


def test_oversized_dial_hits_pointer(spec, ps, ss, parts):
    big = variant(dial_diameter_mm=114.0)
    bad = failed((rd.make_dial(big, ps), rd.make_marks(big, ps), parts[2]), spec, ps, ss)
    assert {"dial.envelope_mm", "dial_pointer.reading_gap_mm"} <= bad


def test_pointer_without_rim_hook_is_detected(spec, ps, ss, parts):
    loose = rd.make_pointer(variant(pointer_lip_clearance_mm=1.0), ps, ss)
    assert "dial_pointer.lip_hooks_rim" in failed((parts[0], parts[1], loose), spec, ps, ss)


def test_numbers_crowding_ticks_are_detected(ps, ss, parts):
    crowded = variant(label_radius_mm=46.5)
    bad = failed((rd.make_dial(crowded, ps), rd.make_marks(crowded, ps), parts[2]), crowded, ps, ss)
    assert any(c.endswith("clear_of_ticks_mm") for c in bad)


@pytest.mark.parametrize("updates", [
    {"dial_screw_length_mm": 6.0},            # 3.5 mm into a 3 mm rotor thread
    {"dial_screw_length_mm": 3.5},            # 1 mm engagement
    {"dial_thickness_mm": 2.8},               # hub over the rotor under 2 mm
    {"inlay_depth_mm": 1.6},                  # less than 1 mm white under the scale
    {"minor_tick_width_mm": 0.4},             # below the minimum printable feature
    {"mid_tick_step_deg": 7.0},               # steps do not nest
    {"minor_tick_step_deg": 7.0},             # does not divide 360
    {"minor_tick_step_deg": 1.0, "mid_tick_step_deg": 5.0},  # ticks merge at the rim
    {"pointer_counterbore_mm": 5.6},          # M3 head cannot drop in
    {"pointer_gap_to_dial_mm": 0.5},          # pointer rubs the turning rim
    {"trial_assumptions_authorized": False},
])
def test_infeasible_dial_specs_rejected(updates):
    with pytest.raises(ValidationError):
        variant(**updates)
