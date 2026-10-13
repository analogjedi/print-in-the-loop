"""Strict specification contracts. Unknown engineering values remain None."""
from __future__ import annotations

from datetime import date
import math
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

Positive = Annotated[float, Field(gt=0, allow_inf_nan=False, strict=True)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)]
Finite = Annotated[float, Field(allow_inf_nan=False, strict=True)]
Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", max_length=80)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Dimensions(Model):
    x_mm: Positive
    y_mm: Positive
    z_mm: Positive


class Assumption(Model):
    id: Identifier
    statement: Annotated[str, Field(min_length=1)]
    approval_state: Literal["proposed", "approved", "rejected"]
    approved_by: str | None
    approval_date: date | None

    @model_validator(mode="after")
    def approval_consistency(self):
        if self.approval_state == "approved":
            if not self.approved_by or not self.approved_by.strip() or not self.approval_date:
                raise ValueError("approved assumptions need reviewer and approval date")
        elif self.approved_by is not None or self.approval_date is not None:
            raise ValueError("unapproved assumptions cannot carry approval metadata")
        return self


class Requirements(Model):
    external_envelope_mm: Dimensions | None
    joint_range_deg: list[Finite] | None
    continuous_torque_nm: Nonnegative | None
    peak_torque_nm: Nonnegative | None
    output_speed_rpm: Nonnegative | None
    backlash_limit_deg: Nonnegative | None
    maximum_mass_g: Positive | None

    @model_validator(mode="after")
    def consistent(self):
        if self.joint_range_deg is not None:
            if len(self.joint_range_deg) != 2 or self.joint_range_deg[0] >= self.joint_range_deg[1]:
                raise ValueError("joint_range_deg needs two increasing finite angles")
        if self.continuous_torque_nm is not None and self.peak_torque_nm is not None:
            if self.peak_torque_nm < self.continuous_torque_nm:
                raise ValueError("peak torque cannot be less than continuous torque")
        return self


class Mechanism(Model):
    drive_type: Literal["manual", "motor", "tendon"]
    bearing_support: Literal["paired"]
    removable_cover: Literal[True]
    mechanical_stops: Literal[True]


class Components(Model):
    shaft: Identifier | None
    bearings: list[Identifier]
    fasteners: list[Identifier]
    magnet: Identifier | None
    sensor_pcb: Identifier | None


class Manufacturing(Model):
    printer_id: Identifier
    machine_profile_id: Identifier | None
    nozzle_diameter_mm: Positive | None
    material_profile_id: Identifier | None
    fit_calibration_id: Identifier | None


class ReleaseControls(Model):
    human_design_review_required: Literal[True]
    human_print_approval_required: Literal[True]
    human_powered_test_approval_required: Literal[True]


class SmokeSpec(Model):
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["smoke_test"]
    release_class: Literal["toolchain_smoke_test"]
    length_unit: Literal["mm"]
    dimensions: Dimensions


class CubeSphereSpec(Model):
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["cube_sphere"]
    release_class: Literal["toolchain_smoke_test"]
    length_unit: Literal["mm"]
    cube_size_mm: Positive
    sphere_radius_mm: Positive
    sphere_embed_mm: Positive

    @model_validator(mode="after")
    def connected_sphere(self):
        if self.sphere_radius_mm * 2 > self.cube_size_mm:
            raise ValueError("sphere diameter must fit within the cube footprint")
        if self.sphere_embed_mm >= self.sphere_radius_mm:
            raise ValueError("embed depth must be less than the sphere radius")
        return self

    @property
    def dimensions(self):
        return Dimensions(x_mm=self.cube_size_mm, y_mm=self.cube_size_mm,
                          z_mm=self.cube_size_mm + 2*self.sphere_radius_mm - self.sphere_embed_mm)


