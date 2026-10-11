"""Validated development artifact build for the approved gearbox trial."""
import json
import math
from pathlib import Path
import shutil
import tempfile
from build123d import Compound, Pos, Unit, export_step, export_stl, import_step
from cad.assemblies.gearbox import build_parts, layout, phases
from .geometry import GeometryPolicy, measure, stl_bounds
from .gearbox_checks import collision_checks, motion_check, mesh_manifold, normalize_stl_zeros
from .io import atomic_json, input_path, sha256, source_identity
from .schema import load_yaml


def build(root,spec,spec_path,output):
    if output.exists():
        raise ValueError("output already exists; choose a new build directory")
    servo_path=input_path(root,spec.servo_step)
    if sha256(servo_path)!=spec.servo_step_sha256:
        raise ValueError("servo STEP reference checksum mismatch")
    policy_path=root/"validation/release_policy.yaml"
    policy=GeometryPolicy.model_validate(load_yaml(policy_path)["geometry"])
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".gearbox-",dir=output.parent))
    try:
        reference_report={}
        parts,servo=build_parts(spec,reference_report)
        atomic_json(stage/"servo_reference_report.json",reference_report)
        (stage/"parts").mkdir(); (stage/"print").mkdir(); (stage/"review_meshes").mkdir()
        checks=[]; records=[]
        for name,shape in parts.items():
            m=measure(shape)
            ok=m["is_valid"] and m["solid_count"]==1 and m["volume_mm3"]>0
            checks.append({"check_id":f"{name}.solid", "status":"PASS" if ok else "FAIL", "measured":m})
            if not ok:
                raise ValueError(f"invalid printable solid {name}")
            step=stage/"parts"/f"{name}.step"
            if not export_step(shape,step,unit=Unit.MM):
                raise ValueError(f"STEP export failed: {name}")
            reopened=measure(import_step(step))
            same=reopened["is_valid"] and reopened["solid_count"]==1 and math.isclose(
                m["volume_mm3"],reopened["volume_mm3"],rel_tol=policy.volume_relative_tolerance)
            same=same and all(abs(a-b)<=policy.linear_tolerance_mm for key in ("minimum_mm","maximum_mm") for a,b in zip(m[key],reopened[key]))
            checks.append({"check_id":f"{name}.step_roundtrip","status":"PASS" if same else "FAIL","measured":reopened})
            # Stable ground-plane STL per printable part, without manufacturing compensation.
            bb=shape.bounding_box(); offset=(-bb.center().X,-bb.center().Y,-bb.min.Z)
            placed=Pos(*offset)*shape
            mesh=stage/"print"/f"{name}.stl"
            if not export_stl(placed,mesh,tolerance=policy.stl_linear_deflection_mm,
                              angular_tolerance=policy.stl_angular_deflection_rad):
                raise ValueError(f"STL export failed: {name}")
            normalization=normalize_stl_zeros(mesh,policy.linear_tolerance_mm*0.001)
            checks.append({"check_id":f"{name}.stl_zero_normalization",**normalization})
            bounds=stl_bounds(mesh)
            # Curved extrema can be inside analytic bounds by the specified tessellation deflection.
            tol=policy.stl_linear_deflection_mm+max(m["dimensions_mm"])*1.2e-7
            good=abs(bounds["minimum_mm"][2])<1e-5 and all(abs(a-b)<=2*tol for a,b in zip(bounds["dimensions_mm"],m["dimensions_mm"]))
            checks.append({"check_id":f"{name}.stl_scale_and_ground","status":"PASS" if good else "FAIL","measured":bounds})
            checks.append({"check_id":f"{name}.stl_manifold",**mesh_manifold(mesh)})
            if not export_stl(shape,stage/"review_meshes"/f"{name}.stl",tolerance=0.04,angular_tolerance=0.15):
                raise ValueError(f"review mesh export failed: {name}")
            records.append({"id":name,"step":f"parts/{name}.step","mesh":f"print/{name}.stl",
                            "print_translation_mm":offset,"volume_mm3":m["volume_mm3"],"color":list(shape.color)})
        static=collision_checks(parts,servo,policy)
        checks.extend(static)
        motion=motion_check(spec)
        checks.extend(motion["checks"])
        atomic_json(stage/"motion_report.json",motion)
        from .gearbox_checks import rotating_clearance_checks
        checks.extend(rotating_clearance_checks(parts,servo,spec,policy))
        for i,(point,angle) in enumerate(zip(layout(),phases())):
            if i<3:
                checks.append({"check_id":f"mesh_{i+1}.center_distance", "status":"PASS" if abs(math.dist(point,layout()[i+1])-40)<policy.linear_tolerance_mm else "FAIL"})
        horn_index=reference_report["front_horn_solid_index"]
        servo_horn=servo.solids()[horn_index]
        servo_body=Compound(children=[s for i,s in enumerate(servo.solids()) if i!=horn_index])
        export_stl(servo_body,stage/"review_meshes/servo_reference.stl",tolerance=0.05,angular_tolerance=0.2)
        export_stl(servo_horn,stage/"review_meshes/servo_horn_reference.stl",tolerance=0.04,angular_tolerance=0.15)
        assembly=Compound(label=spec.project_id,children=[*parts.values(),servo])
        export_step(assembly,stage/"assembly.step",unit=Unit.MM)
        exported=measure(import_step(stage/"assembly.step")); native=measure(assembly)
        good=exported["is_valid"] and exported["solid_count"]==native["solid_count"] and math.isclose(
            exported["volume_mm3"],native["volume_mm3"],rel_tol=policy.volume_relative_tolerance)
        good=good and all(abs(a-b)<=policy.linear_tolerance_mm for key in ("minimum_mm","maximum_mm") for a,b in zip(native[key],exported[key]))
        checks.append({"check_id":"assembly_step_roundtrip","status":"PASS" if good else "FAIL","measured":exported,"expected":native})
        geometry={"status":"PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL", "scope":"gearbox_development_geometry",
                  "checks":checks,"assembly":exported,"policy_sha256":sha256(policy_path)}
        atomic_json(stage/"geometry_report.json",geometry)
        if geometry["status"]!="PASS":
            raise ValueError("gearbox checks failed; see geometry_report.json")
        shutil.copyfile(spec_path,stage/"specification.yaml")
        shutil.copyfile(policy_path,stage/"release_policy.yaml")
        from .build import environment
        shutil.copyfile(servo_path,stage/"original_vendor_servo_reference.step")
        manifest={"schema_version":1,"project_id":spec.project_id,"status":"PASS","scope":"development_build",
                  "release_status":"BLOCKED","length_unit":"mm","source":source_identity(root),"environment":environment(),
                  "parts":records,"servo_reference":{"path":spec.servo_step,"sha256":sha256(servo_path)},
                  "specification_sha256":sha256(spec_path),"policy_sha256":sha256(policy_path),
                  "limitations":["Trial fits and horn threads need physical verification; no load rating.",
                                  "Servo is a dimensioned keep-out and horn mounting reference; original vendor STEP is preserved separately.",
                                  "Hardware is specified in BOM and clearance checks, not modeled as threaded solids.",
                                  "No release, print or powered-test approval."]}
        from .gearbox_review import create_review
        create_review(stage,manifest,spec,root)
        manifest["artifacts"]={str(p.relative_to(stage)):sha256(p) for p in sorted(stage.rglob("*")) if p.is_file()}
        atomic_json(stage/"build_manifest.json",manifest)
        stage.rename(output)
        return {"status":"PASS","scope":"gearbox_development_build","output":str(output.relative_to(root)),
                "manifest":str((output/"build_manifest.json").relative_to(root)),"printable_parts":len(parts),"release_status":"BLOCKED"}
    except Exception as exc:
        atomic_json(stage/"failure.json",{"status":"FAIL","error":str(exc)})
        raise ValueError(f"{exc}; preserved diagnostics: {stage.relative_to(root)}") from exc
