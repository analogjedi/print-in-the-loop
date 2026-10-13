"""Development build and independent checks for the geared BLDC string winch."""
import base64
import json
import math
from pathlib import Path
import shutil
import tempfile

from build123d import Compound, Pos, Rot, Unit, export_step, export_stl, import_step
from shapely import Polygon as ShapelyPolygon
from shapely.affinity import rotate, translate

from cad.assemblies import bldc_stand as stand
from cad.assemblies import bldc_winch as winch
from cad.parts.spur_gear import profile_points
from .gearbox_checks import boxes_overlap, mesh_manifold, normalize_stl_zeros
from .geometry import GeometryPolicy, measure, stl_bounds
from .io import atomic_json, sha256, source_identity
from .schema import load_spec, load_yaml

# Purchased parts that thread into printed pilots or into each other; their overlap is the thread.
THREADED = {("m3x16_plate_screw", "tower_base"), ("m3x16_deck_screw", "winch_frame"),
            ("m25x6_rotor_screw", "motor_rotor_reference"), ("m3x4_set_screw_a", "m3_nut_a"),
            ("m3x4_set_screw_b", "m3_nut_b")}
CLEARANCE_MM = 1.0  # minimum gap checked around rotating parts; a review margin, not a print fit


def common_volume(a, b):
    if not boxes_overlap(a, b):
        return 0.
    return sum(abs(s.volume) for s in (a & b).solids())


def threaded(n1, n2):
    return any((n1.startswith(a) and n2.startswith(b)) or (n2.startswith(a) and n1.startswith(b))
               for a, b in THREADED)


def grown_envelopes(spec, ss, grow):
    """Rotating envelopes enlarged by `grow` radially and axially (drum cones shift horizontally)."""
    z, c, m = winch.levels(spec, ss), winch.centers(spec), spec.module_mm
    cyl = winch.cyl
    tip = lambda n: m * (n / 2 + 1) + grow
    root23 = m * (spec.stage2_pinion_teeth / 2 - 1.25)
    root26 = m * (spec.rotor_gear_teeth / 2 - 1.25)
    so = spec.spacer_outer_diameter_mm / 2 + grow
    g = grow
    profile = [(r + g, zz) for r, zz in winch.drum_profile(spec, z)]
    profile = [(profile[0][0], profile[0][1] - g), *profile, (profile[-1][0], profile[-1][1] + g)]
    return {
        "rotor_gear": ("rotor", cyl(tip(spec.rotor_gear_teeth), z["s1"] - g, z["s1_top"] + g)
                       + cyl(root26 - 0.75 + g, z["rotor"], z["s1"])),
        "stage1_gear": ("shaft_a", cyl(tip(spec.stage1_gear_teeth), z["s1"] - g, z["s1_top"] + g, *c["A"])),
        "stage2_pinion": ("shaft_a", cyl(tip(spec.stage2_pinion_teeth), z["s2"] - g, z["s2_top"], *c["A"])
                          + cyl(root23 - 1.0 + g, z["s1_top"], z["s2"], *c["A"])),
        "pinion_hub": ("shaft_a", cyl(spec.pinion_hub_diameter_mm / 2 + g, z["s2_top"], z["hub_top"] + g, *c["A"])),
        "spacers_a": ("shaft_a", cyl(so, z["frame1"] - g, z["s1"], *c["A"]) + cyl(so, z["hub_top"], z["deck0"] + g, *c["A"])),
        "output_gear": ("shaft_b", cyl(tip(spec.output_gear_teeth), z["s2"] - g, z["s2_top"], *c["B"])),
        "drum": ("shaft_b", winch.stack(profile, *c["B"])
                 + cyl(spec.race_boss_diameter_mm / 2 + g, z["drum_top"], z["deck0"], *c["B"])),
        "spacer_b": ("shaft_b", cyl(so, z["frame1"] - g, z["s2"], *c["B"])),
        "magnet_holder": ("shaft_b", cyl(spec.magnet_holder_diameter_mm / 2 + g, z["holder0"] - g, z["holder1"] + g, *c["B"])),
    }


