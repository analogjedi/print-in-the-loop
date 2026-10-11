"""Independent layout checks and conservative planar motion clearance checks."""
from math import cos, dist, pi, radians, sin, sqrt
from shapely import Polygon
from shapely.affinity import rotate, translate
from cad.parts.spur_gear import profile_points
from cad.assemblies.gearbox import layout, phases


def normalize_stl_zeros(path,epsilon):
    """Remove tiny signed zero residues from separately tessellated circular faces."""
    import struct
    from .io import sha256
    before=sha256(path); data=bytearray(path.read_bytes()); count=struct.unpack_from("<I",data,80)[0]
    changed=0; maximum=0.
    for i in range(count):
        for j in range(9):
            at=84+50*i+12+4*j; value=struct.unpack_from("<f",data,at)[0]
            if value!=0 and abs(value)<epsilon:
                maximum=max(maximum,abs(value)); struct.pack_into("<f",data,at,0.); changed+=1
    path.write_bytes(data)
    return {"status":"PASS","scope":"derived_mesh_near_zero_normalization","coordinate_count":changed,
            "maximum_coordinate_change_mm":maximum,"epsilon_mm":epsilon,"before_sha256":before,"after_sha256":sha256(path)}


def mesh_manifold(path):
    """Exact float32 vertex welding; every directed mesh edge must have one opposite."""
    import struct
    from collections import Counter
    data=path.read_bytes(); count=struct.unpack_from("<I",data,80)[0]
    if len(data)!=84+50*count:
        return {"status":"FAIL","reason":"invalid binary STL length"}
    edges=Counter(); balance=Counter(); degenerate=0; volume=0.
    for i in range(count):
        coords=struct.unpack_from("<9f",data,84+50*i+12)
        a,b,c=[tuple(coords[j:j+3]) for j in (0,3,6)]
        ab=[b[j]-a[j] for j in range(3)]; ac=[c[j]-a[j] for j in range(3)]
        cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
        if sum(v*v for v in cross)==0:
            degenerate+=1
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        for u,v in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((u,v))); edges[key]+=1; balance[key]+=1 if u<v else -1
    bad=sum(v!=2 for v in edges.values()); inconsistent=sum(v!=0 for v in balance.values())
    return {"status":"PASS" if not (bad or inconsistent or degenerate) and volume>0 else "FAIL",
            "triangles":count,"nonmanifold_edges":bad,"orientation_errors":inconsistent,
            "degenerate_triangles":degenerate,"signed_volume_mm3":volume,
            "limitations":["Edge-manifold check does not independently rule out geometric self-intersection."]}


def motion_check(spec, phase_error_deg=0., samples=181):
    if samples < 19:
        raise ValueError("insufficient motion samples")
    profiles={n:Polygon(profile_points(n,thinning=spec.tooth_thinning_mm)) for n in (20,60)}
    refined={n:Polygon(profile_points(n,thinning=spec.tooth_thinning_mm,samples=256)) for n in (20,60)}
    convergence=max(profiles[n].hausdorff_distance(refined[n]) for n in profiles)
    # Conservative 0.002 mm per-boundary software allowance covers sampling and CAD interpolation.
    contour_allowance=0.002
    points=layout(); angles=phases(); checks=[]
    for i in range(3):
        minimum=float("inf"); max_area=0.
        for j in range(samples):
            angle=18*j/(samples-1)
            a=translate(rotate(profiles[20],angles[i]+angle,origin=(0,0)),*points[i])
            b=translate(rotate(profiles[60],angles[i+1]-angle/3+phase_error_deg,origin=(0,0)),*points[i+1])
            minimum=min(minimum,a.distance(b))
            max_area=max(max_area,a.intersection(b).area)
        half_step=radians(18/(samples-1))/2
        # Any boundary point moves at most r*angle; combine both gear motions.
        interval_bound=11*half_step+31*half_step/3
        lower=minimum-interval_bound-2*contour_allowance
        ok=max_area==0 and lower>0 and convergence<contour_allowance
        checks.append({"check_id":f"mesh_{i+1}_full_tooth_period", "status":"PASS" if ok else "FAIL",
                       "samples":samples,"pinion_period_deg":18,"measured_minimum_gap_mm":minimum,
                       "maximum_intersection_area_mm2":max_area,"interval_motion_bound_mm":interval_bound,
                       "contour_allowance_each_mm":contour_allowance,"contour_refinement_difference_mm":convergence,
                       "continuous_gap_lower_bound_mm":lower})
    rb1=10*cos(radians(20)); rb2=30*cos(radians(20))
    contact=(sqrt(11**2-rb1**2)+sqrt(31**2-rb2**2)-40*sin(radians(20)))/(pi*cos(radians(20)))
    checks.append({"check_id":"nominal_transverse_contact_ratio", "status":"PASS" if contact>1 else "FAIL", "measured":contact})
    return {"status":"PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL",
            "scope":"unloaded planar tooth motion with interval clearance bound", "signed_output_input_ratio":-1/27,
            "checks":checks,"limitations":["Rigid nominal geometry with centered backlash; not a loaded contact simulation.",
              "Periodic tooth geometry reduces each mesh sweep to one 18-degree pinion pitch.",
              "Contour allowance is a software bound, not a manufacturing fit tolerance."]}


