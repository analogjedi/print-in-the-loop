"""Degree dial on the 2804 rotor face with a flush second-filament scale, and a fixed pointer.

Frame: the stand frame of the pinned plate (Z=0 at the stator face, rotor up). Angles are
counter-clockwise from +X seen from +Z; `scale_angle` maps a dial reading to that frame.
The pointer clamps under one plate screw, hooks the plate rim and stops level with the dial face.
"""
import math

from build123d import (Align, Box, Color, Cone, Cylinder, Polygon, Pos, Rot, Text, extrude)
from cad.assemblies import bldc_pinned_plate as pp
from cad.assemblies.bldc_stand import PLATE_SCREW_ANGLES, polar

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX = (Align.CENTER, Align.CENTER, Align.MAX)
WHITE, RED = Color(0.96, 0.96, 0.94), Color(0.85, 0.08, 0.10)


def dial_z(spec, ps):
    """Dial underside (outside the recess), rotor face and dial top heights."""
    face = ps.motor_body_height_mm
    bottom = face - spec.rotor_recess_depth_mm
    return bottom, face, bottom + spec.dial_thickness_mm


def scale_angle(spec, value):
    sign = -1.0 if spec.scale_direction == "clockwise" else 1.0
    return (spec.zero_angle_deg + sign * value) % 360.0


def tick_kind(spec, value):
    for kind in ("major", "mid"):
        step = getattr(spec, f"{kind}_tick_step_deg")
        if math.isclose(value / step, round(value / step), abs_tol=1e-9):
            return kind
    return "minor"


def tick_values(spec):
    n = round(360 / spec.minor_tick_step_deg)
    return [i * spec.minor_tick_step_deg for i in range(n)]


def label_values(spec):
    return [i * spec.label_step_deg for i in range(round(360 / spec.label_step_deg))]


def tick_outer_radius(spec):
    return spec.dial_diameter_mm / 2 - spec.tick_outer_inset_mm


def make_ticks(spec, ps):
    _, _, top = dial_z(spec, ps)
    d, r1 = spec.inlay_depth_mm, tick_outer_radius(spec)
    ticks = []
    for value in tick_values(spec):
        kind = tick_kind(spec, value)
        length, width = getattr(spec, f"{kind}_tick_length_mm"), getattr(spec, f"{kind}_tick_width_mm")
        tick = Rot(0, 0, scale_angle(spec, value)) * (Pos(r1 - length / 2, 0, top) * Box(length, width, d, align=MAX))
        tick.label, tick.color = f"tick_{value:g}deg_{kind}", RED
        ticks.append(tick)
    return ticks


def make_labels(spec, ps):
    """Numbers read upright from outside the rim: the glyph 'up' direction points radially out."""
    _, _, top = dial_z(spec, ps)
    labels = []
    for value in label_values(spec):
        a = scale_angle(spec, value)
        x, y = polar(spec.label_radius_mm, a)
        glyphs = extrude(Text(f"{value:g}", font_size=spec.label_font_size_mm, font_path=spec.font_path),
                         amount=spec.inlay_depth_mm)
        label = Pos(x, y, top - spec.inlay_depth_mm) * Rot(0, 0, a - 90) * glyphs
        label.label, label.color = f"label_{value:g}deg", RED
        labels.append(label)
    return labels


def make_zero_marker(spec, ps):
    """Triangle inside the '0', apex pointing out at the zero reading."""
    _, _, top = dial_z(spec, ps)
    s = spec.zero_marker_size_mm
    r = s / math.sqrt(3)
    points = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in (0, 120, 240)]
    a = spec.zero_angle_deg
    x, y = polar(spec.zero_marker_radius_mm, a)
    marker = Pos(x, y, top) * Rot(0, 0, a) * extrude(Polygon(*points, align=None), amount=-spec.inlay_depth_mm)
    marker.label, marker.color = "zero_marker", RED
    return marker


def make_marks(spec, ps):
    return [*make_ticks(spec, ps), *make_labels(spec, ps), make_zero_marker(spec, ps)]


def countersink_holes(spec, ps):
    """Through clearance hole plus 90 degree countersink opening at the dial top, one per rotor hole."""
    _, face, top = dial_z(spec, ps)
    hub = top - face
    hole_r, sink_r = spec.screw_clearance_mm / 2, spec.countersink_diameter_mm / 2
    cuts = []
    for a in spec.rotor_hole_angles_deg:
        x, y = polar(spec.rotor_hole_circle_mm / 2, a)
        cut = Pos(x, y, face) * Cylinder(hole_r, hub, align=MIN)
        cut += Pos(x, y, top - (sink_r - hole_r)) * Cone(hole_r, sink_r, sink_r - hole_r, align=MIN)
        cuts.append(cut)
    return cuts


def recess_radius(spec, ps):
    return (ps.motor_diameter_mm + spec.rotor_recess_diametral_clearance_mm) / 2


