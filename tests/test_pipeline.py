import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from mech_lab.build import build, GeometryFailure
from mech_lab.io import input_path, output_path, sha256
from mech_lab.review import render

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    for name in ("specs", "validation"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copyfile(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def test_build_export_roundtrip_and_review(project):
    out = project / "builds/smoke"
    result = build(project, project / "specs/smoke_test.yaml", out)
    assert result["status"] == "PASS"
    manifest = json.loads((out / "build_manifest.json").read_text())
    assert manifest["release_status"] == "BLOCKED"
    assert manifest["length_unit"] == "mm"
    assert manifest["source"]["source_sha256"]
    for name, digest in manifest["artifacts"].items():
        assert sha256(out / name) == digest
    report = json.loads((out / "geometry_report.json").read_text())
    assert report["measurements"]["volume_mm3"] == pytest.approx(1000)
    assert all(check["status"] == "PASS" for check in report["checks"])
    views = project / "builds/views"
    assert render(project, out / "build_manifest.json", views)["views"] == 4
    assert len(list(views.glob("*.svg"))) == 4
    with pytest.raises(ValueError, match="exists"):
        build(project, project / "specs/smoke_test.yaml", out)
    (out / "assembly.step").write_text("tampered")
    with pytest.raises(ValueError, match="checksum"):
        render(project, out / "build_manifest.json", project / "builds/other_views")


def test_failed_model_preserves_diagnostics(project, monkeypatch):
    def failed_operation(_):
        raise RuntimeError("seeded boolean/fillet operation failure")
    monkeypatch.setattr("mech_lab.build.make_smoke_part", failed_operation)
    output = project / "builds/bad"
    with pytest.raises(GeometryFailure, match="seeded boolean/fillet"):
        build(project, project / "specs/smoke_test.yaml", output)
    assert not output.exists()
    failures = list((project / "builds").glob(".candidate-*/failure.json"))
    assert len(failures) == 1
    assert json.loads(failures[0].read_text())["status"] == "FAIL"


def test_paths_cannot_escape_project(project, tmp_path):
    with pytest.raises(ValueError):
        output_path(project, "releases/unauthorized")
    with pytest.raises(ValueError):
        output_path(project, "builds/../../escape")
    with pytest.raises(ValueError):
        input_path(project, "../outside.yaml")
    (project / "builds").symlink_to(project / "specs", target_is_directory=True)
    with pytest.raises(ValueError):
        output_path(project, "builds/overwritten.yaml")


def test_cli_blocked_is_nonzero_and_machine_readable(project):
    code = "from mech_lab.cli import validate_spec; validate_spec()"
    result = subprocess.run([sys.executable, "-c", code, "specs/finger_joint_v1.yaml"],
                            cwd=project, capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "BLOCKED"


def test_cli_timeout_is_failure(project):
    code = "from mech_lab.cli import build_design; build_design()"
    result = subprocess.run([sys.executable, "-c", code, "specs/smoke_test.yaml",
                             "--output", "builds/timeout", "--timeout", "0.000001"],
                            cwd=project, capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert json.loads(result.stdout)["exception_type"] == "TimeoutExpired"
    assert not (project / "builds/timeout/build_manifest.json").exists()
