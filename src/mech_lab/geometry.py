"""Kernel measurements, independent expectations, and export round-trip checks."""
import math
import struct

from pydantic import BaseModel, ConfigDict
from .schema import CubeSphereSpec, Positive


class GeometryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    linear_tolerance_mm: Positive
    volume_relative_tolerance: Positive
    stl_linear_deflection_mm: Positive
    stl_angular_deflection_rad: Positive


def measure(shape):
    if shape is None or shape.wrapped is None:
        raise ValueError("geometry is empty")
    box = shape.bounding_box()
    return {"is_valid": bool(shape.is_valid), "solid_count": len(shape.solids()),
            "dimensions_mm": list(box.size), "minimum_mm": list(box.min),
            "maximum_mm": list(box.max), "volume_mm3": shape.volume}


def inspect(shape, expected, policy, prefix="geometry"):
    measured = measure(shape)
    checks = []

    def check(name, passed, actual, required):
        checks.append({"check_id": f"{prefix}.{name}", "status": "PASS" if passed else "FAIL",
                       "measured": actual, "expected": required})

    check("valid", measured["is_valid"], measured["is_valid"], True)
    check("solid_count", measured["solid_count"] == 1, measured["solid_count"], 1)
    dimensions = expected.dimensions if isinstance(expected, CubeSphereSpec) else expected
    values = [dimensions.x_mm, dimensions.y_mm, dimensions.z_mm]
    for index, axis in enumerate("xyz"):
        actual = measured["dimensions_mm"][index]
        check(f"{axis}_mm", math.isclose(actual, values[index], rel_tol=0,
              abs_tol=policy.linear_tolerance_mm), actual, values[index])
        minimum = measured["minimum_mm"][index]
        check(f"origin_{axis}_mm", abs(minimum) <= policy.linear_tolerance_mm, minimum, 0)
    volume = math.prod(values)
    if isinstance(expected, CubeSphereSpec):
        r, h, side = expected.sphere_radius_mm, expected.sphere_embed_mm, expected.cube_size_mm
        volume = side**3 + 4*math.pi*r**3/3 - math.pi*h*h*(r-h/3)
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.GeomAbs import GeomAbs_Sphere
        spheres = [surface.Sphere() for face in shape.faces()
                   if (surface := BRepAdaptor_Surface(face.wrapped)).GetType() == GeomAbs_Sphere]
        check("spherical_face_count", len(spheres) == 1, len(spheres), 1)
        if len(spheres) == 1:
            actual_radius = spheres[0].Radius()
            center = list(spheres[0].Location().Coord())
            target = [side/2, side/2, side+r-h]
            check("sphere_radius_mm", abs(actual_radius-r) <= policy.linear_tolerance_mm, actual_radius, r)
            check("sphere_center_mm", all(abs(a-b) <= policy.linear_tolerance_mm for a,b in zip(center,target)), center, target)
    check("volume_mm3", math.isfinite(measured["volume_mm3"]) and math.isclose(
        measured["volume_mm3"], volume, rel_tol=policy.volume_relative_tolerance, abs_tol=0),
        measured["volume_mm3"], volume)
    return {"status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS",
            "measurements": measured, "checks": checks}


def stl_bounds(path):
    """Read binary STL vertices to verify scale without assuming STL has units."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("truncated binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    if not count or len(data) != 84 + count * 50:
        raise ValueError("invalid binary STL triangle count")
    low, high = [math.inf] * 3, [-math.inf] * 3
    for index in range(count):
        values = struct.unpack_from("<9f", data, 84 + index * 50 + 12)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("nonfinite mesh coordinate")
        for offset, value in enumerate(values):
            axis = offset % 3
            low[axis], high[axis] = min(low[axis], value), max(high[axis], value)
    return {"triangle_count": count, "minimum_mm": low, "maximum_mm": high,
            "dimensions_mm": [high[i] - low[i] for i in range(3)]}