def boxes_overlap(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    return all(min(u,v)-max(s,t)>1e-7 for s,u,t,v in zip(aa.min,aa.max,bb.min,bb.max))


def collision_checks(parts,servo,policy):
    def common_volume(a,b):
        if not boxes_overlap(a,b):
            return 0.
        common=a.intersect(b)
        from build123d import ShapeList
        shapes=common if isinstance(common,ShapeList) else ([common] if common is not None else [])
        return sum(abs(solid.volume) for shape in shapes for solid in shape.solids())
    checks=[]; names=list(parts)
    for i,name in enumerate(names):
        a=parts[name]
        for other in names[i+1:]:
            b=parts[other]
            volume=common_volume(a,b)
            tolerance=policy.volume_relative_tolerance*min(a.volume,b.volume)
            checks.append({"check_id":f"collision.{name}.{other}", "status":"PASS" if volume<=tolerance else "FAIL",
                           "common_volume_mm3":volume,"numerical_volume_tolerance_mm3":tolerance})
        # Source assembly solids may overlap each other; inspect only external interference.
        common=sum(common_volume(a,s) for s in servo.solids())
        tolerance=policy.volume_relative_tolerance*a.volume
        checks.append({"check_id":f"servo_clearance.{name}","status":"PASS" if common<=tolerance else "FAIL",
                       "common_volume_mm3":common,"numerical_volume_tolerance_mm3":tolerance})
    return checks


def rotating_clearance_checks(parts,servo,spec,policy):
    """Full-revolution radial envelopes for rotating parts vs fixed printed structures.

    Mating tooth pairs are checked separately; other gear pairs have disjoint tip
    envelopes. Booleans allow zero-volume bearing-face contact.
    """
    from cad.assemblies.gearbox import cyl
    from build123d import Compound
    static={k:v for k,v in parts.items() if not k.startswith("compound_gear") and k!="servo_horn_adapter"}
    moving={}
    for i,(x,y) in enumerate(layout()):
        low=22-5*i; high=27-5*i
        bore=(spec.shaft_diameter_mm+spec.shaft_diametral_clearance_mm)/2
        envelope=cyl(11,4,x,y,low)+cyl(31,4,x,y,high)+cyl(5,5,x,y,low)
        envelope-=cyl(bore,9,x,y,low)
        moving[f"gear_{i+1}_rotation_envelope"]=envelope
    moving["adapter_rotation_envelope"]=cyl(25,4,37,37,31)-cyl(3.3,4,37,37,31)
    moving["horn_rotation_envelope"]=cyl(9.6,4.5,37,37,35)-cyl(3.1,4.5,37,37,35)
    # Evaluate one envelope at a time so intended mating envelope overlaps are excluded.
    result=[]
    for name,envelope in moving.items():
        for static_name,shape in static.items():
            for check in collision_checks({name:envelope,static_name:shape},Compound(),policy):
                if check["check_id"].startswith("collision."+name+"."):
                    result.append(check)
    return result


def inspect_gearbox(shape,spec,policy):
    from cad.assemblies.gearbox import build_parts
    from .geometry import measure
    from .io import sha256
    from pathlib import Path
    if sha256(Path(spec.servo_step))!=spec.servo_step_sha256:
        raise ValueError("servo reference checksum mismatch")
    expected,servo=build_parts(spec)
    targets=[(name,part) for name,part in expected.items()]
    targets.extend((f"servo_reference_{i}",s) for i,s in enumerate(servo.solids()))
    actual=[measure(s) for s in shape.solids()]
    remaining=list(range(len(actual))); checks=[]
    for name,part in targets:
        target=measure(part)
        def matches(m):
            return (m["is_valid"] and abs(m["volume_mm3"]-target["volume_mm3"])<=policy.volume_relative_tolerance*target["volume_mm3"]
                    and all(abs(a-b)<=policy.linear_tolerance_mm for key in ("minimum_mm","maximum_mm") for a,b in zip(m[key],target[key])))
        index=next((i for i in remaining if matches(actual[i])),None)
        checks.append({"check_id":f"assembly_placement.{name}","status":"PASS" if index is not None else "FAIL",
                       "expected":target,"matched_solid_index":index})
        if index is not None:
            remaining.remove(index)
    checks.append({"check_id":"no_extra_assembly_solids","status":"PASS" if not remaining else "FAIL","unmatched":remaining})
    checks.append({"check_id":"whole_assembly_valid","status":"PASS" if shape.is_valid else "FAIL"})
    return {"status":"PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL", "scope":"gearbox_assembly_geometry",
            "checks":checks,"limitations":["Placement/volume/validity checks against rebuilt specified parts; see motion report for tooth engagement.",
            "Servo reference includes a declared conservative casing envelope."]}
