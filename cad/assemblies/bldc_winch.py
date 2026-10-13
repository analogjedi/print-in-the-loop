"""Geared string winch on the face-up BLDC stand: 9:1 spur train, drum, pulley and weight.

Frame: the stand's. Motor axis on Z, Z=0 at the motor's stationary face, rotor face at
the motor body height. Shaft A carries the stage-1 gear and the stage-2 pinion; shaft B
carries the output gear and the string drum, with the output-encoder magnet above the
deck. The string leaves the drum along +X to a pulley overhanging the base's +X edge.
D-shaft flats face +X in every bore; set screws point +X onto them.
"""
import math

from build123d import (Align, Box, Color, Cone, Cylinder, Polygon, Pos, RegularPolygon, Rot, extrude)
from shapely.geometry import Point, box as shapely_box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from cad.assemblies import bldc_stand as stand
from cad.parts.spur_gear import gear_face

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
ROTOR_SCREW_ANGLES = (0.0, 90.0, 180.0, 270.0)


def cyl(r, z0, z1, x=0., y=0.):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=MIN)


def y_cyl(r, y0, y1, x, z):
    """Cylinder along +Y from y0 to y1 through (x, z)."""
    return Pos(x, y0, z) * Rot(-90, 0, 0) * Cylinder(r, y1 - y0, align=MIN)


def x_cyl(r, x0, x1, y, z):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=MIN)


def stack(profile, x=0., y=0.):
    """Solid of revolution about a vertical axis from (radius, z) points, as cones and cylinders."""
    solid = None
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z1 <= z0:
            continue
        piece = Pos(x, y, z0) * (Cylinder(r0, z1 - z0, align=MIN) if r0 == r1
                                 else Cone(r0, r1, z1 - z0, align=MIN))
        solid = piece if solid is None else solid + piece
    return solid


def centers(spec):
    m = spec.module_mm
    cd1 = m * (spec.rotor_gear_teeth + spec.stage1_gear_teeth) / 2
    cd2 = m * (spec.stage2_pinion_teeth + spec.output_gear_teeth) / 2
    a, b = math.radians(spec.stage1_direction_deg), math.radians(spec.stage2_direction_deg)
    A = (cd1 * math.cos(a), cd1 * math.sin(a))
    B = (A[0] + cd2 * math.cos(b), A[1] + cd2 * math.sin(b))
    return {"O": (0., 0.), "A": A, "B": B, "cd1": cd1, "cd2": cd2}


def mesh_phase(line_deg, pinion_deg, np_, ng):
    """Gear angle that puts a tooth gap on the line of centers opposite a pinion tooth."""
    return line_deg + 180 + 180 / ng - (pinion_deg - line_deg) * np_ / ng


def phases(spec):
    """Initial tooth angles (degrees) of the rotor gear, 78T, 23T and 69T."""
    rotor, pinion = 0.0, 0.0
    g1 = mesh_phase(spec.stage1_direction_deg, rotor, spec.rotor_gear_teeth, spec.stage1_gear_teeth)
    g2 = mesh_phase(spec.stage2_direction_deg, pinion, spec.stage2_pinion_teeth, spec.output_gear_teeth)
    return {"rotor": rotor, "stage1_gear": g1, "stage2_pinion": pinion, "output_gear": g2}


def drum_profile(spec, z):
    """(radius, z) outline of the drum above the output gear: waist below the pinion hub, V groove."""
    m, c = spec.module_mm, centers(spec)
    r_neck = m * (spec.output_gear_teeth / 2 - 1.25) - 1.0
    r_mid = c["cd2"] - spec.pinion_hub_diameter_mm / 2 - spec.rotating_clearance_mm
    r_rim, r_g = spec.drum_rim_radius_mm, spec.drum_groove_radius_mm
    z0 = z["s2_top"]
    zc = z0 + 1 + (r_mid - r_neck)
    zd = max(zc, z["hub_top"] + 1)
    ze = zd + (r_rim - r_mid)
    zf = ze + 1
    zg = zf + (r_rim - r_g)
    zh = zg + (r_rim - r_g)
    return [(r_neck, z0), (r_neck, z0 + 1), (r_mid, zc), (r_mid, zd), (r_rim, ze), (r_rim, zf),
            (r_g, zg), (r_rim, zh), (r_rim, zh + 1)]