def mesh_motion(spec, name, np_, ng, pinion_xy, gear_xy, pinion_deg, gear_deg, phase_error_deg=0., samples=181):
    """Planar tooth sweep over one pinion pitch with an interval clearance bound (as the gearbox)."""
    m, pa, th = spec.module_mm, spec.pressure_angle_deg, spec.tooth_thinning_mm
    coarse = {n: ShapelyPolygon(profile_points(n, m, pa, th)) for n in (np_, ng)}
    fine = {n: ShapelyPolygon(profile_points(n, m, pa, th, samples=256)) for n in (np_, ng)}
    convergence = max(coarse[n].hausdorff_distance(fine[n]) for n in coarse)
    allowance = 0.002
    pitch = 360 / np_
    minimum, max_area = float("inf"), 0.
    for j in range(samples):
        a = pitch * j / (samples - 1)
        p = translate(rotate(coarse[np_], pinion_deg + a, origin=(0, 0)), *pinion_xy)
        g = translate(rotate(coarse[ng], gear_deg - a * np_ / ng + phase_error_deg, origin=(0, 0)), *gear_xy)
        minimum = min(minimum, p.distance(g))
        max_area = max(max_area, p.intersection(g).area)
    half = math.radians(pitch / (samples - 1)) / 2
    bound = m * (np_ / 2 + 1) * half + m * (ng / 2 + 1) * half * np_ / ng
    lower = minimum - bound - 2 * allowance
    ok = max_area == 0 and lower > 0 and convergence < allowance
    return {"check_id": f"{name}.full_tooth_period", "status": "PASS" if ok else "FAIL", "samples": samples,
            "pinion_period_deg": pitch, "measured_minimum_gap_mm": minimum,
            "maximum_intersection_area_mm2": max_area, "interval_motion_bound_mm": bound,
            "continuous_gap_lower_bound_mm": lower, "contour_refinement_difference_mm": convergence}


def contact_ratio(spec, np_, ng):
    m, a = spec.module_mm, math.radians(spec.pressure_angle_deg)
    r1, r2 = m * np_ / 2, m * ng / 2
    b1, b2 = r1 * math.cos(a), r2 * math.cos(a)
    return (math.sqrt((r1 + m) ** 2 - b1 ** 2) + math.sqrt((r2 + m) ** 2 - b2 ** 2) - (r1 + r2) * math.sin(a)) / (
        math.pi * m * math.cos(a))


def motion_checks(spec, phase_error_deg=0.):
    c, ph = winch.centers(spec), winch.phases(spec)
    checks = [mesh_motion(spec, "mesh_stage1", spec.rotor_gear_teeth, spec.stage1_gear_teeth, c["O"], c["A"],
                          ph["rotor"], ph["stage1_gear"], phase_error_deg),
              mesh_motion(spec, "mesh_stage2", spec.stage2_pinion_teeth, spec.output_gear_teeth, c["A"], c["B"],
                          ph["stage2_pinion"], ph["output_gear"], phase_error_deg)]
    for name, np_, ng in (("stage1", spec.rotor_gear_teeth, spec.stage1_gear_teeth),
                          ("stage2", spec.stage2_pinion_teeth, spec.output_gear_teeth)):
        cr = contact_ratio(spec, np_, ng)
        checks.append({"check_id": f"mesh_{name}.nominal_contact_ratio", "status": "PASS" if cr > 1.2 else "FAIL",
                       "measured": cr, "expected": "> 1.2"})
    return checks


class Checks(list):
    def add(self, name, passed, measured, expected, **extra):
        self.append({"check_id": name, "status": "PASS" if passed else "FAIL",
                     "measured": measured, "expected": expected, **extra})