class JointSpec(Model):
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["finger_joint"]
    release_class: Literal["kinematic_demonstrator", "functional_prototype", "qualified_design"]
    length_unit: Literal["mm"]
    requirements: Requirements
    mechanism: Mechanism
    components: Components
    manufacturing: Manufacturing
    assumptions: list[Assumption]
    release_controls: ReleaseControls

    @model_validator(mode="after")
    def unique_assumptions(self):
        ids = [item.id for item in self.assumptions]
        if len(set(ids)) != len(ids):
            raise ValueError("assumption IDs must be unique")
        return self


class GearboxSpec(Model):
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["compound_gearbox"]
    release_class: Literal["kinematic_demonstrator"]
    length_unit: Literal["mm"]
    gear_count: Literal[4]
    large_teeth: Literal[60]
    pinion_teeth: Literal[20]
    module_mm: Literal[1.0]
    pressure_angle_deg: Literal[20.0]
    face_width_mm: Literal[4.0]
    axial_step_mm: Literal[5.0]
    tooth_thinning_mm: Positive
    shaft_diameter_mm: Positive
    shaft_diametral_clearance_mm: Positive
    retainer_axial_clearance_mm: Positive
    m3_clearance_mm: Positive
    m3_tap_pilot_mm: Positive
    servo_model: Literal["Waveshare ST3215"]
    servo_step: str
    servo_step_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    trial_assumptions_authorized: Literal[True]
    process_compensation_mm: Literal[0.0]

    @model_validator(mode="after")
    def feasible_trial(self):
        if not 0 < self.tooth_thinning_mm < 0.3:
            raise ValueError("trial tooth thinning must be between 0 and 0.3 mm")
        if not 4 <= self.shaft_diameter_mm <= 5.5:
            raise ValueError("this layout supports shafts between 4 and 5.5 mm")
        if not 0.1 <= self.shaft_diametral_clearance_mm <= 0.6:
            raise ValueError("trial diametral clearance must be 0.1 to 0.6 mm")
        if not 0.1 <= self.retainer_axial_clearance_mm <= 0.5:
            raise ValueError("trial axial clearance must be 0.1 to 0.5 mm")
        if not 3.1 <= self.m3_clearance_mm <= 3.6 or not 2.3 <= self.m3_tap_pilot_mm <= 2.6:
            raise ValueError("invalid trial M3 clearance or tapping pilot")
        return self


class IndicatorDiscSpec(Model):
    """Rotor-face position indicator with inlaid second-filament markers."""
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["indicator_disc"]
    release_class: Literal["kinematic_demonstrator"]
    length_unit: Literal["mm"]
    motor_reference: Annotated[str, Field(min_length=1)]
    diameter_mm: Positive
    thickness_mm: Positive
    center_hole_mm: Positive
    screw_circle_mm: Positive
    screw_angles_deg: list[Finite]
    screw_clearance_mm: Positive
    countersink_diameter_mm: Positive
    marker_shapes: list[Literal["circle", "triangle", "square", "cross"]]
    marker_angles_deg: list[Finite]
    marker_radius_mm: Positive
    marker_size_mm: Positive
    marker_depth_mm: Positive
    trial_assumptions_authorized: Literal[True]
    process_compensation_mm: Literal[0.0]

    @model_validator(mode="after")
    def feasible_disc(self):
        if len(self.marker_shapes) != len(self.marker_angles_deg) or not self.marker_shapes:
            raise ValueError("each marker needs exactly one angle")
        if len(set(self.marker_shapes)) != len(self.marker_shapes):
            raise ValueError("marker shapes must be distinct so positions are distinguishable")
        if not 2.6 <= self.screw_clearance_mm <= 3.2:
            raise ValueError("M2.5 clearance must be 2.6 to 3.2 mm")
        if not self.screw_clearance_mm < self.countersink_diameter_mm <= 2 * self.screw_clearance_mm:
            raise ValueError("countersink must be wider than the clearance hole and at most twice it")
        sink_depth = (self.countersink_diameter_mm - self.screw_clearance_mm) / 2
        if sink_depth >= self.thickness_mm or self.marker_depth_mm >= self.thickness_mm:
            raise ValueError("countersink and marker depths must leave material")
        if self.center_hole_mm + self.countersink_diameter_mm >= self.screw_circle_mm:
            raise ValueError("countersinks would break into the center hole")
        # Largest circumscribed marker radius, so no rotation of a marker can reach the rim or countersinks.
        size = self.marker_size_mm
        reach = max({"circle": size / 2, "triangle": size / math.sqrt(3),
                     "square": size / math.sqrt(2), "cross": size / math.sqrt(2)}[k]
                    for k in self.marker_shapes)
        if self.marker_radius_mm + reach > self.diameter_mm / 2 - 1.0:
            raise ValueError("markers must stay at least 1 mm inside the rim")
        if self.marker_radius_mm - reach < (self.screw_circle_mm + self.countersink_diameter_mm) / 2 + 1.0:
            raise ValueError("markers must clear the countersinks by at least 1 mm")
        return self