def levels(spec, ss):
    """Named heights. `ss` is the stand specification."""
    z = {"rotor": ss.motor_body_height_mm, "frame0": stand.plate_z(ss)[1]}
    z["frame1"] = z["frame0"] + spec.frame_thickness_mm
    z["s1"] = z["rotor"] + spec.axial_gap_mm
    z["s1_top"] = z["s1"] + spec.stage1_face_mm
    z["s2"] = z["s1_top"] + spec.axial_gap_mm
    z["s2_top"] = z["s2"] + spec.stage2_face_mm
    z["hub_top"] = z["s2_top"] + spec.pinion_hub_height_mm
    z["set_a"] = z["s2_top"] + spec.pinion_hub_height_mm / 2
    profile = drum_profile(spec, z)
    z["set_b"] = (profile[2][1] + profile[3][1]) / 2
    z["groove"] = profile[6][1]
    z["drum_top"] = profile[-1][1]
    z["deck0"] = z["drum_top"] + 1.5
    z["deck1"] = z["deck0"] + spec.deck_thickness_mm
    z["holder0"] = z["deck1"] + spec.magnet_holder_gap_mm
    z["holder1"] = z["holder0"] + spec.magnet_holder_shaft_engagement_mm + spec.magnet_thickness_mm
    z["shaft_a_top"] = z["deck0"] + spec.bearing_width_mm
    z["shaft_b_top"] = z["holder0"] + spec.magnet_holder_shaft_engagement_mm
    z["pulley"] = z["groove"] - spec.pulley_groove_radius_mm
    return z


def pulley_frame(spec):
    """Pulley center (x, y, z) is fixed by the drum: string leaves the drum tangent along +X."""
    c = centers(spec)
    return spec.pulley_x_mm, c["B"][1] + spec.drum_groove_radius_mm


def d_bore(spec, xy, z0, z1):
    r = (spec.shaft_diameter_mm + spec.d_bore_diametral_clearance_mm) / 2
    flat = spec.shaft_diameter_mm / 2 - spec.shaft_flat_depth_mm + spec.d_bore_diametral_clearance_mm / 2
    bore = cyl(r, z0, z1, *xy)
    return bore - Pos(xy[0] + flat, xy[1], z0) * Box(2 * r, 2 * r, z1 - z0, align=(Align.MIN, Align.CENTER, Align.MIN))


def d_shaft(spec, xy, z0, z1):
    r = spec.shaft_diameter_mm / 2
    flat = r - spec.shaft_flat_depth_mm
    return cyl(r, z0, z1, *xy) - Pos(xy[0] + flat, xy[1], z0) * Box(2 * r, 2 * r, z1 - z0,
                                                                     align=(Align.MIN, Align.CENTER, Align.MIN))


def set_screw_cut(spec, xy, z, outer_r, top):
    """Radial M3 clearance hole along +X and a captive-nut slot open to `top`."""
    hole = x_cyl(spec.m3_clearance_mm / 2, xy[0], xy[0] + outer_r + 1, xy[1], z)
    af, c = spec.nut_across_flats_mm, spec.nut_clearance_mm
    width = af / math.cos(math.radians(30)) + c
    bottom = z - (af + c) / 2
    slot = Pos(xy[0] + spec.nut_inner_radius_mm, xy[1], bottom) * Box(
        spec.nut_thickness_mm + c, width, top - bottom, align=(Align.MIN, Align.CENTER, Align.MIN))
    return hole + slot


def gear(spec, teeth, face, xy, z0, phase_deg):
    body = extrude(gear_face(teeth, spec.module_mm, spec.pressure_angle_deg, spec.tooth_thinning_mm), amount=face)
    return Pos(xy[0], xy[1], z0) * Rot(0, 0, phase_deg) * body


def label(part, name, color):
    part.label, part.color = name, Color(*color)
    return part


