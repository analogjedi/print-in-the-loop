"""Development build for the rotor degree dial (two filaments) and its fixed pointer."""
import math
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace

from build123d import Compound, Cylinder, Pos, Rot, Unit, export_step, export_stl, import_step
from cad.assemblies import bldc_pinned_plate as pp
from cad.parts import rotor_dial as rd
from .gearbox_checks import mesh_manifold, normalize_stl_zeros
from .geometry import GeometryPolicy, measure, stl_bounds
from .io import atomic_json, sha256, source_identity
from .plate_build import create_review
from .schema import load_spec, load_yaml
from .stand_build import review_group


def angle_of(shape):
    c = shape.center()
    return math.degrees(math.atan2(c.Y, c.X)) % 360.0, math.hypot(c.X, c.Y)


def angle_error(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def holed_dial_volume(spec, ps):
    """Analytic volume of the blank: disc minus recess, center hole and countersunk screw holes."""
    R, t, d = spec.dial_diameter_mm / 2, spec.dial_thickness_mm, spec.rotor_recess_depth_mm
    hub = t - d
    r, s = spec.screw_clearance_mm / 2, spec.countersink_diameter_mm / 2
    k = s - r
    per_hole = math.pi * r * r * hub + math.pi * k / 3 * (s * s + s * r + r * r) - math.pi * r * r * k
    return (math.pi * R * R * t - math.pi * rd.recess_radius(spec, ps) ** 2 * d
            - math.pi * (spec.center_hole_mm / 2) ** 2 * hub - len(spec.rotor_hole_angles_deg) * per_hole)


def inspect_dial(dial, marks, pointer, spec, ps, ss, policy):
    """Independent checks against the motor, plate, tower and screw envelopes."""
    checks = []
    tol, rel = policy.linear_tolerance_mm, policy.volume_relative_tolerance
    zero = rel * 1000.0  # mm^3 boolean noise floor

    def check(name, passed, measured, expected):
        checks.append({"check_id": name, "status": "PASS" if passed else "FAIL",
                       "measured": measured, "expected": expected})

    bottom, face, top = rd.dial_z(spec, ps)
    m = measure(dial)
    check("dial.valid_single_solid", m["is_valid"] and m["solid_count"] == 1, m["solid_count"], 1)
    size = [spec.dial_diameter_mm, spec.dial_diameter_mm, spec.dial_thickness_mm]
    check("dial.envelope_mm", all(abs(a - b) <= tol for a, b in zip(m["dimensions_mm"], size))
          and abs(m["minimum_mm"][2] - bottom) <= tol, [m["dimensions_mm"], m["minimum_mm"][2]], [size, bottom])
    # Scale: every mark flush with the top face, inlaid without overlap, filling its pocket exactly.
    total = 0.
    for mark in marks:
        mm = measure(mark)
        z = [mm["minimum_mm"][2], mm["maximum_mm"][2]]
        flush = mm["is_valid"] and abs(z[0] - (top - spec.inlay_depth_mm)) <= tol and abs(z[1] - top) <= tol
        check(f"{mark.label}.flush_inlay", flush, z, [top - spec.inlay_depth_mm, top])
        v = (dial & mark).volume
        check(f"{mark.label}.no_body_overlap", v <= zero, v, 0.)
        total += mm["volume_mm3"]
    filled, target = m["volume_mm3"] + total, holed_dial_volume(spec, ps)
    check("dial_plus_scale.fills_blank_mm3", math.isclose(filled, target, rel_tol=rel), filled, target)
    ticks = [k for k in marks if k.label.startswith("tick_")]
    labels = [k for k in marks if k.label.startswith("label_")]
    n = round(360 / spec.minor_tick_step_deg)
    check("scale.tick_count", len(ticks) == n, len(ticks), n)
    for tick in ticks:
        value = float(tick.label.split("_")[1].removesuffix("deg"))
        a, _ = angle_of(tick)
        expect = rd.scale_angle(spec, value)
        check(f"{tick.label}.angle_deg", angle_error(a, expect) <= 0.05, a, expect)
    # Readings increase in the specified direction seen from above: label 'v' sits at zero -/+ v.
    n_labels = round(360 / spec.label_step_deg)
    check("scale.label_count", len(labels) == n_labels, len(labels), n_labels)
    tick_outer = rd.tick_outer_radius(spec)
    major_inner = tick_outer - spec.major_tick_length_mm
    for label in labels:
        value = float(label.label.split("_")[1].removesuffix("deg"))
        a, r = angle_of(label)
        expect = rd.scale_angle(spec, value)
        check(f"{label.label}.angle_deg", angle_error(a, expect) <= 2.0, a, expect)
        check(f"{label.label}.radius_mm", abs(r - spec.label_radius_mm) <= 1.0, r, spec.label_radius_mm)
        near = [t for t in ticks if angle_error(angle_of(t)[0], a) <= 25.0]
        gap = min(label.distance_to(t) for t in near)
        check(f"{label.label}.clear_of_ticks_mm", gap >= spec.min_feature_mm, gap, f">= {spec.min_feature_mm}")
    gap = min(labels, key=lambda k: angle_error(angle_of(k)[0], spec.zero_angle_deg)).distance_to(marks[-1])
    check("zero_marker.clear_of_zero_label_mm", gap >= spec.min_feature_mm, gap, f">= {spec.min_feature_mm}")
    sinks = rd.countersink_holes(spec, ps)
    gap = min(k.distance_to(s) for k in [*labels, marks[-1]] for s in sinks)
    check("scale.clear_of_countersinks_mm", gap >= 1.0, gap, ">= 1.0")
    check("scale.labels_inside_major_ticks", spec.label_radius_mm < major_inner, spec.label_radius_mm,
          f"< {major_inner}")
    # Seat on the rotor: the hub rests on the rotor face, the step clears the rotor rim.
    stationary, bell, boss = pp.motor_references(ps)
    v = (dial & bell).volume
    check("dial.no_overlap_with_rotor", v <= zero, v, 0.)
    r_face = ps.motor_diameter_mm / 2
    seat = Pos(0, 0, face) * (Cylinder(r_face, 0.05, align=rd.MIN) - Cylinder(ps.shaft_bore_mm / 2, 0.05, align=rd.MIN))
    v = (dial & seat).volume
    check("dial.hub_seats_on_rotor_face", v > 0.75 * seat.volume, v, f"> 75% of {seat.volume:.2f}")
    radial = rd.recess_radius(spec, ps) - r_face
    check("dial.recess_clears_rotor_rim_mm", 0 < radial <= 0.3, radial, "(0, 0.3]")
    check("dial.center_hole_keeps_bore_open", spec.center_hole_mm >= ps.shaft_bore_mm, spec.center_hole_mm,
          f">= {ps.shaft_bore_mm}")
    for screw in rd.dial_screw_references(spec, ps):
        v = (dial & screw).volume
        check(f"{screw.label}.passes_dial", v <= zero, v, 0.)
        below = measure(screw)["minimum_mm"][2]
        depth = face - below
        check(f"{screw.label}.thread_depth_mm", 1.5 <= depth <= spec.rotor_thread_depth_mm, depth,
              f"1.5 <= d <= {spec.rotor_thread_depth_mm}")
    # Turning dial versus every fixed part.
    plate, tower = pp.make_plate(ps, ss), pp.make_tower_at(ps, ss)
    keepout = rd.dial_keepout(spec, ps)
    plate_screws = rd.plate_screw_references(spec, ps, ss)
    fixed = {"motor_plate": plate, "tower_base": tower, "dial_pointer": pointer,
             "motor_stationary": stationary, **{s.label: s for s in plate_screws}}
    for name, part in fixed.items():
        v = (part & keepout).volume
        check(f"{name}.clear_of_turning_dial", v <= zero, v, 0.)
    # Pointer: one solid, resting on the plate, hooked on the rim, clamped by the plate screw.
    pm = measure(pointer)
    check("dial_pointer.valid_single_solid", pm["is_valid"] and pm["solid_count"] == 1, pm["solid_count"], 1)
    for name, part in (("motor_plate", plate), ("tower_base", tower)):
        v = (pointer & part).volume
        check(f"dial_pointer.no_overlap_with_{name}", v <= zero, v, 0.)
    for s in plate_screws:
        v = (pointer & s).volume
        check(f"dial_pointer.clear_of_{s.label}", v <= zero, v, 0.)
    z0, plate_top = pp.plate_z(ps)
    contact = Pos(0, 0, plate_top) * Cylinder(ps.plate_diameter_mm / 2, 0.05, align=rd.MIN)
    v = (pointer & contact).volume
    check("dial_pointer.rests_on_plate_top", v > 0.05 * 20.0, v, "> 1.0 (20 mm^2)")
    r_rim = max(ps.plate_diameter_mm, ss.tower_outer_diameter_mm) / 2
    band = Pos(0, 0, plate_top) * (Cylinder(r_rim + spec.pointer_lip_clearance_mm + 0.1, 4.0, align=rd.MAX)
                                   - Cylinder(r_rim, 4.0, align=rd.MAX))
    v = (pointer & band).volume
    check("dial_pointer.lip_hooks_rim", v > zero, v, "> 0")
    engagement = spec.pointer_screw_length_mm - spec.pointer_floor_under_head_mm - (plate_top - z0)
    check("dial_pointer.screw_pilot_engagement_mm", 4.0 <= engagement <= ss.plate_screw_pilot_depth_mm - 1.0,
          engagement, f"4 <= e <= {ss.plate_screw_pilot_depth_mm - 1.0}")
    check("dial_pointer.top_level_with_dial_face", abs(pm["maximum_mm"][2] - top) <= tol, pm["maximum_mm"][2], top)
    gap = pointer.distance_to(dial)
    check("dial_pointer.reading_gap_mm", spec.rotating_clearance_mm <= gap <= 3.0, gap,
          f"{spec.rotating_clearance_mm} <= g <= 3.0")
    tip = pointer & (Pos(0, 0, top - 0.5) * (Cylinder(rd.pointer_radii(spec)[0] + 1.0, 0.5, align=rd.MIN)))
    a, _ = angle_of(tip)
    check("dial_pointer.tip_angle_deg", angle_error(a, spec.pointer_screw_angle_deg) <= 0.5, a,
          spec.pointer_screw_angle_deg)
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks}


