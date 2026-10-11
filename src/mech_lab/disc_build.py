"""Development build for the rotor indicator disc: body plus inlaid marker solids."""
import math
from pathlib import Path
import shutil
import tempfile

from build123d import Compound, Pos, Rot, Unit, export_step, export_stl, import_step
from cad.parts.indicator_disc import make_body, make_markers, marker_centers, shape_area
from .gearbox_checks import mesh_manifold, normalize_stl_zeros
from .geometry import GeometryPolicy, measure, stl_bounds
from .io import atomic_json, sha256, source_identity
from .schema import load_yaml


def holed_disc_volume(spec):
    """Analytic volume of the disc with bore and countersunk holes, markers filled in."""
    R, t = spec.diameter_mm / 2, spec.thickness_mm
    r, s = spec.screw_clearance_mm / 2, spec.countersink_diameter_mm / 2
    d = s - r
    per_hole = math.pi * r * r * t + math.pi * d / 3 * (s * s + s * r + r * r) - math.pi * r * r * d
    return math.pi * (R * R - (spec.center_hole_mm / 2) ** 2) * t - len(spec.screw_angles_deg) * per_hole


def inspect_disc(body, markers, spec, policy):
    """Independent geometry checks; markers must exactly fill their pockets at the right angles."""
    checks = []

    def check(name, passed, measured, expected):
        checks.append({"check_id": name, "status": "PASS" if passed else "FAIL",
                       "measured": measured, "expected": expected})

    tol, rel = policy.linear_tolerance_mm, policy.volume_relative_tolerance
    t, depth = spec.thickness_mm, spec.marker_depth_mm
    m = measure(body)
    check("body.valid_single_solid", m["is_valid"] and m["solid_count"] == 1, m["solid_count"], 1)
    expected_size = [spec.diameter_mm, spec.diameter_mm, t]
    check("body.envelope_mm", all(abs(a - b) <= tol for a, b in zip(m["dimensions_mm"], expected_size))
          and abs(m["minimum_mm"][2]) <= tol, m["dimensions_mm"], expected_size)
    check("marker.count", len(markers) == len(spec.marker_shapes), len(markers), len(spec.marker_shapes))
    marker_total = 0.
    for marker, kind, angle, center in zip(markers, spec.marker_shapes, spec.marker_angles_deg,
                                           marker_centers(spec)):
        mm = measure(marker)
        name = f"marker_{angle:g}deg_{kind}"
        check(f"{name}.valid_single_solid", mm["is_valid"] and mm["solid_count"] == 1, mm["solid_count"], 1)
        z = [mm["minimum_mm"][2], mm["maximum_mm"][2]]
        check(f"{name}.flush_depth_mm", abs(z[0] - (t - depth)) <= tol and abs(z[1] - t) <= tol, z, [t - depth, t])
        volume = shape_area(kind, spec.marker_size_mm) * depth
        check(f"{name}.volume_mm3", math.isclose(mm["volume_mm3"], volume, rel_tol=rel), mm["volume_mm3"], volume)
        c = marker.center()
        check(f"{name}.position_mm", math.dist((c.X, c.Y), center) <= tol, [c.X, c.Y], list(center))
        overlap = (body & marker).volume
        check(f"{name}.no_body_overlap", overlap <= rel * volume, overlap, 0.)
        marker_total += mm["volume_mm3"]
    filled, target = m["volume_mm3"] + marker_total, holed_disc_volume(spec)
    check("body_plus_markers.fills_disc_mm3", math.isclose(filled, target, rel_tol=rel), filled, target)
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
            "checks": checks, "body": m}


def build(root, spec, spec_path, output):
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    policy_path = root / "validation/release_policy.yaml"
    policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".disc-", dir=output.parent))
    try:
        body, markers = make_body(spec), make_markers(spec)
        report = inspect_disc(body, markers, spec, policy)
        checks = report["checks"]
        parts = {"indicator_disc_body": body,
                 "indicator_disc_markers": Compound(label="indicator_disc_markers", children=markers)}
        (stage / "parts").mkdir(); (stage / "print").mkdir()
        # Print marker face down: rotate 180 degrees about X, then ground. Both bodies share
        # one transform so their relative placement is preserved for multi-filament slicing.
        to_print = Pos(0, 0, spec.thickness_mm) * Rot(180, 0, 0)
        records = []
        for name, shape in parts.items():
            native = measure(shape)
            step = stage / "parts" / f"{name}.step"
            if not export_step(shape, step, unit=Unit.MM):
                raise ValueError(f"STEP export failed: {name}")
            reopened = measure(import_step(step))
            same = reopened["is_valid"] and reopened["solid_count"] == native["solid_count"] and math.isclose(
                native["volume_mm3"], reopened["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
            same = same and all(abs(a - b) <= policy.linear_tolerance_mm for key in ("minimum_mm", "maximum_mm")
                                for a, b in zip(native[key], reopened[key]))
            checks.append({"check_id": f"{name}.step_roundtrip", "status": "PASS" if same else "FAIL",
                           "measured": reopened})
            placed = to_print * shape
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
            records.append({"id": name, "step": f"parts/{name}.step", "mesh": f"print/{name}.stl",
                            "print_transform": "rotate 180 deg about X, translate +Z by thickness",
                            "volume_mm3": native["volume_mm3"], "solids": native["solid_count"]})
        assembly = Compound(label=spec.project_id, children=[body, *markers])
        export_step(assembly, stage / "assembly.step", unit=Unit.MM)
        exported, native = measure(import_step(stage / "assembly.step")), measure(assembly)
        good = exported["is_valid"] and exported["solid_count"] == native["solid_count"] and math.isclose(
            exported["volume_mm3"], native["volume_mm3"], rel_tol=policy.volume_relative_tolerance)
        checks.append({"check_id": "assembly_step_roundtrip", "status": "PASS" if good else "FAIL",
                       "measured": exported, "expected": native})
        geometry = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
                    "scope": "indicator_disc_development_geometry", "checks": checks,
                    "policy_sha256": sha256(policy_path)}
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise ValueError("indicator disc checks failed; see geometry_report.json")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        from .build import environment
        manifest = {"schema_version": 1, "project_id": spec.project_id, "status": "PASS",
                    "scope": "development_build", "release_status": "BLOCKED", "length_unit": "mm",
                    "source": source_identity(root), "environment": environment(), "parts": records,
                    "specification_sha256": sha256(spec_path), "policy_sha256": sha256(policy_path),
                    "limitations": ["Rotor hole pattern and thread depth are supplier nominals, not measured.",
                                    "Marker STL is a multi-solid second-filament body; slice both meshes together.",
                                    "No release or print approval."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "indicator_disc_development_build",
                "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)), "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