def make_rotor_gear(spec, ss):
    z, ph = levels(spec, ss), phases(spec)
    root = spec.module_mm * (spec.rotor_gear_teeth / 2 - 1.25)
    g = gear(spec, spec.rotor_gear_teeth, spec.stage1_face_mm, (0, 0), z["s1"], ph["rotor"])
    g += cyl(root - 0.75, z["rotor"], z["s1"])
    g -= cyl(spec.rotor_center_hole_mm / 2, z["rotor"], z["s1_top"])
    floor = z["rotor"] + spec.rotor_screw_length_mm - spec.rotor_screw_engagement_mm
    for a in ROTOR_SCREW_ANGLES:
        x, y = stand.polar(spec.rotor_screw_circle_mm / 2, a)
        g -= cyl(spec.rotor_screw_clearance_mm / 2, z["rotor"], z["s1_top"], x, y)
        g -= cyl(spec.rotor_counterbore_diameter_mm / 2, floor, z["s1_top"], x, y)
    return label(g, "rotor_gear", (0.96, 0.52, 0.10))


def make_stage_gear(spec, ss):
    """78T + 23T compound on shaft A; printed 78T face down."""
    z, ph, A = levels(spec, ss), phases(spec), centers(spec)["A"]
    root23 = spec.module_mm * (spec.stage2_pinion_teeth / 2 - 1.25)
    g = gear(spec, spec.stage1_gear_teeth, spec.stage1_face_mm, A, z["s1"], ph["stage1_gear"])
    g += cyl(root23 - 1.0, z["s1_top"], z["s2"], *A)
    g += gear(spec, spec.stage2_pinion_teeth, spec.stage2_face_mm, A, z["s2"], ph["stage2_pinion"])
    g += cyl(spec.pinion_hub_diameter_mm / 2, z["s2_top"], z["hub_top"], *A)
    g -= d_bore(spec, A, z["s1"], z["hub_top"])
    g -= set_screw_cut(spec, A, z["set_a"], spec.pinion_hub_diameter_mm / 2, z["hub_top"])
    return label(g, "stage_gear_78t_23t", (0.16, 0.47, 0.68))


def make_output_drum(spec, ss):
    """69T output gear + string drum on shaft B; printed gear face down."""
    z, ph, B = levels(spec, ss), phases(spec), centers(spec)["B"]
    profile = drum_profile(spec, z)
    g = gear(spec, spec.output_gear_teeth, spec.stage2_face_mm, B, z["s2"], ph["output_gear"])
    g += stack(profile, *B)
    g += cyl(spec.race_boss_diameter_mm / 2, z["drum_top"], z["deck0"], *B)
    g -= d_bore(spec, B, z["s2"], z["deck0"])
    g -= set_screw_cut(spec, B, z["set_b"], profile[2][0], z["drum_top"])
    # String anchor on -X, away from the set screw: radial hole from the groove bottom into
    # a vertical hole up to the top face, for tying off.
    r_g = spec.drum_groove_radius_mm
    g -= x_cyl(0.75, B[0] - r_g - 0.5, B[0] - r_g + 6.5, B[1], z["groove"])
    g -= cyl(1.25, z["groove"] - 1.25, z["drum_top"], B[0] - (r_g - 5.0), B[1])
    return label(g, "output_gear_69t_drum", (0.96, 0.52, 0.10))


def make_spacer(spec, name, xy, z0, z1, boss_at):
    b = spec.race_boss_height_mm
    lo, hi = (z0 + b, z1) if boss_at == "bottom" else (z0, z1 - b)
    s = cyl(spec.spacer_outer_diameter_mm / 2, lo, hi, *xy)
    s += cyl(spec.race_boss_diameter_mm / 2, z0, lo, *xy) if boss_at == "bottom" else \
        cyl(spec.race_boss_diameter_mm / 2, hi, z1, *xy)
    s -= cyl((spec.shaft_diameter_mm + spec.spacer_bore_diametral_clearance_mm) / 2, z0, z1, *xy)
    return label(s, name, (0.85, 0.85, 0.82))


def make_spacers(spec, ss):
    z, c = levels(spec, ss), centers(spec)
    return [make_spacer(spec, "spacer_a_lower", c["A"], z["frame1"], z["s1"], "bottom"),
            make_spacer(spec, "spacer_a_upper", c["A"], z["hub_top"], z["deck0"], "top"),
            make_spacer(spec, "spacer_b_lower", c["B"], z["frame1"], z["s2"], "bottom")]


def outline(shapes):
    hull = orient(unary_union(shapes).convex_hull)  # counter-clockwise, so faces point +Z
    return Polygon(*list(hull.exterior.coords)[:-1], align=None)


