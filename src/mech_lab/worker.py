"""Private subprocess boundary for kernel failures/timeouts."""
from contextlib import redirect_stdout
import json
from pathlib import Path
import plistlib
import sys


def run():
    from .io import root_dir
    root = root_dir()
    task, *arguments = sys.argv[1:]
    if task == "build":
        from .build import build
        return build(root, Path(arguments[0]), Path(arguments[1]))
    if task == "render":
        from .review import render
        return render(root, Path(arguments[0]), Path(arguments[1]))
    if task == "inspect":
        from build123d import import_step
        from .geometry import GeometryPolicy, inspect
        from .io import sha256
        from .schema import CubeSphereSpec, load_spec, load_yaml, SmokeSpec
        spec = load_spec(Path(arguments[1]))
        if not isinstance(spec, (SmokeSpec, CubeSphereSpec)):
            return {"status": "BLOCKED", "scope": "inspection", "blockers": ["only smoke-test inspection is implemented"]}
        policy_path = root / "validation/release_policy.yaml"
        policy = GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
        expected = spec if isinstance(spec, CubeSphereSpec) else spec.dimensions
        result = inspect(import_step(arguments[0]), expected, policy)
        result.update({"policy_sha256": sha256(policy_path), "step_sha256": sha256(Path(arguments[0])),
                       "specification_sha256": sha256(Path(arguments[1])), "scope": "smoke_geometry"})
        return result
    if task == "environment":
        from .build import environment
        apps = {}
        for name in ("Visual Studio Code", "FreeCAD", "BambuStudio", "Bambu Studio"):
            paths = [base / f"{name}.app/Contents/Info.plist"
                     for base in (Path("/Applications"), Path.home() / "Applications")]
            found = next((p for p in paths if p.exists()), None)
            info = plistlib.loads(found.read_bytes()) if found else {}
            apps[name] = {"found": found is not None,
                          "version": info.get("CFBundleShortVersionString") or info.get("CFBundleVersion"),
                          "path": str(found.parent.parent) if found else None}
        return {"status": "PASS", "scope": "environment_inventory", **environment(), "applications": apps,
                "limitations": ["Inventory is not application commissioning.",
                    "Printer/nozzle/material configuration has not been verified."]}
    raise ValueError(f"unknown worker task: {task}")


if __name__ == "__main__":
    try:
        with redirect_stdout(sys.stderr):
            result = run()
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "exception_type": type(exc).__name__}
    print(json.dumps(result, allow_nan=False))
    sys.exit({"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["status"]])
