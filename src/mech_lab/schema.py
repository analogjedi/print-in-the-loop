"""Strict specification contracts. Unknown engineering values remain None."""
from __future__ import annotations

from datetime import date
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


SPEC = TypeAdapter(Annotated[SmokeSpec | CubeSphereSpec | JointSpec | GearboxSpec, Field(discriminator="design_type")])


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
        elif isinstance(spec, (SmokeSpec, CubeSphereSpec)):
            blockers.append("toolchain smoke tests are not releasable manufacturing designs")
        else:
            for key, value in spec.manufacturing.model_dump().items():
                if value is None:
                    blockers.append(f"manufacturing.{key} is unresolved")
    return blockers
