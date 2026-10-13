from pathlib import Path

import pytest
from pydantic import ValidationError

from cad.assemblies import bldc_winch as winch
from mech_lab.geometry import GeometryPolicy
from mech_lab.schema import BldcWinchSpec, load_spec, load_yaml, readiness
from mech_lab.winch_build import (context, drive_checks, inspect_winch, path_checks, review_group,
                                  rotating_checks)

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])
SPEC_PATH = ROOT / "specs/bldc_4015_winch_v1.yaml"


@pytest.fixture(scope="module")
def spec():
    return load_spec(SPEC_PATH)


@pytest.fixture(scope="module")
def ss(spec):
    return load_spec(ROOT / spec.stand_spec)


@pytest.fixture(scope="module")
def printed(spec, ss):
    return winch.make_printed(spec, ss)


def failed(checks):
    return {c["check_id"] for c in checks if c["status"] == "FAIL"}


def variant(**updates):
    return BldcWinchSpec.model_validate({**load_yaml(SPEC_PATH), **updates})


def test_winch_passes_all_checks(spec, ss, printed):
    report = inspect_winch(printed, spec, ss, POLICY)
    assert report["status"] == "PASS", failed(report["checks"])
    assert spec.ratio == 9.0
    assert not readiness(spec, "build")
    assert readiness(spec, "release")


def test_tooth_phase_error_is_detected(spec, ss, printed):
    ctx = context(printed, spec, ss, POLICY)
    # A quarter of a 78T pitch puts tooth tips into tooth tips on the first stage.
    assert "mesh_stage1.full_tooth_period" in failed(drive_checks(ctx, phase_error_deg=360 / 78 / 4))


def test_column_inside_drum_sweep_is_detected(ss):
    s = variant(column_positions_mm=[[-8.0, 40.0], [-8.0, -40.0], [95.0, -20.0], [70.0, 45.0]])
    ctx = context(winch.make_printed(s, ss), s, ss, POLICY)
    assert "rotating.drum.clear_of_winch_frame_by_1mm" in failed(rotating_checks(ctx))


def test_pulley_too_close_puts_weight_over_the_base(ss):
    s = variant(pulley_x_mm=72.0)
    ctx = context(winch.make_printed(s, ss), s, ss, POLICY)
    bad = failed(path_checks(ctx))
    assert "weight_travel.beyond_base_edge" in bad
    assert "weight_travel.clear_of_all_parts" in bad


def test_rotating_parts_stay_inside_their_envelopes(spec, ss, printed):
    # Enlarging the rotor gear past its envelope must be caught, or the sweep checks prove nothing.
    bigger = dict(printed)
    bigger["rotor_gear"] = printed["rotor_gear"] + winch.cyl(16.0, 27.0, 29.0)
    ctx = context(bigger, spec, ss, POLICY)
    assert "rotor_gear.inside_rotation_envelope" in failed(rotating_checks(ctx))


def test_viewer_groups():
    printed = {"rotor_gear": None, "winch_frame": None}
    assert review_group("rotor_gear", printed) == "printed"
    assert review_group("motor_plate", printed) == "stand"
    assert review_group("motor_rotor_reference", printed) == "motor"
    assert review_group("bearing_625_a_lower", printed) == "hardware"
    assert review_group("m5x20_pulley_bolt", printed) == "hardware"
    assert review_group("weight_lowest", printed) == "load"


def test_drive_kinematics(spec):
    rates = winch.rotation_groups(spec)
    assert rates["shaft_a"]["rate"] == pytest.approx(-1 / 3)
    assert rates["shaft_b"]["rate"] == pytest.approx(1 / 9)
    c = winch.centers(spec)
    assert c["cd1"] == 52.0 and c["cd2"] == 46.0


@pytest.mark.parametrize("updates", [
    {"stage2_pinion_teeth": 24},                 # 8.625:1, not the required 9:1
    {"rotor_gear_teeth": 24, "stage1_gear_teeth": 72},  # counterbores break into the tooth roots
    {"rotor_screw_engagement_mm": 3.5},          # deeper than the rotor threads
    {"drop_mm": 230.0},                          # needs more than one output turn
    {"m5_bolt_length_mm": 16.0},                 # too short for fork plus nut
    {"spacer_outer_diameter_mm": 12.0},          # output spacer brushes the 78T tips
    {"magnet_holder_diameter_mm": 7.0},          # magnet pocket wall too thin
    {"set_screw_length_mm": 6.0},                # set screw would pass through the nut
    {"deck_screw_length_mm": 20.0},              # bottoms in the column pilot
    {"trial_assumptions_authorized": False},
])
def test_infeasible_winch_specs_rejected(updates):
    with pytest.raises(ValidationError):
        variant(**updates)