def context(printed, spec, ss, policy):
    """Everything the check groups share: placed stand, motor, hardware and envelopes."""
    plate, tower = stand.make_plate(ss), stand.make_tower(ss)
    stationary, bell, boss = stand.motor_references(ss)
    static = {**printed, "motor_plate": plate, "tower_base": tower, "motor_stationary_reference": stationary,
              "motor_rotor_reference": bell, "motor_boss_reference": boss, **winch.hardware(spec, ss)}
    fixed = {k: v for k, v in static.items() if k in ("winch_frame", "winch_deck", "motor_plate", "tower_base",
                                                       "motor_stationary_reference", "m5x20_pulley_bolt", "m5_nylock_nut")
             or k.startswith("m3x16_")}
    return {"printed": printed, "spec": spec, "ss": ss, "static": static, "fixed": fixed,
            "env": winch.rotating_envelopes(spec, ss), "z": winch.levels(spec, ss), "c": winch.centers(spec),
            "zero": policy.volume_relative_tolerance * 1000.0,  # mm^3 boolean noise floor, not a fit allowance
            "tol": policy.linear_tolerance_mm}


def static_checks(ctx):
    checks, static, zero = Checks(), ctx["static"], ctx["zero"]
    for name, part in ctx["printed"].items():
        m = measure(part)
        checks.add(f"{name}.valid_single_solid", m["is_valid"] and m["solid_count"] == 1, m["solid_count"], 1)
    names = list(static)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not threaded(a, b) and boxes_overlap(static[a], static[b]):
                v = common_volume(static[a], static[b])
                checks.add(f"static.{a}.{b}", v <= zero, v, 0.)
    checks.add("static.pairs_evaluated", True, len(names) * (len(names) - 1) // 2, "all pairs with overlapping bounds")
    return checks


def rotating_checks(ctx):
    checks, spec, ss, zero, z = Checks(), ctx["spec"], ctx["ss"], ctx["zero"], ctx["z"]
    printed, fixed, env0 = ctx["printed"], ctx["fixed"], ctx["env"]
    # Each rotating printed part must lie inside its envelope, or the envelope checks prove nothing.
    for group in ("rotor", "shaft_a", "shaft_b"):
        hull = None
        for g, e in env0.values():
            if g == group:
                hull = e if hull is None else hull + e
        for name, axis in winch.PART_AXIS.items():
            if axis == group:
                outside = printed[name].volume - common_volume(printed[name], hull)
                checks.add(f"{name}.inside_rotation_envelope", outside <= zero, outside, 0.)
    for key, (_, env) in grown_envelopes(spec, ss, CLEARANCE_MM).items():
        for name, part in fixed.items():
            v = common_volume(env, part)
            checks.add(f"rotating.{key}.clear_of_{name}_by_{CLEARANCE_MM:g}mm", v <= zero, v, 0.)
    for name, part in fixed.items():
        v = common_volume(printed["pulley_sheave"], part)
        checks.add(f"rotating.pulley_sheave.clear_of_{name}", v <= zero, v, 0.)
    half = grown_envelopes(spec, ss, CLEARANCE_MM / 2)
    keys = list(half)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if half[a][0] == half[b][0] or (a, b) in winch.MESHES or (b, a) in winch.MESHES:
                continue
            v = common_volume(half[a][1], half[b][1])
            checks.add(f"rotating.{a}.{b}_gap_{CLEARANCE_MM:g}mm", v <= zero, v, 0.)
    bell_r = ss.motor_diameter_mm / 2 + ss.rotor_radial_clearance_mm
    above_bell = winch.cyl(bell_r, ss.motor_stationary_height_mm, z["rotor"] + CLEARANCE_MM)
    for key, (group, env) in env0.items():
        if group != "rotor":
            v = common_volume(env, above_bell)
            checks.add(f"rotating.{key}.clear_of_rotor_bell", v <= zero, v, 0.)
    beside_bell = {"rotor_bell": winch.cyl(bell_r, ss.motor_stationary_height_mm, z["rotor"]),
                   "rotor_boss": stand.rotating_keepouts(ss)["rotor_boss"]}
    for name, part in printed.items():
        if name not in winch.PART_AXIS:
            for key, keepout in beside_bell.items():
                v = common_volume(part, keepout)
                checks.add(f"{name}.clear_of_{key}", v <= zero, v, 0.)
    return checks


def drive_checks(ctx, phase_error_deg=0.):
    checks, spec = Checks(), ctx["spec"]
    checks.extend(motion_checks(spec, phase_error_deg))
    checks.add("drive.ratio", math.isclose(spec.ratio, spec.required_ratio, rel_tol=1e-12), spec.ratio, spec.required_ratio)
    rate = winch.rotation_groups(spec)["shaft_b"]["rate"]
    checks.add("drive.output_turns_with_rotor", rate > 0, rate, "> 0")
    return checks


def path_checks(ctx):
    """String run, hanging string and weight travel against every part and envelope; desk edge."""
    checks, spec, ss, zero, z, c = Checks(), ctx["spec"], ctx["ss"], ctx["zero"], ctx["z"], ctx["c"]
    r_eff = spec.drum_groove_radius_mm + spec.string_diameter_mm / 2
    turns = spec.drop_mm / (2 * math.pi * r_eff)
    checks.add("drum.full_drop_within_one_output_turn", turns <= 1 - spec.drum_turn_margin, turns,
               f"<= {1 - spec.drum_turn_margin}")
    x_p, y_p, z_p, *_ = winch.pulley_layout(spec, ss)
    checks.add("string.tangent_height_matches_pulley",
               abs(z["groove"] - (z_p + spec.pulley_groove_radius_mm)) <= ctx["tol"],
               z_p + spec.pulley_groove_radius_mm, z["groove"])
    checks.add("string.tangent_line_matches_pulley_plane",
               abs(c["B"][1] + spec.drum_groove_radius_mm - y_p) <= ctx["tol"], y_p, c["B"][1] + spec.drum_groove_radius_mm)
    rs = spec.string_diameter_mm / 2
    x0 = c["B"][0] + math.sqrt(spec.drum_rim_radius_mm ** 2 - spec.drum_groove_radius_mm ** 2) + 1
    rg = spec.pulley_groove_radius_mm + rs
    entry = math.sqrt(spec.pulley_flange_radius_mm ** 2 - rg ** 2) + 1
    top = z_p - spec.weight_min_hang_mm
    low = top - spec.drop_mm
    segments = {"string_run": winch.x_cyl(rs, x0, x_p - entry, y_p, z["groove"] + rs),
                "string_drop": winch.cyl(rs, low, z_p - entry, x_p + rg, y_p),
                "weight_travel": winch.cyl(spec.weight_envelope_diameter_mm / 2, low - spec.weight_envelope_height_mm,
                                           top, x_p + rg, y_p)}
    obstacles = {**ctx["static"], **{f"envelope_{k}": e for k, (_, e) in ctx["env"].items()}}
    for seg_name, seg in segments.items():
        hits = {name: v for name, part in obstacles.items() if (v := common_volume(seg, part)) > zero}
        checks.add(f"{seg_name}.clear_of_all_parts", not hits, hits, {}, parts_checked=len(obstacles))
    edge = ss.base_x_mm / 2 + spec.desk_edge_margin_mm
    w_min = x_p + rg - spec.weight_envelope_diameter_mm / 2
    checks.add("weight_travel.beyond_base_edge", w_min >= edge, w_min, f">= {edge}")
    return checks


def interface_checks(ctx):
    """Fastener engagement, shaft support, magnet holder and encoder envelope."""
    checks, spec, ss, zero, z = Checks(), ctx["spec"], ctx["ss"], ctx["zero"], ctx["z"]
    plate_t = stand.plate_z(ss)[1] - stand.plate_z(ss)[0]
    e = spec.plate_screw_length_mm - spec.frame_thickness_mm - plate_t
    checks.add("plate_screw.engagement_in_tower_mm", 4 <= e <= ss.plate_screw_pilot_depth_mm - 1, e,
               f"4 <= e <= {ss.plate_screw_pilot_depth_mm - 1}")
    e = spec.deck_screw_length_mm - spec.deck_thickness_mm
    checks.add("deck_screw.engagement_in_column_mm", 5 <= e <= spec.column_pilot_depth_mm - 1, e,
               f"5 <= e <= {spec.column_pilot_depth_mm - 1}")
    checks.add("rotor_screw.engagement_mm", 0 < spec.rotor_screw_engagement_mm <= spec.rotor_thread_depth_mm,
               spec.rotor_screw_engagement_mm, f"0 < e <= {spec.rotor_thread_depth_mm}")
    w = spec.bearing_width_mm
    for key, top_z in (("a", z["shaft_a_top"]), ("b", z["shaft_b_top"])):
        lo, hi = top_z - spec.shaft_length_mm, top_z
        checks.add(f"shaft_{key}.spans_both_bearings", lo <= z["frame1"] - w and hi >= z["deck0"] + w,
                   [lo, hi], [z["frame1"] - w, z["deck0"] + w])
    engaged = z["shaft_b_top"] - z["holder0"]
    checks.add("shaft_b.magnet_holder_engagement_mm", math.isclose(engaged, spec.magnet_holder_shaft_engagement_mm),
               engaged, spec.magnet_holder_shaft_engagement_mm)
    enc = winch.encoder_envelope(spec, ss)
    for name, part in ctx["fixed"].items():
        v = common_volume(enc, part)
        checks.add(f"encoder_envelope.clear_of_{name}", v <= zero, v, 0.)
    return checks


def inspect_winch(printed, spec, ss, policy, phase_error_deg=0.):
    """Independent interference, clearance, mesh, string-path and interface checks."""
    ctx = context(printed, spec, ss, policy)
    checks = [*static_checks(ctx), *rotating_checks(ctx), *drive_checks(ctx, phase_error_deg),
              *path_checks(ctx), *interface_checks(ctx)]
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks}