class BldcStandSpec(Model):
    """Face-up desktop stand: motor-specific plate on a common tower with an encoder cavity."""
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["bldc_motor_stand"]
    release_class: Literal["kinematic_demonstrator"]
    length_unit: Literal["mm"]
    motor_reference: Annotated[str, Field(min_length=1)]
    motor_diameter_mm: Positive
    motor_body_height_mm: Positive
    motor_stationary_height_mm: Positive
    motor_boss_diameter_mm: Positive
    motor_boss_height_mm: Positive
    motor_outer_hole_circle_mm: Positive
    motor_inner_hole_circle_mm: Positive
    motor_thread_depth_mm: Positive
    pocket_diametral_clearance_mm: Positive
    pocket_depth_mm: Positive
    floor_thickness_mm: Positive
    plate_diameter_mm: Positive
    center_opening_mm: Positive
    standoff_slot_width_mm: Positive
    standoff_slot_outer_radius_mm: Positive
    cable_notch_width_mm: Positive
    cable_notch_outer_radius_mm: Positive
    m25_clearance_mm: Positive
    m25_countersink_diameter_mm: Positive
    motor_screw_length_mm: Positive
    m3_clearance_mm: Positive
    m3_tap_pilot_mm: Positive
    plate_screw_radius_mm: Positive
    plate_screw_pilot_depth_mm: Positive
    tower_outer_diameter_mm: Positive
    tower_wall_mm: Positive
    cavity_height_mm: Positive
    window_width_mm: Positive
    window_height_mm: Positive
    base_x_mm: Positive
    base_y_mm: Positive
    base_thickness_mm: Positive
    base_hole_mm: Positive
    base_hole_inset_mm: Positive
    encoder_board_max_square_mm: Positive
    encoder_standoff_min_mm: Positive
    encoder_standoff_max_mm: Positive
    encoder_pcb_thickness_mm: Positive
    encoder_chip_side_height_mm: Positive
    encoder_chip_side_radius_mm: Positive
    encoder_below_pcb_depth_mm: Positive
    encoder_standoff_hex_corner_mm: Positive
    rotor_radial_clearance_mm: Positive
    trial_assumptions_authorized: Literal[True]
    process_compensation_mm: Literal[0.0]

    @model_validator(mode="after")
    def feasible_stand(self):
        r_in = self.motor_inner_hole_circle_mm / 2
        r_out = self.motor_outer_hole_circle_mm / 2
        if not r_in < r_out < self.motor_diameter_mm / 2:
            raise ValueError("motor hole circles must be ordered inside the body")
        if self.pocket_depth_mm >= self.motor_stationary_height_mm:
            raise ValueError("pocket wall must stay below the rotating bell")
        engagement = self.motor_screw_length_mm - self.floor_thickness_mm
        if not 0 < engagement <= self.motor_thread_depth_mm:
            raise ValueError("motor screw must engage without exceeding the thread depth")
        if self.encoder_standoff_min_mm <= self.floor_thickness_mm:
            raise ValueError("shortest standoff must keep the PCB below the plate floor")
        if self.encoder_standoff_max_mm < self.encoder_standoff_min_mm:
            raise ValueError("standoff range is inverted")
        sink_inner = r_out - self.m25_countersink_diameter_mm / 2
        if self.center_opening_mm / 2 + 1.0 > sink_inner:
            raise ValueError("center opening must leave at least 1 mm beside the countersinks")
        if self.encoder_chip_side_radius_mm >= self.center_opening_mm / 2:
            raise ValueError("chip-side components must fit inside the center opening")
        if self.standoff_slot_width_mm <= self.encoder_standoff_hex_corner_mm:
            raise ValueError("standoff slots must pass the standoff hex")
        if self.standoff_slot_outer_radius_mm < r_out + self.encoder_standoff_hex_corner_mm / 2:
            raise ValueError("standoff slots must reach standoffs on the outer circle")
        cavity = self.tower_outer_diameter_mm - 2 * self.tower_wall_mm
        if self.encoder_board_max_square_mm * math.sqrt(2) >= cavity:
            raise ValueError("largest board must rotate freely inside the cavity")
        if self.tower_outer_diameter_mm > self.plate_diameter_mm:
            raise ValueError("plate must cover the tower")
        r_wall = self.tower_outer_diameter_mm / 2 - self.tower_wall_mm
        if not r_wall + self.m3_tap_pilot_mm / 2 + 1 <= self.plate_screw_radius_mm <= self.tower_outer_diameter_mm / 2 - self.m3_tap_pilot_mm / 2 - 1:
            raise ValueError("plate screw pilots must sit inside the tower wall with 1 mm each side")
        below = self.encoder_standoff_max_mm + self.encoder_pcb_thickness_mm + self.encoder_below_pcb_depth_mm
        if below >= self.cavity_height_mm:
            raise ValueError("encoder stack must fit in the cavity")
        if self.window_height_mm < self.window_width_mm / 2 or self.window_height_mm + 4 > self.cavity_height_mm - self.plate_screw_pilot_depth_mm:
            raise ValueError("windows need an arched top and must stay below the plate screw pilots")
        if not 2.6 <= self.m25_clearance_mm <= 3.2 or not 3.1 <= self.m3_clearance_mm <= 3.6 or not 2.3 <= self.m3_tap_pilot_mm <= 2.6:
            raise ValueError("invalid trial screw clearances")
        return self


