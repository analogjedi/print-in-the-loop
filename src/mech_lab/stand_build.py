"""Development build for the face-up BLDC evaluation stand."""
import base64
import json
import math
from pathlib import Path
import shutil
import tempfile

from build123d import Compound, Cylinder, Pos, Unit, export_step, export_stl, import_step
from cad.assemblies import bldc_stand as stand
from .gearbox_checks import mesh_manifold, normalize_stl_zeros
from .geometry import GeometryPolicy, measure, stl_bounds
from .io import atomic_json, sha256, source_identity
from .schema import load_yaml


def standoff_samples(spec, count=6):
    lo, hi = spec.encoder_standoff_min_mm, spec.encoder_standoff_max_mm
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def inspect_stand(plate, tower, spec, policy):
    """Independent clearance and interface checks against envelopes, not against the CAD intent."""
    checks = []
    zero = policy.volume_relative_tolerance * 1000.0  # mm^3; boolean noise floor, not a fit allowance

    def check(name, passed, measured, expected, **extra):
        checks.append({"check_id": name, "status": "PASS" if passed else "FAIL",
                       "measured": measured, "expected": expected, **extra})

    for name, part in (("motor_plate", plate), ("tower_base", tower)):
        m = measure(part)
        check(f"{name}.valid_single_solid", m["is_valid"] and m["solid_count"] == 1, m["solid_count"], 1)
    fixed = {"motor_plate": plate, "tower_base": tower}
    stationary, _, _ = stand.motor_references(spec)
    v = (plate & stationary).volume
    check("motor_plate.no_motor_overlap", v <= zero, v, 0.)
    v = (plate & tower).volume
    check("plate_tower.no_overlap", v <= zero, v, 0.)
    # The motor must actually rest on plate material at Z=0 outside the openings.
    r_seat0, r_seat1 = spec.center_opening_mm / 2, spec.motor_diameter_mm / 2
    seat = Pos(0, 0, -0.05) * (Cylinder(r_seat1, 0.05) - Cylinder(r_seat0, 0.05))
    v = (plate & seat).volume
    check("motor_plate.seat_supports_motor", v > 0.25 * seat.volume, v, f"> 25% of {seat.volume:.2f}")
    # The plate must rest on the tower wall.
    top = stand.tower_z(spec)[0]
    r_out = spec.tower_outer_diameter_mm / 2
    ring = Pos(0, 0, top - 0.05) * (Cylinder(r_out, 0.05) - Cylinder(r_out - spec.tower_wall_mm, 0.05))
    v = (tower & ring).volume
    check("tower_base.supports_plate", v > 0.5 * ring.volume, v, f"> 50% of {ring.volume:.2f}")
    # Windows must not cut the base, and must leave wall above them for the plate screw pilots.
    _, base_top, bottom = stand.tower_z(spec)
    r_mid = spec.tower_outer_diameter_mm / 2 - spec.tower_wall_mm / 2
    window_top = base_top + 4.0 + spec.window_height_mm
    for sign, side in ((-1, "front"), (1, "rear")):
        probe = Pos(0, sign * r_mid, (bottom + base_top) / 2) * Cylinder(1.0, spec.base_thickness_mm * 0.8)
        v = (tower & probe).volume
        check(f"tower_base.base_intact_under_{side}_window", math.isclose(v, probe.volume, rel_tol=1e-6),
              v, probe.volume)
        above = Pos(0, sign * r_mid, (window_top + top) / 2) * Cylinder(1.0, (top - window_top) * 0.8)
        v = (tower & above).volume
        check(f"tower_base.wall_above_{side}_window", math.isclose(v, above.volume, rel_tol=1e-6),
              v, above.volume)
        opening = Pos(0, sign * r_mid, base_top + 4.0 + spec.window_height_mm / 2) * Cylinder(1.0, 2.0)
        v = (tower & opening).volume
        check(f"tower_base.{side}_window_open", v <= zero, v, 0.)
    for key, keepout in stand.rotating_keepouts(spec).items():
        for name, part in fixed.items():
            v = (part & keepout).volume
            check(f"{name}.clear_of_{key}", v <= zero, v, 0.)
    for s in standoff_samples(spec):
        env = stand.encoder_envelopes(spec, s)
        for key in ("chip_side", "pcb", "below_pcb"):
            for name, part in fixed.items():
                v = (part & env[key]).volume
                check(f"{name}.clear_of_encoder_{key}_at_{s:.1f}mm", v <= zero, v, 0.)
        v = sum((plate & so).volume for so in env["standoffs"])
        check(f"motor_plate.passes_standoffs_at_{s:.1f}mm", v <= zero, v, 0.)
    engagement = spec.motor_screw_length_mm - spec.floor_thickness_mm
    check("motor_screw.thread_engagement_mm", 0 < engagement <= spec.motor_thread_depth_mm,
          engagement, f"0 < e <= {spec.motor_thread_depth_mm}")
    for ref in stand.as5600_reference(spec):
        for name, part in fixed.items():
            v = (part & ref).volume
            check(f"{name}.clear_of_{ref.label}", v <= zero, v, 0.)
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks}