REVIEW_GROUPS = {"stand": ("motor_plate", "tower_base"), "motor": ("motor_",),
                 "load": ("string_", "weight_"),
                 "hardware": ("bearing_", "shaft_", "m25", "m3", "m5", "magnet_6")}


def review_group(name, printable):
    """Viewer toggle group. Printed winch parts first, then the existing stand, then the rest."""
    if name in printable:
        return "printed"
    for group, prefixes in REVIEW_GROUPS.items():
        if name.startswith(prefixes):
            return group
    return "printed"


# Print orientation per part: transform applied to the assembled shape before grounding.
def print_transform(name, spec, ss):
    if name in ("rotor_gear", "winch_deck"):
        return Rot(180, 0, 0)
    if name == "pulley_sheave":
        x_p, y_p, z_p, *_ = winch.pulley_layout(spec, ss)
        return Rot(-90, 0, 0) * Pos(-x_p, -y_p, -z_p)
    return Pos(0, 0, 0)


def grounded(shape):
    box = shape.bounding_box()
    return Pos(-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z) * shape


def create_review(stage, spec, meshes):
    template = Path(__file__).with_name("winch_viewer.html").read_text()
    payload = [{**m, "data": base64.b64encode((stage / "review_meshes" / f"{m['name']}.stl").read_bytes()).decode()}
               for m in meshes]
    r_eff = spec.drum_groove_radius_mm + spec.string_diameter_mm / 2
    motion = {"ratio": spec.ratio, "drop_mm": spec.drop_mm, "r_eff_mm": r_eff}
    (stage / "review.html").write_text(template.replace("__MESH_DATA__", json.dumps(payload))
                                       .replace("__MOTION__", json.dumps(motion))
                                       .replace("__TITLE__", f"{spec.project_id} — {spec.ratio:g}:1, {spec.drop_mm:g} mm drop"))


