"""Development build for a pinned pocket motor plate on the existing stand tower."""
import base64
import json
import math
from pathlib import Path
import shutil
import tempfile

from build123d import Compound, Cylinder, Pos, Unit, export_step, export_stl, import_step
from cad.assemblies import bldc_pinned_plate as pp
from cad.assemblies.bldc_stand import PLATE_SCREW_ANGLES, polar
from .gearbox_checks import mesh_manifold, normalize_stl_zeros
from .geometry import GeometryPolicy, measure, stl_bounds
from .io import atomic_json, sha256, source_identity
from .schema import load_spec, load_yaml
from .stand_build import review_group  # same viewer groups as the stand


def standoff_samples(spec, count=6):
    lo, hi = spec.encoder_standoff_min_mm, spec.encoder_standoff_max_mm
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def inspect_plate(plate, tower, spec, ss, policy):
    """Independent fit, clearance and interface checks against envelopes, not against the CAD intent."""
    checks = []
    zero = policy.volume_relative_tolerance * 1000.0  # mm^3; boolean noise floor, not a fit allowance

    def check(name, passed, measured, expected):
        checks.append({"check_id": name, "status": "PASS" if passed else "FAIL",
                       "measured": measured, "expected": expected})

    m = measure(plate)
    check("motor_plate.valid_single_solid", m["is_valid"] and m["solid_count"] == 1, m["solid_count"], 1)
    stationary, _, _ = pp.motor_references(spec)
    # The only plate material inside the stator ring is the crush-rib interference.
    ribs = pp.make_ribs(spec)
    grip = plate & stationary
    v_all, v_out = grip.volume, (grip - ribs).volume
    check("motor_plate.overlap_only_at_crush_ribs", v_out <= zero, v_out, 0.)
    check("motor_plate.crush_ribs_grip_ring", v_all > zero, v_all, "> 0")
    n_ribs = len(pp.rib_angles(spec))
    check("motor_plate.crush_rib_count", n_ribs >= 3, n_ribs, ">= 3")
    # The pin must reach into the locating hole and stay clear of the hole wall (covered above).
    hole = pp.locating_hole(spec)
    v_pin = (plate & hole).volume
    pin_full = math.pi * (spec.pin_diameter_mm / 2) ** 2 * (spec.pin_height_mm - 0.4)
    check("motor_plate.pin_engages_locating_hole", v_pin >= pin_full, v_pin, f">= {pin_full:.2f}")
    # The stator face must rest on plate material at Z=0 around the opening.
    r0, r1 = spec.center_opening_mm / 2, spec.motor_diameter_mm / 2
    seat = Pos(0, 0, -0.05) * (Cylinder(r1, 0.05) - Cylinder(r0, 0.05))
    v = (plate & seat).volume
    check("motor_plate.seat_supports_stator", v > 0.75 * seat.volume, v, f"> 75% of {seat.volume:.2f}")
    # Interface to the existing tower.
    v = (plate & tower).volume
    check("plate_tower.no_overlap", v <= zero, v, 0.)
    top = measure(tower)["maximum_mm"][2]
    check("plate_tower.plate_underside_on_tower_top", abs(top - pp.plate_z(spec)[0]) <= policy.linear_tolerance_mm,
          top, pp.plate_z(spec)[0])
    r_out = ss.tower_outer_diameter_mm / 2
    ring = Pos(0, 0, top - 0.05) * (Cylinder(r_out, 0.05) - Cylinder(r_out - ss.tower_wall_mm, 0.05))
    v = (tower & ring).volume
    check("tower_base.supports_plate", v > 0.5 * ring.volume, v, f"> 50% of {ring.volume:.2f}")
    check("motor_plate.covers_tower_top", spec.plate_diameter_mm >= ss.tower_outer_diameter_mm,
          spec.plate_diameter_mm, f">= {ss.tower_outer_diameter_mm}")
    z0, z1 = pp.plate_z(spec)
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(ss.plate_screw_radius_mm, a)
        path = Pos(x, y, z0) * Cylinder(1.5, z1 - z0, align=pp.MIN)
        v = (plate & path).volume
        check(f"motor_plate.m3_path_clear_at_{a:g}", v <= zero, v, 0.)
    engagement = spec.plate_screw_length_mm - (z1 - z0)
    check("plate_screw.pilot_engagement_mm", 4.0 <= engagement <= ss.plate_screw_pilot_depth_mm - 1.0,
          engagement, f"4 <= e <= {ss.plate_screw_pilot_depth_mm - 1.0}")
    for key, keepout in pp.rotating_keepouts(spec).items():
        for name, part in (("motor_plate", plate), ("tower_base", tower)):
            v = (part & keepout).volume
            check(f"{name}.clear_of_{key}", v <= zero, v, 0.)
    v = (plate & pp.lead_envelope(spec)).volume
    check("motor_plate.lead_notch_clear", v <= zero, v, 0.)
    for s in standoff_samples(spec):
        env = pp.encoder_envelopes(spec, s)
        for key in ("chip_side", "pcb", "below_pcb"):
            for name, part in (("motor_plate", plate), ("tower_base", tower)):
                v = (part & env[key]).volume
                check(f"{name}.clear_of_encoder_{key}_at_{s:.1f}mm", v <= zero, v, 0.)
        v = sum((plate & so).volume for so in env["standoffs"])
        check(f"motor_plate.passes_standoffs_on_all_four_holes_at_{s:.1f}mm", v <= zero, v, 0.)
    for ref in pp.as5600_reference(spec, spec.encoder_review_standoff_mm):
        for name, part in (("motor_plate", plate), ("tower_base", tower)):
            v = (part & ref).volume
            check(f"{name}.clear_of_{ref.label}", v <= zero, v, 0.)
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks}