def bearing_seat(spec, xy, z_seat0, z_seat1, z_lip0, z_lip1):
    r = (spec.bearing_od_mm + spec.bearing_seat_diametral_allowance_mm) / 2
    return cyl(r, z_seat0, z_seat1, *xy) + cyl(spec.bearing_lip_hole_mm / 2, z_lip0, z_lip1, *xy)


def make_frame(spec, ss):
    """Lower bearing frame on the motor plate, with columns up to the deck."""
    z, c = levels(spec, ss), centers(spec)
    col_r = spec.column_diameter_mm / 2
    shapes = [Point(0, 0).buffer(spec.frame_outer_radius_mm, 64)]
    shapes += [Point(*c[k]).buffer(spec.bearing_boss_radius_mm, 64) for k in ("A", "B")]
    shapes += [Point(*p).buffer(col_r + spec.deck_margin_mm, 32) for p in spec.column_positions_mm]
    f = extrude(Pos(0, 0, z["frame0"]) * outline(shapes), amount=spec.frame_thickness_mm)
    f -= cyl(spec.frame_inner_radius_mm, z["frame0"], z["frame1"])
    w = spec.bearing_width_mm
    for k in ("A", "B"):
        f -= bearing_seat(spec, c[k], z["frame1"] - w, z["frame1"], z["frame0"], z["frame1"] - w)
    for a in stand.PLATE_SCREW_ANGLES:
        x, y = stand.polar(ss.plate_screw_radius_mm, a)
        f -= cyl(spec.m3_clearance_mm / 2, z["frame0"], z["frame1"], x, y)
    for x, y in spec.column_positions_mm:
        f += cyl(col_r, z["frame1"], z["deck0"], x, y)
        f -= cyl(spec.m3_tap_pilot_mm / 2, z["deck0"] - spec.column_pilot_depth_mm, z["deck0"], x, y)
    return label(f, "winch_frame", (0.20, 0.22, 0.25))


def pulley_layout(spec, ss):
    x_p, y_p = pulley_frame(spec)
    z_p = levels(spec, ss)["pulley"]
    half = spec.pulley_width_mm / 2
    inner = half + spec.pulley_side_gap_mm
    outer = inner + spec.pulley_cheek_thickness_mm
    return x_p, y_p, z_p, half, inner, outer


def make_deck(spec, ss):
    """Upper bearing deck with the pulley fork and output-encoder pilots; printed upside down."""
    z, c = levels(spec, ss), centers(spec)
    x_p, y_p, z_p, half, inner, outer = pulley_layout(spec, ss)
    cr = spec.pulley_cheek_radius_mm
    shapes = [Point(*p).buffer(spec.column_diameter_mm / 2 + spec.deck_margin_mm, 32) for p in spec.column_positions_mm]
    shapes += [Point(*c["A"]).buffer(spec.bearing_boss_radius_mm, 64),
               Point(*c["B"]).buffer(spec.encoder_pilot_circle_mm / 2 + 4.0, 64),
               shapely_box(x_p - cr, y_p - outer, x_p + cr, y_p + outer)]
    d = extrude(Pos(0, 0, z["deck0"]) * outline(shapes), amount=spec.deck_thickness_mm)
    w = spec.bearing_width_mm
    for k in ("A", "B"):
        d -= bearing_seat(spec, c[k], z["deck0"], z["deck0"] + w, z["deck0"] + w, z["deck1"])
    for x, y in spec.column_positions_mm:
        d -= cyl(spec.m3_clearance_mm / 2, z["deck0"], z["deck1"], x, y)
    for i in range(spec.encoder_pilot_count):
        x, y = stand.polar(spec.encoder_pilot_circle_mm / 2, 360 * i / spec.encoder_pilot_count)
        d -= cyl(spec.encoder_pilot_mm / 2, z["deck0"], z["deck1"], c["B"][0] + x, c["B"][1] + y)
    # Fork cheeks hanging from the deck, round at the axle; race bosses on the inner faces.
    bearing0 = y_p - half
    bearing1 = bearing0 + spec.bearing_width_mm
    for y0, y1 in ((y_p - outer, y_p - inner), (y_p + inner, y_p + outer)):
        d += Pos(x_p, y0, z_p) * Box(2 * cr, y1 - y0, z["deck0"] - z_p, align=(Align.CENTER, Align.MIN, Align.MIN))
        d += y_cyl(cr, y0, y1, x_p, z_p)
    rb = spec.race_boss_diameter_mm / 2
    d += y_cyl(rb, y_p - inner, bearing0, x_p, z_p) + y_cyl(rb, bearing1, y_p + inner, x_p, z_p)
    d -= y_cyl(spec.m5_clearance_mm / 2, y_p - outer, y_p + outer, x_p, z_p)
    return label(d, "winch_deck", (0.32, 0.36, 0.40))


