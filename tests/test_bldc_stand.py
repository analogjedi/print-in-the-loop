from pathlib import Path

from build123d import Align, Box, Cylinder, Pos
import pytest
from pydantic import ValidationError

from cad.assemblies import bldc_stand as stand
from mech_lab.geometry import GeometryPolicy
from mech_lab.schema import BldcStandSpec, load_spec, load_yaml, readiness
from mech_lab.stand_build import inspect_stand, review_group

ROOT = Path(__file__).resolve().parents[1]
POLICY = GeometryPolicy.model_validate(load_yaml(ROOT / "validation/release_policy.yaml")["geometry"])
MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@pytest.fixture(scope="module")
def spec():
    return load_spec(ROOT / "specs/bldc_4015_stand_v1.yaml")


@pytest.fixture(scope="module")
def parts(spec):
    return stand.make_plate(spec), stand.make_tower(spec)


def failed(report):
    return {c["check_id"] for c in report["checks"] if c["status"] == "FAIL"}


def test_stand_passes_clearance_and_interface_checks(spec, parts):
    report = inspect_stand(*parts, spec, POLICY)
    assert report["status"] == "PASS", failed(report)
    assert not readiness(spec, "build")
    assert readiness(spec, "release")


def test_thicker_floor_hits_shortest_encoder_stack(spec, parts):
    plate, tower = parts
    thick = plate + Pos(0, 0, -spec.floor_thickness_mm) * (
        Cylinder(spec.plate_diameter_mm / 2 - 10, 1.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
        - Cylinder(spec.center_opening_mm / 2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MAX)))
    assert "motor_plate.clear_of_encoder_pcb_at_3.0mm" in failed(inspect_stand(thick, tower, spec, POLICY))


def test_small_center_opening_hits_chip_side(spec, parts):
    plate, tower = parts
    ring = Pos(0, 0, -spec.floor_thickness_mm) * (Cylinder(spec.center_opening_mm / 2, 1.0, align=MIN)
                                                  - Cylinder(8.0, 1.0, align=MIN))
    assert "motor_plate.clear_of_encoder_chip_side_at_3.0mm" in failed(
        inspect_stand(plate + ring, tower, spec, POLICY))


def test_fixed_post_inside_rotor_clearance_is_detected(spec, parts):
    plate, tower = parts
    post = Pos(spec.motor_diameter_mm / 2 + 1.5, 0, spec.pocket_depth_mm) * Box(2, 2, 10, align=MIN)
    assert "motor_plate.clear_of_rotor_bell" in failed(inspect_stand(plate + post, tower, spec, POLICY))


def test_window_cut_into_base_is_detected(spec, parts):
    plate, tower = parts
    _, base_top, _ = stand.tower_z(spec)
    r_mid = spec.tower_outer_diameter_mm / 2 - spec.tower_wall_mm / 2
    notch = Pos(0, -r_mid, base_top - 4) * Box(8, 10, 4, align=MIN)
    assert "tower_base.base_intact_under_front_window" in failed(
        inspect_stand(plate, tower - notch, spec, POLICY))


def test_plate_is_a_printed_part_not_a_motor_reference():
    printable = {"motor_plate": None, "tower_base": None}
    assert review_group("motor_plate", printable) == "printed"
    assert review_group("motor_rotor_reference", printable) == "motor"
    assert review_group("as5600_board_reference", printable) == "encoder"
    assert review_group("m25_motor_screw_0_reference", printable) == "screws"


@pytest.mark.parametrize("updates", [
    {"motor_screw_length_mm": 6.0},             # 3.5 mm engagement exceeds 3 mm thread depth
    {"encoder_standoff_min_mm": 2.5},           # PCB would touch the plate floor
    {"encoder_board_max_square_mm": 56.0},      # board diagonal no longer rotates in the cavity
    {"pocket_depth_mm": 5.5},                   # pocket wall would reach the rotor bell
    {"center_opening_mm": 34.0},                # breaks into the countersinks
    {"standoff_slot_width_mm": 5.5},            # standoff hex cannot pass
    {"window_height_mm": 38.0},                 # window would reach the plate screw pilots
    {"trial_assumptions_authorized": False},
])
def test_infeasible_stand_specs_rejected(updates):
    data = load_yaml(ROOT / "specs/bldc_4015_stand_v1.yaml")
    with pytest.raises(ValidationError):
        BldcStandSpec.model_validate({**data, **updates})