def create_review(stage, spec, meshes):
    template = Path(__file__).with_name("stand_viewer.html").read_text()
    payload = [{**m, "data": base64.b64encode((stage / "review_meshes" / f"{m['name']}.stl").read_bytes()).decode()}
               for m in meshes]
    title = f"{spec.project_id} — {spec.motor_reference}"
    (stage / "review.html").write_text(template.replace("__MESH_DATA__", json.dumps(payload))
                                       .replace("__TITLE__", title))


def build(root, spec, spec_path, output):
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    policy_path = root / "validation/release_policy.yaml"
    policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    ss = load_spec(root / spec.stand_spec)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".plate-", dir=output.parent))
    try:
        plate, tower = pp.make_plate(spec, ss), pp.make_tower_at(spec, ss)
        report = inspect_plate(plate, tower, spec, ss, policy)
        checks = report["checks"]
        (stage / "parts").mkdir(); (stage / "print").mkdir(); (stage / "review_meshes").mkdir()
        name = plate.label
        native = measure(plate)
        step = stage / "parts" / f"{name}.step"
        if not export_step(plate, step, unit=Unit.MM):
            raise ValueError(f"STEP export failed: {name}")
        reopened = measure(import_step(step))
        same = reopened["is_valid"] and reopened["solid_count"] == 1 and math.isclose(
            native["volume_mm3"], reopened["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        same = same and all(abs(a - b) <= policy.linear_tolerance_mm for key in ("minimum_mm", "maximum_mm")
                            for a, b in zip(native[key], reopened[key]))
        checks.append({"check_id": f"{name}.step_roundtrip", "status": "PASS" if same else "FAIL",
                       "measured": reopened})
        # Print orientation: as assembled, underside on the bed; pin and ribs point up.
        offset = -native["minimum_mm"][2]
        placed = Pos(0, 0, offset) * plate
        mesh = stage / "print" / f"{name}.stl"
        if not export_stl(placed, mesh, tolerance=policy.stl_linear_deflection_mm,
                          angular_tolerance=policy.stl_angular_deflection_rad):
            raise ValueError(f"STL export failed: {name}")
        checks.append({"check_id": f"{name}.stl_zero_normalization",
                       **normalize_stl_zeros(mesh, policy.linear_tolerance_mm * 0.001)})
        bounds, expected = stl_bounds(mesh), measure(placed)
        tol = policy.stl_linear_deflection_mm + max(expected["dimensions_mm"]) * 1.2e-7
        good = all(abs(a - b) <= 2 * tol for key in ("minimum_mm", "maximum_mm")
                   for a, b in zip(bounds[key], expected[key])) and abs(bounds["minimum_mm"][2]) < 1e-5
        checks.append({"check_id": f"{name}.stl_print_placement", "status": "PASS" if good else "FAIL",
                       "measured": bounds})
        checks.append({"check_id": f"{name}.stl_manifold", **mesh_manifold(mesh)})
        records = [{"id": name, "step": f"parts/{name}.step", "mesh": f"print/{name}.stl",
                    "print_translation_z_mm": offset, "volume_mm3": native["volume_mm3"]}]
        stationary, bell, boss = pp.motor_references(spec)
        references = [stationary, bell, boss, pp.lead_reference(spec),
                      *pp.as5600_reference(spec, spec.encoder_review_standoff_mm), *pp.screw_references(spec, ss)]
        printable = {name: plate, "tower_base": tower}
        meshes = []
        for shape in [plate, tower, *references]:
            label = shape.label
            if not export_stl(shape, stage / "review_meshes" / f"{label}.stl", tolerance=0.03, angular_tolerance=0.15):
                raise ValueError(f"review mesh export failed: {label}")
            group = review_group(label, printable)
            explode = {name: 25, "tower_base": 0}.get(label, {"motor": 55, "encoder": 12, "screws": 25}.get(group, 0))
            meshes.append({"name": label, "color": list(shape.color)[:3], "group": group,
                           "rotor": label in ("motor_rotor_reference", "motor_boss_reference"), "explode": explode})
        create_review(stage, spec, meshes)
        assembly = Compound(label=spec.project_id, children=[plate])
        export_step(assembly, stage / "assembly.step", unit=Unit.MM)
        exported = measure(import_step(stage / "assembly.step"))
        good = exported["is_valid"] and exported["solid_count"] == 1 and math.isclose(
            exported["volume_mm3"], native["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        checks.append({"check_id": "assembly_step_roundtrip", "status": "PASS" if good else "FAIL",
                       "measured": exported})
        geometry = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
                    "scope": "bldc_pinned_plate_development_geometry", "checks": checks,
                    "policy_sha256": sha256(policy_path)}
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise ValueError("plate checks failed; see geometry_report.json")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(root / spec.stand_spec, stage / "stand_specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        from .build import environment
        manifest = {"schema_version": 1, "project_id": spec.project_id, "status": "PASS",
                    "scope": "development_build", "release_status": "BLOCKED", "length_unit": "mm",
                    "source": source_identity(root), "environment": environment(), "parts": records,
                    "specification_sha256": sha256(spec_path), "policy_sha256": sha256(policy_path),
                    "limitations": ["Motor and encoder are simplified supplier-nominal envelopes; physical fit unverified.",
                                    "Crush-rib interference and pin fit carry no process compensation; not calibrated.",
                                    "The kit's motor-to-board spacing is unknown; the plate is checked over a range.",
                                    "The tower is the existing printed part; only the plate is exported for print.",
                                    "No release or print approval."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "bldc_pinned_plate_development_build",
                "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)), "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