def make_dial_blank(spec, ps):
    """Dial with its recess and holes but no scale pockets (the white body plus the red inlay)."""
    bottom, face, top = dial_z(spec, ps)
    dial = Pos(0, 0, bottom) * Cylinder(spec.dial_diameter_mm / 2, spec.dial_thickness_mm, align=MIN)
    dial -= Pos(0, 0, bottom) * Cylinder(recess_radius(spec, ps), spec.rotor_recess_depth_mm, align=MIN)
    dial -= Pos(0, 0, face) * Cylinder(spec.center_hole_mm / 2, top - face, align=MIN)
    for cut in countersink_holes(spec, ps):
        dial -= cut
    return dial


def make_dial(spec, ps):
    body = make_dial_blank(spec, ps)
    for mark in make_marks(spec, ps):
        body -= mark
    body.label, body.color = "rotor_dial", WHITE
    return body


def pointer_radii(spec):
    """Tip, riser inner face and outer face radii."""
    tip = spec.dial_diameter_mm / 2 + spec.pointer_gap_to_dial_mm
    inner = tip + spec.pointer_tip_length_mm
    return tip, inner, inner + spec.pointer_riser_thickness_mm


def make_pointer(spec, ps, ss):
    """Built along +X, then turned to the chosen plate screw."""
    _, plate_top = pp.plate_z(ps)
    _, _, top = dial_z(spec, ps)
    w, t = spec.pointer_width_mm, spec.pointer_arm_thickness_mm
    arm_top = plate_top + t
    tip, inner, outer = pointer_radii(spec)
    r0 = spec.pointer_arm_inner_radius_mm
    pointer = Pos((r0 + outer) / 2, 0, plate_top) * Box(outer - r0, w, t, align=MIN)
    pointer += Pos((inner + outer) / 2, 0, arm_top) * Box(outer - inner, w, top - arm_top, align=MIN)
    wedge = Polygon((inner, w / 2), (tip, 0.3), (tip, -0.3), (inner, -w / 2), align=None)
    pointer += Pos(0, 0, arm_top) * extrude(wedge, amount=top - arm_top)
    # Lip hooking the plate and tower rim, so the pointer cannot swing about its screw.
    r_rim = max(ps.plate_diameter_mm, ss.tower_outer_diameter_mm) / 2
    r_lip = r_rim + spec.pointer_lip_clearance_mm
    lip = (Cylinder(r_lip + spec.pointer_lip_thickness_mm, spec.pointer_lip_depth_mm, align=MAX)
           - Cylinder(r_lip, spec.pointer_lip_depth_mm, align=MAX))
    pointer += Pos(0, 0, plate_top) * (lip & Pos(r_rim, 0, 0) * Box(2 * spec.pointer_lip_thickness_mm + 2, w,
                                                                       spec.pointer_lip_depth_mm, align=MAX))
    x = ss.plate_screw_radius_mm
    pointer -= Pos(x, 0, plate_top) * Cylinder(ss.m3_clearance_mm / 2, t, align=MIN)
    floor = plate_top + spec.pointer_floor_under_head_mm
    pointer -= Pos(x, 0, floor) * Cylinder(spec.pointer_counterbore_mm / 2, arm_top - floor, align=MIN)
    pointer = Rot(0, 0, spec.pointer_screw_angle_deg) * pointer
    pointer.label, pointer.color = "dial_pointer", RED
    return pointer


def dial_screw_references(spec, ps):
    """M2.5 countersunk screws: head flush with the dial top, shank down into the rotor."""
    _, _, top = dial_z(spec, ps)
    head_r, shank_r = spec.countersink_diameter_mm / 2, 1.25
    screws = []
    for a in spec.rotor_hole_angles_deg:
        x, y = polar(spec.rotor_hole_circle_mm / 2, a)
        s = Pos(x, y, top - (head_r - shank_r)) * Cone(shank_r, head_r, head_r - shank_r, align=MIN)
        s += Pos(x, y, top) * Cylinder(shank_r, spec.dial_screw_length_mm, align=MAX)
        s.label, s.color = f"m25_dial_screw_{a:g}_reference", Color(0.75, 0.75, 0.78)
        screws.append(s)
    return screws


def plate_screw_references(spec, ps, ss):
    """All four M3 plate screws with full-height socket heads; the pointer's sits on its counterbore floor."""
    _, plate_top = pp.plate_z(ps)
    screws = []
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(ss.plate_screw_radius_mm, a)
        under = plate_top + (spec.pointer_floor_under_head_mm if math.isclose(a, spec.pointer_screw_angle_deg) else 0.)
        length = spec.pointer_screw_length_mm if math.isclose(a, spec.pointer_screw_angle_deg) else ps.plate_screw_length_mm
        s = Pos(x, y, under) * Cylinder(spec.m3_head_diameter_mm / 2, spec.m3_head_height_mm, align=MIN)
        s += Pos(x, y, under) * Cylinder(1.5, length, align=MAX)
        s.label, s.color = f"m3_plate_screw_{a:g}_reference", Color(0.75, 0.75, 0.78)
        screws.append(s)
    return screws


def dial_keepout(spec, ps):
    """Swept dial with the rotating clearance; fixed parts must stay outside it."""
    bottom, _, top = dial_z(spec, ps)
    c = spec.rotating_clearance_mm
    return Pos(0, 0, bottom - c) * Cylinder(spec.dial_diameter_mm / 2 + c, top - bottom + 2 * c, align=MIN)