class BldcWinchSpec(Model):
    """Geared string winch on the BLDC stand: rotor gear, two shafts, drum, pulley, weight."""
    schema_version: Literal[1]
    project_id: Identifier
    design_type: Literal["bldc_geared_winch"]
    release_class: Literal["kinematic_demonstrator"]
    length_unit: Literal["mm"]
    stand_spec: Annotated[str, Field(pattern=r"^specs/[a-zA-Z0-9_.-]+\.yaml$")]
    required_ratio: Positive
    module_mm: Positive
    pressure_angle_deg: Positive
    tooth_thinning_mm: Positive
    rotor_gear_teeth: Annotated[int, Field(ge=20, strict=True)]
    stage1_gear_teeth: Annotated[int, Field(ge=20, strict=True)]
    stage2_pinion_teeth: Annotated[int, Field(ge=20, strict=True)]
    output_gear_teeth: Annotated[int, Field(ge=20, strict=True)]
    stage1_face_mm: Positive
    stage2_face_mm: Positive
    stage1_direction_deg: Finite
    stage2_direction_deg: Finite
    axial_gap_mm: Positive
    rotating_clearance_mm: Positive
    rotor_screw_circle_mm: Positive
    rotor_screw_clearance_mm: Positive
    rotor_counterbore_diameter_mm: Positive
    rotor_screw_length_mm: Positive
    rotor_screw_engagement_mm: Positive
    rotor_thread_depth_mm: Positive
    rotor_screw_head_height_mm: Positive
    rotor_center_hole_mm: Positive
    shaft_diameter_mm: Positive
    shaft_flat_depth_mm: Positive
    shaft_length_mm: Positive
    d_bore_diametral_clearance_mm: Positive
    spacer_bore_diametral_clearance_mm: Positive
    spacer_outer_diameter_mm: Positive
    race_boss_diameter_mm: Positive
    race_boss_height_mm: Positive
    bearing_od_mm: Positive
    bearing_id_mm: Positive
    bearing_width_mm: Positive
    bearing_seat_diametral_allowance_mm: Nonnegative
    bearing_lip_hole_mm: Positive
    bearing_boss_radius_mm: Positive
    frame_thickness_mm: Positive
    frame_inner_radius_mm: Positive
    frame_outer_radius_mm: Positive
    column_diameter_mm: Positive
    column_positions_mm: list[Annotated[list[Finite], Field(min_length=2, max_length=2)]]
    column_pilot_depth_mm: Positive
    deck_thickness_mm: Positive
    deck_margin_mm: Positive
    m3_clearance_mm: Positive
    m3_tap_pilot_mm: Positive
    plate_screw_length_mm: Positive
    deck_screw_length_mm: Positive
    pinion_hub_diameter_mm: Positive
    pinion_hub_height_mm: Positive
    set_screw_length_mm: Positive
    nut_across_flats_mm: Positive
    nut_thickness_mm: Positive
    nut_clearance_mm: Positive
    nut_inner_radius_mm: Positive
    drum_groove_radius_mm: Positive
    drum_rim_radius_mm: Positive
    drop_mm: Positive
    drum_turn_margin: Annotated[float, Field(ge=0, lt=0.5, strict=True)]
    string_diameter_mm: Positive
    pulley_groove_radius_mm: Positive
    pulley_flange_radius_mm: Positive
    pulley_width_mm: Positive
    pulley_x_mm: Finite
    pulley_cheek_thickness_mm: Positive
    pulley_side_gap_mm: Positive
    pulley_cheek_radius_mm: Positive
    m5_clearance_mm: Positive
    m5_bolt_length_mm: Positive
    m5_nut_height_mm: Positive
    weight_envelope_diameter_mm: Positive
    weight_envelope_height_mm: Positive
    weight_min_hang_mm: Positive
    desk_edge_margin_mm: Nonnegative
    magnet_diameter_mm: Positive
    magnet_thickness_mm: Positive
    magnet_pocket_clearance_mm: Positive
    magnet_holder_diameter_mm: Positive
    magnet_holder_gap_mm: Positive
    magnet_holder_shaft_engagement_mm: Positive
    encoder_pilot_circle_mm: Positive
    encoder_pilot_count: Annotated[int, Field(ge=2, le=12, strict=True)]
    encoder_pilot_mm: Positive
    encoder_board_max_square_mm: Positive
    encoder_envelope_height_mm: Positive
    trial_assumptions_authorized: Literal[True]
    process_compensation_mm: Literal[0.0]

    @property
    def ratio(self):
        return (self.stage1_gear_teeth / self.rotor_gear_teeth) * (self.output_gear_teeth / self.stage2_pinion_teeth)

    @model_validator(mode="after")
    def feasible_winch(self):
        m = self.module_mm
        if not math.isclose(self.ratio, self.required_ratio, rel_tol=1e-12):
            raise ValueError(f"tooth counts give {self.ratio:g}:1, not the required {self.required_ratio:g}:1")
        if self.rotor_gear_teeth >= self.stage1_gear_teeth or self.stage2_pinion_teeth >= self.output_gear_teeth:
            raise ValueError("both stages must reduce speed")
        if not 0 < self.tooth_thinning_mm < 0.3 or not 14 <= self.pressure_angle_deg <= 25:
            raise ValueError("trial tooth thinning must be 0-0.3 mm and pressure angle 14-25 degrees")
        root = m * (self.rotor_gear_teeth / 2 - 1.25)
        if root - (self.rotor_screw_circle_mm + self.rotor_counterbore_diameter_mm) / 2 < 1.0:
            raise ValueError("rotor screw counterbores must stay 1 mm inside the rotor gear tooth roots")
        if self.rotor_center_hole_mm / 2 + 1.0 > (self.rotor_screw_circle_mm - self.rotor_counterbore_diameter_mm) / 2:
            raise ValueError("rotor center hole would break into the counterbores")
        if not 0 < self.rotor_screw_engagement_mm <= self.rotor_thread_depth_mm:
            raise ValueError("rotor screw must engage without exceeding the thread depth")
        clamp = self.rotor_screw_length_mm - self.rotor_screw_engagement_mm
        if clamp < 1.5 or self.axial_gap_mm + self.stage1_face_mm - clamp < self.rotor_screw_head_height_mm:
            raise ValueError("rotor gear must leave 1.5 mm under the screw head and room to sink the head")
        if not 2.6 <= self.rotor_screw_clearance_mm <= 3.2 or self.rotor_counterbore_diameter_mm < 4.8:
            raise ValueError("invalid M2.5 clearance or counterbore")
        cd2 = m * (self.stage2_pinion_teeth + self.output_gear_teeth) / 2
        tip78 = m * (self.stage1_gear_teeth / 2 + 1)
        if cd2 - tip78 - self.spacer_outer_diameter_mm / 2 < self.rotating_clearance_mm:
            raise ValueError("output shaft spacer passes too close to the stage-1 gear tips")
        if not self.shaft_flat_depth_mm < self.shaft_diameter_mm / 4:
            raise ValueError("D-flat too deep")
        if not self.shaft_diameter_mm + 1.0 <= self.race_boss_diameter_mm <= self.bearing_od_mm - 6.0:
            raise ValueError("race bosses must bear on the inner race only")
        if not self.shaft_diameter_mm + 1.0 < self.bearing_lip_hole_mm < self.bearing_od_mm - 2.0:
            raise ValueError("bearing lip must clear the inner race and still hold the outer race")
        if self.bearing_id_mm != self.shaft_diameter_mm:
            raise ValueError("bearing bore must match the shaft")
        if self.bearing_width_mm >= self.frame_thickness_mm or self.bearing_width_mm >= self.deck_thickness_mm:
            raise ValueError("bearing seats need a lip below the frame and above the deck")
        if self.bearing_boss_radius_mm < self.bearing_od_mm / 2 + 2.0:
            raise ValueError("bearing bosses need 2 mm of wall")
        if self.frame_inner_radius_mm >= self.frame_outer_radius_mm:
            raise ValueError("frame ring is inverted")
        hub_r = self.pinion_hub_diameter_mm / 2
        corner = self.nut_across_flats_mm / math.cos(math.radians(30)) + self.nut_clearance_mm
        outer = self.nut_inner_radius_mm + self.nut_thickness_mm + self.nut_clearance_mm
        if self.nut_inner_radius_mm - (self.shaft_diameter_mm + self.d_bore_diametral_clearance_mm) / 2 < 0.8:
            raise ValueError("nut slot must leave 0.8 mm beside the bore")
        if math.sqrt(hub_r ** 2 - (corner / 2) ** 2) - outer < 0.8:
            raise ValueError("pinion hub must leave 0.8 mm outside the nut slot")
        flat = self.shaft_diameter_mm / 2 - self.shaft_flat_depth_mm
        if not self.nut_inner_radius_mm < flat + self.set_screw_length_mm <= outer:
            raise ValueError("set screw must reach into the nut without passing it")
        root69 = m * (self.output_gear_teeth / 2 - 1.25)
        r_mid = cd2 - hub_r - self.rotating_clearance_mm
        if not root69 - 1.0 < r_mid < self.drum_rim_radius_mm:
            raise ValueError("drum waist must lie between the output gear root and the rim")
        if not self.pulley_groove_radius_mm < self.drum_groove_radius_mm < self.drum_rim_radius_mm:
            raise ValueError("drum groove must be inside the rim")
        r_eff = self.drum_groove_radius_mm + self.string_diameter_mm / 2
        if self.drop_mm > (1 - self.drum_turn_margin) * 2 * math.pi * r_eff:
            raise ValueError("the full drop must take less than one output turn")
        if self.pulley_groove_radius_mm < self.bearing_od_mm / 2 + 2.0 or self.pulley_flange_radius_mm <= self.pulley_groove_radius_mm:
            raise ValueError("pulley groove must leave 2 mm over the bearing and sit below the flanges")
        if self.pulley_width_mm <= self.bearing_width_mm:
            raise ValueError("pulley must be wider than its bearing")
        grip = 2 * (self.pulley_cheek_thickness_mm + self.pulley_side_gap_mm) + self.pulley_width_mm
        if self.m5_bolt_length_mm < grip + self.m5_nut_height_mm:
            raise ValueError("M5 bolt too short for the pulley fork and nut")
        if not 3.1 <= self.m3_clearance_mm <= 3.6 or not 2.3 <= self.m3_tap_pilot_mm <= 2.6 or not 5.1 <= self.m5_clearance_mm <= 5.6:
            raise ValueError("invalid trial screw clearances")
        if self.deck_screw_length_mm - self.deck_thickness_mm > self.column_pilot_depth_mm - 1.0:
            raise ValueError("deck screws would bottom in the column pilots")
        if len(self.column_positions_mm) < 3:
            raise ValueError("the deck needs at least three columns")
        if self.magnet_holder_diameter_mm < self.magnet_diameter_mm + 2.0 or self.magnet_holder_diameter_mm > self.bearing_lip_hole_mm + 4:
            raise ValueError("magnet holder wall too thin or too wide")
        if self.encoder_pilot_circle_mm / 2 - self.encoder_pilot_mm / 2 < self.bearing_od_mm / 2 + 1.5:
            raise ValueError("encoder pilots must clear the output bearing seat")
        return self