REVIEW_GROUPS = {"motor": ("motor_",), "encoder": ("as5600_",), "screws": ("m25_", "m3_")}


def review_group(name, printable):
    """Viewer toggle group. Printed parts are matched first: 'motor_plate' is not a motor reference."""
    if name in printable:
        return "printed"
    return next((g for g, prefixes in REVIEW_GROUPS.items() if name.startswith(prefixes)), "printed")


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
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".stand-", dir=output.parent))
    try:
        plate, tower = stand.make_plate(spec), stand.make_tower(spec)
        report = inspect_stand(plate, tower, spec, policy)
        checks = report["checks"]
        (stage / "parts").mkdir(); (stage / "print").mkdir(); (stage / "review_meshes").mkdir()
        printable = {"motor_plate": plate, "tower_base": tower}
        records = []
        for name, shape in printable.items():
            native = measure(shape)
            step = stage / "parts" / f"{name}.step"
            if not export_step(shape, step, unit=Unit.MM):
                raise ValueError(f"STEP export failed: {name}")
            reopened = measure(import_step(step))
            same = reopened["is_valid"] and reopened["solid_count"] == 1 and math.isclose(
                native["volume_mm3"], reopened["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
            same = same and all(abs(a - b) <= policy.linear_tolerance_mm for key in ("minimum_mm", "maximum_mm")
                                for a, b in zip(native[key], reopened[key]))
            checks.append({"check_id": f"{name}.step_roundtrip", "status": "PASS" if same else "FAIL",
                           "measured": reopened})
            # Print orientation: the assembly orientation, grounded (plate underside, base bottom down).
            offset = -native["minimum_mm"][2]
            placed = Pos(0, 0, offset) * shape
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
            records.append({"id": name, "step": f"parts/{name}.step", "mesh": f"print/{name}.stl",
                            "print_translation_z_mm": offset, "volume_mm3": native["volume_mm3"]})
        stationary, bell, boss = stand.motor_references(spec)
        references = [stationary, bell, boss, *stand.as5600_reference(spec), *stand.screw_references(spec)]
        meshes = []
        for shape in [plate, tower, *references]:
            name = shape.label
            if not export_stl(shape, stage / "review_meshes" / f"{name}.stl", tolerance=0.03, angular_tolerance=0.15):
                raise ValueError(f"review mesh export failed: {name}")
            group = review_group(name, printable)
            explode = {"motor_plate": 30, "tower_base": 0}.get(name, {"motor": 70, "encoder": 12, "screws": 30}.get(group, 0))
            if name.startswith("m25_"):
                explode = 10
            meshes.append({"name": name, "color": list(shape.color)[:3], "group": group,
                           "rotor": name in ("motor_rotor_reference", "motor_boss_reference"), "explode": explode})
        create_review(stage, spec, meshes)
        assembly = Compound(label=spec.project_id, children=[plate, tower])
        export_step(assembly, stage / "assembly.step", unit=Unit.MM)
        exported, native = measure(import_step(stage / "assembly.step")), measure(assembly)
        good = exported["is_valid"] and exported["solid_count"] == 2 and math.isclose(
            exported["volume_mm3"], native["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        checks.append({"check_id": "assembly_step_roundtrip", "status": "PASS" if good else "FAIL",
                       "measured": exported, "expected": native})
        geometry = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
                    "scope": "bldc_stand_development_geometry", "checks": checks,
                    "policy_sha256": sha256(policy_path)}
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise ValueError("stand checks failed; see geometry_report.json")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        from .build import environment
        manifest = {"schema_version": 1, "project_id": spec.project_id, "status": "PASS",
                    "scope": "development_build", "release_status": "BLOCKED", "length_unit": "mm",
                    "source": source_identity(root), "environment": environment(), "parts": records,
                    "specification_sha256": sha256(spec_path), "policy_sha256": sha256(policy_path),
                    "limitations": ["Motor and encoder are simplified nominal envelopes; physical fit unverified.",
                                    "Encoder clearance is checked over a swept envelope, not a specific future board.",
                                    "Printed hole sizes carry no process compensation; tap M3 pilots by hand.",
                                    "No release or print approval."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "bldc_stand_development_build",
                "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)), "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