def make_sheave(spec, ss):
    """Pulley sheave about +Y; bearing pocket open toward -Y, retaining lip toward +Y."""
    x_p, y_p, z_p, half, _, _ = pulley_layout(spec, ss)
    rf, rg = spec.pulley_flange_radius_mm, spec.pulley_groove_radius_mm
    v = min(rf - rg, half - 0.5)
    local = stack([(rf, -half), (rf, -v), (rg, 0.0), (rf, v), (rf, half)])
    seat = -half + spec.bearing_width_mm
    local -= cyl((spec.bearing_od_mm + spec.bearing_seat_diametral_allowance_mm) / 2, -half, seat)
    local -= cyl(spec.bearing_lip_hole_mm / 2, seat, half)
    return label(Pos(x_p, y_p, z_p) * Rot(-90, 0, 0) * local, "pulley_sheave", (0.96, 0.52, 0.10))


def make_magnet_holder(spec, ss):
    z, B = levels(spec, ss), centers(spec)["B"]
    h = cyl(spec.magnet_holder_diameter_mm / 2, z["holder0"], z["holder1"], *B)
    h -= d_bore(spec, B, z["holder0"], z["holder0"] + spec.magnet_holder_shaft_engagement_mm)
    pocket = (spec.magnet_diameter_mm + spec.magnet_pocket_clearance_mm) / 2
    h -= cyl(pocket, z["holder1"] - spec.magnet_thickness_mm, z["holder1"], *B)
    return label(h, "magnet_holder", (0.96, 0.52, 0.10))


def make_printed(spec, ss):
    parts = [make_rotor_gear(spec, ss), make_stage_gear(spec, ss), make_output_drum(spec, ss),
             *make_spacers(spec, ss), make_frame(spec, ss), make_deck(spec, ss),
             make_sheave(spec, ss), make_magnet_holder(spec, ss)]
    return {p.label: p for p in parts}


# Rotating bodies: axis, rate relative to the rotor, and printed parts that turn on it.
def rotation_groups(spec):
    c = centers(spec)
    s1 = -spec.rotor_gear_teeth / spec.stage1_gear_teeth
    out = s1 * -spec.stage2_pinion_teeth / spec.output_gear_teeth
    x_p, y_p = pulley_frame(spec)
    r_eff = spec.drum_groove_radius_mm + spec.string_diameter_mm / 2
    # Drum turning +Z (CCW from above) winds string at its +Y tangent, so the string at the
    # top of the sheave runs -X and the sheave turns negatively about +Y.
    sheave = -out * r_eff / (spec.pulley_groove_radius_mm + spec.string_diameter_mm / 2)
    return {"rotor": {"axis": "z", "center": c["O"], "rate": 1.0},
            "shaft_a": {"axis": "z", "center": c["A"], "rate": s1},
            "shaft_b": {"axis": "z", "center": c["B"], "rate": out},
            "sheave": {"axis": "y", "center": (x_p, y_p), "rate": sheave}}


PART_AXIS = {"rotor_gear": "rotor", "stage_gear_78t_23t": "shaft_a", "spacer_a_lower": "shaft_a",
             "spacer_a_upper": "shaft_a", "output_gear_69t_drum": "shaft_b", "spacer_b_lower": "shaft_b",
             "magnet_holder": "shaft_b", "pulley_sheave": "sheave"}


def bearing_ref(spec, xy, z0, name):
    b = cyl(spec.bearing_od_mm / 2, z0, z0 + spec.bearing_width_mm, *xy)
    b -= cyl(spec.bearing_id_mm / 2, z0, z0 + spec.bearing_width_mm, *xy)
    return label(b, name, (0.72, 0.74, 0.78))


