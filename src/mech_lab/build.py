from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
import platform
import shutil
import tempfile

from build123d import Compound, Unit, export_step, export_stl, import_step

from cad.interfaces.features import Frame
from cad.parts.smoke_test import make_smoke_part
from cad.parts.cube_sphere import make_cube_sphere
from .geometry import GeometryPolicy, inspect, stl_bounds
from .io import atomic_json, sha256, source_identity
from .schema import BldcStandSpec, BldcWinchSpec, CubeSphereSpec, GearboxSpec, IndicatorDiscSpec, load_spec, load_yaml, readiness


class BuildBlocked(ValueError):
    pass


class GeometryFailure(ValueError):
    pass


def register_part(registry, part_id, shape):
    if part_id in registry:
        raise ValueError(f"duplicate part ID: {part_id}")
    if shape is None or shape.wrapped is None:
        raise GeometryFailure(f"empty part: {part_id}")
    registry[part_id] = shape


def environment():
    return {"python": platform.python_version(), "architecture": platform.machine(),
            "platform": platform.platform(), "packages": {
                name: version(name) for name in
                ("build123d", "cadquery-ocp-novtk", "ocp-vscode", "pydantic", "pyyaml")}}


def build(root, spec_path, output):
    spec = load_spec(spec_path)
    blocked = readiness(spec, "build")
    if blocked:
        raise BuildBlocked("; ".join(blocked))
    if isinstance(spec, GearboxSpec):
        from .gearbox_build import build as build_gearbox
        return build_gearbox(root,spec,spec_path,output)
    if isinstance(spec, IndicatorDiscSpec):
        from .disc_build import build as build_disc
        return build_disc(root, spec, spec_path, output)
    if isinstance(spec, BldcWinchSpec):
        from .winch_build import build as build_winch
        return build_winch(root, spec, spec_path, output)
    if isinstance(spec, BldcStandSpec):
        from .stand_build import build as build_stand
        return build_stand(root, spec, spec_path, output)
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    policy_path = root / "validation/release_policy.yaml"
    policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".candidate-", dir=output.parent))
    try:
        registry = {}
        part_id = "cube_sphere" if isinstance(spec, CubeSphereSpec) else "smoke_block"
        expectations = spec if isinstance(spec, CubeSphereSpec) else spec.dimensions
        try:
            shape = make_cube_sphere(spec) if isinstance(spec, CubeSphereSpec) else make_smoke_part(spec.dimensions)
            register_part(registry, part_id, shape)
        except Exception as exc:
            raise GeometryFailure(f"part construction failed: {exc}") from exc
        part = registry[part_id]
        geometry = inspect(part, expectations, policy)
        if geometry["status"] != "PASS":
            atomic_json(stage / "geometry_report.json", geometry)
            raise GeometryFailure("constructed geometry fails checks; see diagnostic directory")
        (stage / "parts").mkdir()
        for name, shape in registry.items():
            if not export_step(shape, stage / "parts" / f"{name}.step", unit=Unit.MM):
                raise GeometryFailure("STEP export failed")
            if not export_stl(shape, stage / "parts" / f"{name}.stl",
                              tolerance=policy.stl_linear_deflection_mm,
                              angular_tolerance=policy.stl_angular_deflection_rad):
                raise GeometryFailure("STL export failed")
        # build123d 0.11.1 cannot export an individual child after parenting it.
        assembly = Compound(label=spec.project_id, children=list(registry.values()))
        if not export_step(assembly, stage / "assembly.step", unit=Unit.MM):
            raise GeometryFailure("assembly STEP export failed")
        roundtrip = inspect(import_step(stage / f"parts/{part_id}.step"), expectations,
                            policy, "step_roundtrip")
        assembly_check = inspect(import_step(stage / "assembly.step"), expectations,
                                 policy, "assembly_roundtrip")
        mesh = stl_bounds(stage / f"parts/{part_id}.stl")
        # STL stores float32 coordinates. This is export precision, not fit tolerance.
        expected = [spec.dimensions.x_mm, spec.dimensions.y_mm, spec.dimensions.z_mm]
        mesh_tolerance = max(policy.linear_tolerance_mm, max(expected) * 1.2e-7)
        mesh_ok = all(abs(a - b) <= mesh_tolerance for a, b in zip(mesh["dimensions_mm"], expected))
        mesh_ok = mesh_ok and all(abs(v) <= mesh_tolerance for v in mesh["minimum_mm"])
        geometry["checks"].extend(roundtrip["checks"] + assembly_check["checks"])
        geometry["checks"].append({"check_id": "stl_bounds", "status": "PASS" if mesh_ok else "FAIL",
                                   "measured": mesh, "tolerance_mm": mesh_tolerance,
                                   "limitations": ["bounds check does not establish mesh manifoldness"]})
        if not mesh_ok or roundtrip["status"] != "PASS" or assembly_check["status"] != "PASS":
            geometry["status"] = "FAIL"
        geometry["policy_sha256"] = sha256(policy_path)
        atomic_json(stage / "geometry_report.json", geometry)
        if geometry["status"] != "PASS":
            raise GeometryFailure("export round-trip verification failed")
        shutil.copyfile(spec_path, stage / "specification.yaml")
        shutil.copyfile(policy_path, stage / "release_policy.yaml")
        manifest = {"schema_version": 1, "project_id": spec.project_id,
                    "status": "PASS", "scope": "development_build", "release_status": "BLOCKED",
                    "length_unit": "mm", "specification_sha256": sha256(spec_path),
                    "policy_sha256": sha256(policy_path), "source": source_identity(root),
                    "environment": environment(), "frames": [asdict(Frame("world"))],
                    "parts": [{"id": name, "frame_id": "world", "step": f"parts/{name}.step",
                               "mesh": f"parts/{name}.stl"} for name in registry],
                    "limitations": ["No release or print authorization.",
                        "STL coordinates use millimeters by manifest convention; verify slicer import scale.",
                        "Desktop commissioning evidence is recorded separately from this build."],
                    "artifacts": {str(p.relative_to(stage)): sha256(p)
                                  for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "build_manifest.json", manifest)
        stage.rename(output)
        return {"status": "PASS", "scope": "development_build", "output": str(output.relative_to(root)),
                "manifest": str((output / "build_manifest.json").relative_to(root)),
                "release_status": "BLOCKED"}
    except Exception as exc:
        atomic_json(stage / "failure.json", {"status": "FAIL", "error": str(exc),
                                             "exception_type": type(exc).__name__})
        raise GeometryFailure(f"{exc}; diagnostics: {stage.relative_to(root)}") from exc