def export_checked(stage, policy, shape, name, transform, checks, records, note):
    native = measure(shape)
    step = stage / "parts" / f"{name}.step"
    if not export_step(shape, step, unit=Unit.MM):
        raise ValueError(f"STEP export failed: {name}")
    reopened = measure(import_step(step))
    same = reopened["is_valid"] and reopened["solid_count"] == native["solid_count"] and math.isclose(
        native["volume_mm3"], reopened["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
    same = same and all(abs(a - b) <= policy.linear_tolerance_mm for key in ("minimum_mm", "maximum_mm")
                        for a, b in zip(native[key], reopened[key]))
    checks.append({"check_id": f"{name}.step_roundtrip", "status": "PASS" if same else "FAIL", "measured": reopened})
    placed = transform * shape
    mesh = stage / "print" / f"{name}.stl"
    if not export_stl(placed, mesh, tolerance=policy.stl_linear_deflection_mm,
                      angular_tolerance=policy.stl_angular_deflection_rad):
        raise ValueError(f"STL export failed: {name}")
    checks.append({"check_id": f"{name}.stl_zero_normalization",
                   **normalize_stl_zeros(mesh, policy.linear_tolerance_mm * 0.001)})
    bounds, expected = stl_bounds(mesh), measure(placed)
    tol = policy.stl_linear_deflection_mm + max(expected["dimensions_mm"]) * 1.2e-7
    good = all(abs(a - b) <= 2 * tol for key in ("minimum_mm", "maximum_mm")
               for a, b in zip(bounds[key], expected[key]))
    checks.append({"check_id": f"{name}.stl_print_placement", "status": "PASS" if good else "FAIL",
                   "measured": bounds, "expected": expected})
    checks.append({"check_id": f"{name}.stl_manifold", **mesh_manifold(mesh)})
    records.append({"id": name, "step": f"parts/{name}.step", "mesh": f"print/{name}.stl", "print_transform": note,
                    "volume_mm3": native["volume_mm3"], "solids": native["solid_count"]})


def build(root, spec, spec_path, output):
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    policy_path = root / "validation/release_policy.yaml"
    policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    ps = load_spec(root / spec.plate_spec)
    ss = load_spec(root / ps.stand_spec)
    font = Path(spec.font_path)
    if not font.is_file():
        raise ValueError(f"font not found: {font}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".dial-", dir=output.parent))
    try:
        dial, marks, pointer = rd.make_dial(spec, ps), rd.make_marks(spec, ps), rd.make_pointer(spec, ps, ss)
        report = inspect_dial(dial, marks, pointer, spec, ps, ss, policy)
        checks = report["checks"]
        (stage / "parts").mkdir(); (stage / "print").mkdir(); (stage / "review_meshes").mkdir()
        scale = Compound(label="rotor_dial_scale", children=marks)
        scale.color = rd.RED
        _, _, top = rd.dial_z(spec, ps)
        # Dial face down on the bed (scale in the first layers); both bodies share one transform.
        face_down = Pos(0, 0, top) * Rot(180, 0, 0)
        records = []
        export_checked(stage, policy, dial, "rotor_dial", face_down, checks, records,
                       "rotate 180 deg about X, dial face on the bed")
        export_checked(stage, policy, scale, "rotor_dial_scale", face_down, checks, records,
                       "same transform as rotor_dial; second filament")
        # Pointer on its side: turned back to +X, then its -Y side face on the bed.
        side = Pos(0, 0, spec.pointer_width_mm / 2) * Rot(90, 0, 0) * Rot(0, 0, -spec.pointer_screw_angle_deg)
        export_checked(stage, policy, pointer, "dial_pointer", side, checks, records,
                       "turn to +X, rotate 90 deg about X, side face on the bed")
        plate, tower = pp.make_plate(ps, ss), pp.make_tower_at(ps, ss)
        stationary, bell, boss = pp.motor_references(ps)
        references = [stationary, bell, boss, *rd.dial_screw_references(spec, ps),
                      *rd.plate_screw_references(spec, ps, ss)]
        printable = {"rotor_dial": dial, "rotor_dial_scale": scale, "dial_pointer": pointer,
                     "motor_plate_2804": plate, "tower_base": tower}
        spinning = ("rotor_dial", "rotor_dial_scale", "motor_rotor_reference", "motor_boss_reference")
        meshes = []
        for label, shape in [*printable.items(), *[(r.label, r) for r in references]]:
            if not export_stl(shape, stage / "review_meshes" / f"{label}.stl", tolerance=0.03, angular_tolerance=0.15):
                raise ValueError(f"review mesh export failed: {label}")
            group = review_group(label, printable)
            explode = {"rotor_dial": 30, "rotor_dial_scale": 30, "dial_pointer": 12}.get(
                label, 45 if label.startswith("m25_") else 0)
            color = list(shape.color)[:3] if label not in ("motor_plate_2804", "tower_base") else list(rd.WHITE)[:3]
            meshes.append({"name": label, "color": color, "group": group,
                           "rotor": label in spinning or label.startswith("m25_dial"), "explode": explode})
        create_review(stage, SimpleNamespace(project_id=spec.project_id, motor_reference=ps.motor_reference), meshes)
        assembly = Compound(label=spec.project_id, children=[dial, *marks, pointer])
        export_step(assembly, stage / "assembly.step", unit=Unit.MM)
        exported, native = measure(import_step(stage / "assembly.step")), measure(assembly)
        good = exported["is_valid"] and exported["solid_count"] == native["solid_count"] and math.isclose(
            exported["volume_mm3"], native["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        checks.append({"check_id": "assembly_step_roundtrip", "status": "PASS" if good else "FAIL",
                       "measured": exported, "expected": native})
        geometry = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
                    "scope": "rotor_dial_development_geometry", "checks": checks,
                    "policy_sha256": sha256(policy_path)}
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise ValueError("dial checks failed; see geometry_report.json")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(root / spec.plate_spec, stage / "plate_specification.yaml")
        shutil.copyfile(root / ps.stand_spec, stage / "stand_specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        from .build import environment
        manifest = {"schema_version": 1, "project_id": spec.project_id, "status": "PASS",
                    "scope": "development_build", "release_status": "BLOCKED", "length_unit": "mm",
                    "source": source_identity(root), "environment": environment(), "parts": records,
                    "font": {"path": str(font), "sha256": sha256(font)},
                    "specification_sha256": sha256(spec_path), "policy_sha256": sha256(policy_path),
                    "limitations": ["Rotor hole pattern, thread depth and outer diameter are supplier nominals.",
                                    "Scale STL is a multi-solid second-filament body; slice it with the dial.",
                                    "Glyph stroke widths are not checked here; inspect the slicer preview.",
                                    "The plate and tower are the existing printed parts; not exported for print.",
                                    "No release or print approval."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "rotor_dial_development_build",
                "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)), "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