def screw_ref(name, xy, z_head, length, shank_r, head_r, head_h):
    s = cyl(head_r, z_head, z_head + head_h, *xy) + cyl(shank_r, z_head - length, z_head, *xy)
    return label(s, name, (0.75, 0.75, 0.78))


def hardware(spec, ss):
    """Purchased parts at seller-nominal size, plus the string and weight envelope."""
    z, c = levels(spec, ss), centers(spec)
    w = spec.bearing_width_mm
    x_p, y_p, z_p, half, inner, outer = pulley_layout(spec, ss)
    parts = [bearing_ref(spec, c["A"], z["frame1"] - w, "bearing_625_a_lower"),
             bearing_ref(spec, c["B"], z["frame1"] - w, "bearing_625_b_lower"),
             bearing_ref(spec, c["A"], z["deck0"], "bearing_625_a_upper"),
             bearing_ref(spec, c["B"], z["deck0"], "bearing_625_b_upper")]
    pb = Pos(x_p, y_p, z_p) * Rot(-90, 0, 0) * (
        cyl(spec.bearing_od_mm / 2, -half, -half + w) - cyl(spec.bearing_id_mm / 2, -half, -half + w))
    parts.append(label(pb, "bearing_625_pulley", (0.72, 0.74, 0.78)))
    parts.append(label(d_shaft(spec, c["A"], z["shaft_a_top"] - spec.shaft_length_mm, z["shaft_a_top"]),
                       "shaft_a_d5x100", (0.80, 0.81, 0.83)))
    parts.append(label(d_shaft(spec, c["B"], z["shaft_b_top"] - spec.shaft_length_mm, z["shaft_b_top"]),
                       "shaft_b_d5x100", (0.80, 0.81, 0.83)))
    floor = z["rotor"] + spec.rotor_screw_length_mm - spec.rotor_screw_engagement_mm
    for a in ROTOR_SCREW_ANGLES:
        parts.append(screw_ref(f"m25x6_rotor_screw_{a:g}", stand.polar(spec.rotor_screw_circle_mm / 2, a),
                               floor, spec.rotor_screw_length_mm, 1.25, 2.25, spec.rotor_screw_head_height_mm))
    for a in stand.PLATE_SCREW_ANGLES:
        parts.append(screw_ref(f"m3x16_plate_screw_{a:g}", stand.polar(ss.plate_screw_radius_mm, a),
                               z["frame1"], spec.plate_screw_length_mm, 1.5, 2.75, 3.0))
    for i, p in enumerate(spec.column_positions_mm):
        parts.append(screw_ref(f"m3x16_deck_screw_{i + 1}", p, z["deck1"], spec.deck_screw_length_mm, 1.5, 2.75, 3.0))
    bolt = y_cyl(4.25, y_p - outer - 3.0, y_p - outer, x_p, z_p) + y_cyl(
        2.5, y_p - outer, y_p - outer + spec.m5_bolt_length_mm, x_p, z_p)
    parts.append(label(bolt, "m5x20_pulley_bolt", (0.75, 0.75, 0.78)))
    nut = Pos(x_p, y_p + outer, z_p) * Rot(-90, 0, 0) * extrude(RegularPolygon(4.6, 6), amount=spec.m5_nut_height_mm)
    nut -= y_cyl(2.5, y_p + outer, y_p + outer + spec.m5_nut_height_mm, x_p, z_p)
    parts.append(label(nut, "m5_nylock_nut", (0.75, 0.75, 0.78)))
    flat = spec.shaft_diameter_mm / 2 - spec.shaft_flat_depth_mm
    af = spec.nut_across_flats_mm
    for key, zz in (("A", z["set_a"]), ("B", z["set_b"])):
        x, y = c[key]
        parts.append(label(x_cyl(1.5, x + flat, x + flat + spec.set_screw_length_mm, y, zz),
                           f"m3x4_set_screw_{key.lower()}", (0.2, 0.2, 0.2)))
        hexnut = extrude(Rot(0, 0, 30) * RegularPolygon(af / math.sqrt(3), 6), amount=spec.nut_thickness_mm)
        hexnut = Pos(x + spec.nut_inner_radius_mm + spec.nut_clearance_mm / 2, y, zz) * Rot(0, 90, 0) * hexnut
        hexnut -= x_cyl(1.5, x, x + 10, y, zz)
        parts.append(label(hexnut, f"m3_nut_{key.lower()}", (0.75, 0.75, 0.78)))
    parts.append(label(cyl(spec.magnet_diameter_mm / 2, z["holder1"] - spec.magnet_thickness_mm, z["holder1"], *c["B"]),
                       "magnet_6x2_5_diametric", (0.55, 0.12, 0.12)))
    return {p.label: p for p in parts}


