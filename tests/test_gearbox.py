from pathlib import Path
import math
import pytest
from pydantic import ValidationError
from mech_lab.schema import load_spec, readiness
from cad.assemblies.gearbox import layout, phases
from cad.parts.spur_gear import gear_face, profile_points
from mech_lab.gearbox_checks import motion_check, collision_checks
from mech_lab.geometry import GeometryPolicy


@pytest.fixture
def spec():
    return load_spec(Path("specs/gearbox_v1.yaml"))


def test_gearbox_schema_and_release_boundary(spec):
    assert not readiness(spec,"build")
    assert readiness(spec,"release")
    with pytest.raises(ValidationError):
        type(spec).model_validate({**spec.model_dump(),"shaft_diametral_clearance_mm":0.})
    with pytest.raises(ValidationError):
        type(spec).model_validate({**spec.model_dump(),"trial_assumptions_authorized":False})


def test_compound_layout_ratio_and_absolute_phases():
    assert phases()==pytest.approx([0,177,198,111])
    assert [math.dist(a,b) for a,b in zip(layout(),layout()[1:])]==pytest.approx([40]*3)
    assert (-20/60)**3==pytest.approx(-1/27)


@pytest.mark.parametrize("teeth",[20,60])
def test_involute_profile_has_correct_tip_count_and_radius(teeth):
    from shapely import Polygon
    from math import hypot
    points=profile_points(teeth)
    assert Polygon(points).is_valid
    assert max(hypot(x,y) for x,y in points)==pytest.approx(teeth/2+1)
    face=gear_face(teeth)
    assert face.is_valid
    assert len(face.outer_wire().edges())==(6 if teeth==20 else 4)*teeth
    assert abs(face.area-Polygon(points).area)<0.01


def test_full_pitch_motion_and_wrong_phasing(spec):
    correct=motion_check(spec)
    assert correct["status"]=="PASS"
    assert min(c["continuous_gap_lower_bound_mm"] for c in correct["checks"][:3])>0
    defect=motion_check(spec,phase_error_deg=3.)
    assert defect["status"]=="FAIL"
    assert all(c["maximum_intersection_area_mm2"]>0 for c in defect["checks"][:3])


def test_collision_empty_contact_and_multisolid_intersection():
    from build123d import Box, Compound, Pos
    from mech_lab.schema import load_yaml
    policy=GeometryPolicy.model_validate(load_yaml(Path("validation/release_policy.yaml"))["geometry"])
    a=Box(10,10,10)
    for x,status in ((10.,"PASS"),(9.,"FAIL")):
        checks=collision_checks({"a":a,"b":Pos(x,0,0)*a},Compound(),policy)
        assert checks[0]["status"]==status
    checks=collision_checks({"a":a,"b":Compound(children=[Pos(-3,0,0)*Box(1,1,1),Pos(3,0,0)*Box(1,1,1)])},Compound(),policy)
    assert checks[0]["status"]=="FAIL"
    assert checks[0]["common_volume_mm3"]==pytest.approx(2.)


def test_mesh_zero_normalization_does_not_hide_a_hole(tmp_path):
    import struct
    from build123d import Cylinder, Pos, export_stl
    from mech_lab.gearbox_checks import mesh_manifold,normalize_stl_zeros
    shape=Pos(77,37,26.3)*(Cylinder(5,2)-Cylinder(1.7,2))
    shape=Pos(-77,-37,-25.3)*shape
    path=tmp_path/"ring.stl"; export_stl(shape,path)
    normalized=normalize_stl_zeros(path,1e-9)
    assert normalized["maximum_coordinate_change_mm"]<1e-9
    assert mesh_manifold(path)["status"]=="PASS"
    data=bytearray(path.read_bytes()); count=struct.unpack_from("<I",data,80)[0]
    struct.pack_into("<I",data,80,count-1); path.write_bytes(data[:-50])
    normalize_stl_zeros(path,1e-9)
    assert mesh_manifold(path)["status"]=="FAIL"


VENDOR_STEP=Path("components/drawings/waveshare_st3215/ST3215.step")


@pytest.mark.skipif(not VENDOR_STEP.exists(),
                    reason="vendor ST3215 STEP is not redistributed; see components/drawings/README.md")
def test_purchased_servo_keepout_roundtrip_and_horn_datums(tmp_path,spec):
    from build123d import Compound,Pos,Rot,export_step,import_step
    from cad.standard_components.servo_reference import load_servo_reference
    report={}; servo=Pos(62.5,37,44.6)*Rot(-90,0,0)*load_servo_reference(spec.servo_step,report)
    horn=servo.solids()[report["front_horn_solid_index"]]
    assert list(horn.bounding_box().size)==pytest.approx([19.2,19.2,4.5])
    assert horn.bounding_box().min.Z==pytest.approx(35.)
    assembly=Compound(children=[servo]); path=tmp_path/"servo.step"; export_step(assembly,path)
    loaded=import_step(path)
    assert loaded.is_valid and len(loaded.solids())==3
    assert loaded.volume==pytest.approx(assembly.volume,rel=1e-8)
    assert report["raw_source_geometry_status"]=="FAIL"