SPEC = TypeAdapter(Annotated[SmokeSpec | CubeSphereSpec | JointSpec | GearboxSpec | IndicatorDiscSpec | BldcStandSpec
                             | BldcWinchSpec,
                             Field(discriminator="design_type")])


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than silently accepting the final value."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_yaml(path):
    if path.stat().st_size > 1_000_000:
        raise ValueError("YAML input exceeds 1 MB")
    return yaml.load(path.read_text(), Loader=UniqueLoader)


def load_spec(path):
    return SPEC.validate_python(load_yaml(path))


def readiness(spec, scope):
    """Foundation readiness only; never imply complete release verification."""
    blockers = []
    if scope == "schema":
        return blockers
    if isinstance(spec, JointSpec):
        blockers.append("finger-joint builder is not implemented")
        for key, value in spec.components.model_dump().items():
            if value is None or value == []:
                blockers.append(f"components.{key} is unresolved")
        for key in ("external_envelope_mm", "joint_range_deg"):
            if getattr(spec.requirements, key) is None:
                blockers.append(f"requirements.{key} is unresolved")
        for assumption in spec.assumptions:
            if assumption.approval_state != "approved":
                blockers.append(f"assumption {assumption.id} is {assumption.approval_state}")
        if spec.release_class != "kinematic_demonstrator":
            for key, value in spec.requirements.model_dump().items():
                if value is None:
                    blockers.append(f"requirements.{key} required for requested release class")
    if scope == "release":
        blockers.append("release evaluation and packaging are not implemented; no print authorization")
        if isinstance(spec, GearboxSpec):
            blockers.append("gearbox trial fits, servo attachment, material and physical tests are unverified")
        elif isinstance(spec, BldcStandSpec):
            blockers.append("stand clearances use supplier nominals and Jamie's approximate encoder stack; physical fit unverified")
        elif isinstance(spec, BldcWinchSpec):
            blockers.append("winch gears, bearings, shafts and string are seller nominals; tooth strength is not rated; physical fit unverified")
        elif isinstance(spec, IndicatorDiscSpec):
            blockers.append("indicator disc screw fit and rotor hole pattern are supplier nominals, not measured")
        elif isinstance(spec, (SmokeSpec, CubeSphereSpec)):
            blockers.append("toolchain smoke tests are not releasable manufacturing designs")
        else:
            for key, value in spec.manufacturing.model_dump().items():
                if value is None:
                    blockers.append(f"manufacturing.{key} is unresolved")
    return blockers