def string_and_weight(spec, ss):
    """String segments and the weight envelope at its lowest position."""
    z, B = levels(spec, ss), centers(spec)["B"]
    x_p, y_p, z_p, *_ = pulley_layout(spec, ss)
    rs = spec.string_diameter_mm / 2
    rp = spec.pulley_groove_radius_mm + rs
    top = z_p - spec.weight_min_hang_mm
    low = top - spec.drop_mm
    run = x_cyl(rs, B[0], x_p, y_p, z["groove"] + rs)
    drop = cyl(rs, low, z_p, x_p + rp, y_p)
    weight = cyl(spec.weight_envelope_diameter_mm / 2, low - spec.weight_envelope_height_mm, low, x_p + rp, y_p)
    return (label(run, "string_run", (0.95, 0.95, 0.30)), label(drop, "string_drop", (0.95, 0.95, 0.30)),
            label(weight, "weight_lowest", (0.40, 0.40, 0.44)))


def rotating_envelopes(spec, ss):
    """Full-revolution envelopes, keyed by component, each with its axis group."""
    z, c, m = levels(spec, ss), centers(spec), spec.module_mm
    tip = lambda n: m * (n / 2 + 1)
    root23 = m * (spec.stage2_pinion_teeth / 2 - 1.25)
    root26 = m * (spec.rotor_gear_teeth / 2 - 1.25)
    so = spec.spacer_outer_diameter_mm / 2
    x_p, y_p, z_p, half, *_ = pulley_layout(spec, ss)
    env = {
        "rotor_gear": ("rotor", cyl(tip(spec.rotor_gear_teeth), z["s1"], z["s1_top"]) + cyl(root26 - 0.75, z["rotor"], z["s1"])),
        "stage1_gear": ("shaft_a", cyl(tip(spec.stage1_gear_teeth), z["s1"], z["s1_top"], *c["A"])),
        "stage2_pinion": ("shaft_a", cyl(tip(spec.stage2_pinion_teeth), z["s2"], z["s2_top"], *c["A"])
                          + cyl(root23 - 1.0, z["s1_top"], z["s2"], *c["A"])),
        "pinion_hub": ("shaft_a", cyl(spec.pinion_hub_diameter_mm / 2, z["s2_top"], z["hub_top"], *c["A"])),
        "spacers_a": ("shaft_a", cyl(so, z["frame1"], z["s1"], *c["A"]) + cyl(so, z["hub_top"], z["deck0"], *c["A"])),
        "output_gear": ("shaft_b", cyl(tip(spec.output_gear_teeth), z["s2"], z["s2_top"], *c["B"])),
        "drum": ("shaft_b", stack(drum_profile(spec, z), *c["B"])
                 + cyl(spec.race_boss_diameter_mm / 2, z["drum_top"], z["deck0"], *c["B"])),
        "spacer_b": ("shaft_b", cyl(so, z["frame1"], z["s2"], *c["B"])),
        "magnet_holder": ("shaft_b", cyl(spec.magnet_holder_diameter_mm / 2, z["holder0"], z["holder1"], *c["B"])),
        "sheave": ("sheave", y_cyl(spec.pulley_flange_radius_mm, y_p - half, y_p + half, x_p, z_p)),
    }
    return env


MESHES = (("rotor_gear", "stage1_gear"), ("stage2_pinion", "output_gear"))


def encoder_envelope(spec, ss):
    """Largest supported board at any rotation above the deck, from the deck surface up."""
    z, B = levels(spec, ss), centers(spec)["B"]
    r = spec.encoder_board_max_square_mm * math.sqrt(2) / 2
    env = cyl(r, z["deck1"] + 0.01, z["deck1"] + spec.encoder_envelope_height_mm, *B)
    return env - cyl(spec.magnet_holder_diameter_mm / 2 + 0.5, z["deck1"], z["deck1"] + spec.encoder_envelope_height_mm, *B)
