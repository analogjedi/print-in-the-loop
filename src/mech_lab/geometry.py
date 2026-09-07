"""Kernel measurements, independent expectations, and export round-trip checks."""
import math
import struct

from pydantic import BaseModel, ConfigDict
from .schema import Positive


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
    values = [expected.x_mm, expected.y_mm, expected.z_mm]
    for index, axis in enumerate("xyz"):
        actual = measured["dimensions_mm"][index]
        check(f"{axis}_mm", math.isclose(actual, values[index], rel_tol=0,
              abs_tol=policy.linear_tolerance_mm), actual, values[index])
        minimum = measured["minimum_mm"][index]
        check(f"origin_{axis}_mm", abs(minimum) <= policy.linear_tolerance_mm, minimum, 0)
    volume = math.prod(values)
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
