from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mech_lab.schema import SPEC, load_spec, load_yaml, readiness

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def smoke():
    return load_yaml(ROOT / "specs/smoke_test.yaml")


@pytest.mark.parametrize("key,value", [
    ("length_unit", "inch"), ("schema_version", 2), ("project_id", "../escape"),
    ("release_class", "functional_prototype"), ("unknown", True),
])
def test_reject_invalid_contract(smoke, key, value):
    smoke[key] = value
    with pytest.raises(ValidationError):
        SPEC.validate_python(smoke)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), "10", True])
def test_reject_invalid_dimensions(smoke, value):
    smoke["dimensions"]["x_mm"] = value
    with pytest.raises(ValidationError):
        SPEC.validate_python(smoke)


def test_missing_units(smoke):
    del smoke["length_unit"]
    with pytest.raises(ValidationError):
        SPEC.validate_python(smoke)


def test_joint_unknowns_are_preserved_and_block_build():
    spec = load_spec(ROOT / "specs/finger_joint_v1.yaml")
    assert spec.requirements.continuous_torque_nm is None
    assert readiness(spec, "schema") == []
    assert "components.shaft is unresolved" in readiness(spec, "build")
    assert "assumption A001 is proposed" in readiness(spec, "build")


def test_smoke_never_grants_release(smoke):
    spec = SPEC.validate_python(smoke)
    assert readiness(spec, "build") == []
    assert readiness(spec, "release")


@pytest.mark.parametrize("change", ["approval", "review", "torque", "range", "duplicate"])
def test_joint_contradictions(change):
    data = load_yaml(ROOT / "specs/finger_joint_v1.yaml")
    if change == "approval":
        data["assumptions"][0]["approval_state"] = "approved"
    elif change == "review":
        data["release_controls"]["human_print_approval_required"] = False
    elif change == "torque":
        data["requirements"].update(continuous_torque_nm=2.0, peak_torque_nm=1.0)
    elif change == "range":
        data["requirements"]["joint_range_deg"] = [90.0, 0.0]
    else:
        data["assumptions"].append(deepcopy(data["assumptions"][0]))
    with pytest.raises(ValidationError):
        SPEC.validate_python(data)


def test_duplicate_yaml_keys(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text("length_unit: mm\nlength_unit: inch\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_yaml(path)