def build(root, spec, spec_path, output):
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    policy_path = root / "validation/release_policy.yaml"
    policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    stand_path = root / spec.stand_spec
    ss = load_spec(stand_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".winch-", dir=output.parent))
    try:
        printed = winch.make_printed(spec, ss)
        report = inspect_winch(printed, spec, ss, policy)
        checks = report["checks"]
        (stage / "parts").mkdir(); (stage / "print").mkdir(); (stage / "review_meshes").mkdir()
        records = []
        for name, shape in printed.items():
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
                           "measured": reopened, "expected": native})
            placed = grounded(print_transform(name, spec, ss) * shape)
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
                            "volume_mm3": native["volume_mm3"], "print_size_mm": expected["dimensions_mm"]})
        stationary, bell, boss = stand.motor_references(ss)
        plate, tower = stand.make_plate(ss), stand.make_tower(ss)
        plate.label, tower.label = "motor_plate", "tower_base"
        references = [plate, tower, stationary, bell, boss, *winch.hardware(spec, ss).values(),
                      *winch.string_and_weight(spec, ss)]
        rates = winch.rotation_groups(spec)
        bolt_axis = {"bearing_625_pulley": "sheave", "shaft_a_d5x100": "shaft_a", "shaft_b_d5x100": "shaft_b",
                     "m3x4_set_screw_a": "shaft_a", "m3_nut_a": "shaft_a", "m3x4_set_screw_b": "shaft_b",
                     "m3_nut_b": "shaft_b", "magnet_6x2_5_diametric": "shaft_b",
                     "motor_rotor_reference": "rotor", "motor_boss_reference": "rotor"}
        weight_top = winch.pulley_layout(spec, ss)[2] - spec.weight_min_hang_mm - spec.drop_mm
        meshes = []
        for shape in [*printed.values(), *references]:
            name = shape.label
            if not export_stl(shape, stage / "review_meshes" / f"{name}.stl", tolerance=0.03, angular_tolerance=0.15):
                raise ValueError(f"review mesh export failed: {name}")
            axis = winch.PART_AXIS.get(name) or bolt_axis.get(name) or (
                "rotor" if name.startswith("m25x6_rotor") else None)
            rot = rates[axis] if axis else None
            meshes.append({"name": name, "color": list(shape.color)[:3], "group": review_group(name, printed),
                           "axis": rot["axis"] if rot else None, "center": list(rot["center"]) if rot else [0, 0],
                           "center_z": winch.pulley_layout(spec, ss)[2] if axis == "sheave" else 0,
                           "rate": rot["rate"] if rot else 0, "slide": name == "weight_lowest",
                           "clip_z": weight_top if name == "string_drop" else None})
        create_review(stage, spec, meshes)
        assembly = Compound(label=spec.project_id, children=list(printed.values()))
        export_step(assembly, stage / "assembly.step", unit=Unit.MM)
        exported, native = measure(import_step(stage / "assembly.step")), measure(assembly)
        good = exported["is_valid"] and exported["solid_count"] == len(printed) and math.isclose(
            exported["volume_mm3"], native["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        checks.append({"check_id": "assembly_step_roundtrip", "status": "PASS" if good else "FAIL",
                       "measured": exported, "expected": native})
        geometry = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
                    "scope": "bldc_winch_development_geometry", "checks": checks,
                    "policy_sha256": sha256(policy_path)}
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise ValueError("winch checks failed; see geometry_report.json")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(stand_path, stage / "stand_specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        from .build import environment
        manifest = {"schema_version": 1, "project_id": spec.project_id, "status": "PASS",
                    "scope": "development_build", "release_status": "BLOCKED", "length_unit": "mm",
                    "source": source_identity(root), "environment": environment(), "parts": records,
                    "specification_sha256": sha256(spec_path), "stand_specification_sha256": sha256(stand_path),
                    "policy_sha256": sha256(policy_path),
                    "limitations": ["Bearings, D-shafts, screws, magnet and weights are seller nominals; none measured.",
                                    "Gear teeth are not load rated; the motor can exceed what printed teeth carry. "
                                    "Limit driver current before any powered test.",
                                    f"Rotating clearances are checked at {CLEARANCE_MM:g} mm against envelopes; "
                                    "45-degree drum cones get about 0.7 mm normal margin.",
                                    "Magnet gap depends on Jamie's standoff choice; not set by this design.",
                                    "Printed holes carry no process compensation. No release or print approval."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "bldc_winch_development_build",
                "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)), "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
