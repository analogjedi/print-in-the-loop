from pathlib import Path

from build123d import Align, Box, Cylinder, Pos
import pytest
from pydantic import ValidationError

from cad.assemblies import bldc_pinned_plate as pp
from mech_lab.geometry import GeometryPolicy
from mech_lab.plate_build import inspect_plate
from mech_lab.schema import BldcPinnedPlateSpec, load_spec, load_yaml, readiness

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])
SPEC_PATH = ROOT / "specs/bldc_2804_plate_v1.yaml"
MAX = (Align.CENTER, Align.CENTER, Align.MAX)


@pytest.fixture(scope="module")
def spec():
    return load_spec(SPEC_PATH)


@pytest.fixture(scope="module")
def ss(spec):
    return load_spec(ROOT / spec.stand_spec)


@pytest.fixture(scope="module")
def parts(spec, ss):
    return pp.make_plate(spec, ss), pp.make_tower_at(spec, ss)


def failed(plate, tower, spec, ss):
    report = inspect_plate(plate, tower, spec, ss, POLICY)
    return {c["check_id"] for c in report["checks"] if c["status"] == "FAIL"}


def variant(**updates):
    return BldcPinnedPlateSpec.model_validate({**load_yaml(SPEC_PATH), **updates})


def test_plate_passes_fit_clearance_and_interface_checks(spec, ss, parts):
    assert not failed(*parts, spec, ss)
    assert not readiness(spec, "build")
    assert readiness(spec, "release")


def test_ribs_avoid_the_lead_notch(spec):
    angles = pp.rib_angles(spec)
    assert len(angles) == 6 and spec.lead_angle_deg not in angles


def test_lead_is_counterclockwise_from_pin_seen_from_rotor(spec):
    # Drawing (stator face seen from below): hole 9 o'clock, lead 12 o'clock. Mirrored to +Z: +90 degrees.
    assert (spec.lead_angle_deg - spec.locating_hole_angle_deg) % 360 == 90.0


def test_misplaced_pin_is_detected(spec, ss, parts):
    # A pin 5 degrees off the locating hole lands on the stator face instead of in the hole.
    plate = pp.make_plate(variant(locating_hole_angle_deg=5.0), ss)
    bad = failed(plate, parts[1], spec, ss)
    assert {"motor_plate.overlap_only_at_crush_ribs", "motor_plate.pin_engages_locating_hole"} <= bad


def test_undersized_pocket_is_detected(spec, ss, parts):
    plate, tower = parts
    r = spec.motor_diameter_mm / 2
    lip = Cylinder(r + 0.5, 1.0, align=pp.MIN) - Cylinder(r - 0.4, 1.0, align=pp.MIN)
    assert "motor_plate.overlap_only_at_crush_ribs" in failed(plate + lip, tower, spec, ss)


def test_small_opening_hits_boss_and_standoffs(spec, ss, parts):
    plate, tower = parts
    ring = Pos(0, 0, 0) * (Cylinder(10.0, spec.floor_thickness_mm, align=MAX) - Cylinder(6.5, spec.floor_thickness_mm, align=MAX))
    bad = failed(plate + ring, tower, spec, ss)
    assert "motor_plate.clear_of_rotor_boss" in bad
    assert "motor_plate.passes_standoffs_on_all_four_holes_at_4.5mm" in bad


def test_blocked_lead_notch_is_detected(spec, ss, parts):
    plate, tower = parts
    plug = Pos(0, 22.0, -spec.floor_thickness_mm) * Box(8, 6, spec.floor_thickness_mm + spec.pocket_depth_mm,
                                                        align=pp.MIN)
    assert "motor_plate.lead_notch_clear" in failed(plate + plug, tower, spec, ss)


def test_thicker_floor_hits_shortest_encoder_stack(spec, ss, parts):
    plate, tower = parts
    under = Pos(0, 0, -spec.floor_thickness_mm) * (Cylinder(30.0, 1.5, align=MAX) - Cylinder(spec.center_opening_mm / 2, 1.5, align=MAX))
    assert "motor_plate.clear_of_encoder_chip_side_at_4.5mm" in failed(plate + under, tower, spec, ss)


@pytest.mark.parametrize("updates", [
    {"pocket_depth_mm": 3.5},                 # pocket wall within 1 mm of the rotating bell
    {"pin_diameter_mm": 2.0},                 # pin no longer clears the locating hole
    {"pin_height_mm": 3.8},                   # pin would bottom in the 4 mm hole
    {"center_opening_mm": 24.0},              # encoder standoffs on the Ø19 holes cannot pass
    {"center_opening_mm": 30.0},              # stator seat narrower than 2.5 mm
    {"rib_interference_mm": 0.4},             # crush ribs too tight
    {"encoder_standoff_min_mm": 4.0},         # chip side would touch the floor
    {"lead_notch_width_mm": 5.5},             # notch too tight around the lead envelope
    {"encoder_review_standoff_mm": 12.0},     # review stack outside the checked range
    {"trial_assumptions_authorized": False},
])
def test_infeasible_plate_specs_rejected(updates):
    with pytest.raises(ValidationError):
        variant(**updates)
