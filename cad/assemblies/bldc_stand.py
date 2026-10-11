"""Face-up BLDC evaluation stand: motor plate on a tower with an open encoder cavity.

Frame: motor axis on Z, Z=0 at the motor's stationary (wire-side) face, rotor up (+Z).
The stand's two M2.5 screws use the outer hole pair on X; the encoder standoffs use the
perpendicular pair on Y through radial slots. Windows face -Y (front) and +Y (rear).
"""
import math

from build123d import (Align, Box, Color, Cone, Cylinder, Pos, Rot)

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX = (Align.CENTER, Align.CENTER, Align.MAX)
CABLE_ANGLES = (45.0, 135.0, 225.0, 315.0)
PLATE_SCREW_ANGLES = (45.0, 135.0, 225.0, 315.0)


def polar(r, angle):
    return r * math.cos(math.radians(angle)), r * math.sin(math.radians(angle))


def plate_z(spec):
    """Plate underside and top (pocket rim) heights."""
    return -spec.floor_thickness_mm, spec.pocket_depth_mm


def radial_slot(r0, r1, width, angle, z0, z1):
    """Through slot from radius r0 to r1 along `angle`, with rounded ends."""
    length = r1 - r0
    slot = Pos((r0 + r1) / 2, 0, z0) * Box(length, width, z1 - z0, align=MIN)
    slot += Pos(r0, 0, z0) * Cylinder(width / 2, z1 - z0, align=MIN)
    slot += Pos(r1, 0, z0) * Cylinder(width / 2, z1 - z0, align=MIN)
    return Rot(0, 0, angle) * slot


def make_plate(spec):
    z0, z1 = plate_z(spec)
    h = z1 - z0
    plate = Pos(0, 0, z0) * Cylinder(spec.plate_diameter_mm / 2, h, align=MIN)
    pocket_d = spec.motor_diameter_mm + spec.pocket_diametral_clearance_mm
    plate -= Cylinder(pocket_d / 2, spec.pocket_depth_mm, align=MIN)
    plate -= Pos(0, 0, z0) * Cylinder(spec.center_opening_mm / 2, h, align=MIN)
    r_open = spec.center_opening_mm / 2
    for a in (90.0, 270.0):
        plate -= radial_slot(r_open - 1, spec.standoff_slot_outer_radius_mm,
                             spec.standoff_slot_width_mm, a, z0, z1)
    for a in CABLE_ANGLES:
        plate -= radial_slot(r_open - 1, spec.cable_notch_outer_radius_mm,
                             spec.cable_notch_width_mm, a, z0, z1)
    hole_r, sink_r = spec.m25_clearance_mm / 2, spec.m25_countersink_diameter_mm / 2
    for a in (0.0, 180.0):
        x, y = polar(spec.motor_outer_hole_circle_mm / 2, a)
        plate -= Pos(x, y, z0) * Cylinder(hole_r, h, align=MIN)
        # 90 degree countersink opening on the underside; screws enter from below.
        plate -= Pos(x, y, z0) * Cone(sink_r, hole_r, sink_r - hole_r, align=MIN)
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(spec.plate_screw_radius_mm, a)
        plate -= Pos(x, y, z0) * Cylinder(spec.m3_clearance_mm / 2, h, align=MIN)
    plate.label = "motor_plate"
    plate.color = Color(0.20, 0.22, 0.25)
    return plate


def tower_z(spec):
    """Tower top (meets plate underside), base top and base bottom heights."""
    top = -spec.floor_thickness_mm
    base_top = top - spec.cavity_height_mm
    return top, base_top, base_top - spec.base_thickness_mm


def make_tower(spec):
    top, base_top, bottom = tower_z(spec)
    r_out = spec.tower_outer_diameter_mm / 2
    r_in = r_out - spec.tower_wall_mm
    tower = Pos(0, 0, bottom) * Box(spec.base_x_mm, spec.base_y_mm, spec.base_thickness_mm, align=MIN)
    tower += Pos(0, 0, base_top) * (Cylinder(r_out, spec.cavity_height_mm, align=MIN)
                                     - Cylinder(r_in, spec.cavity_height_mm, align=MIN))
    # Windows with 45-degree pointed tops (print without support), front -Y and rear +Y.
    # Planar cuts meet the tube along exact ellipses, which survive STEP exchange; a
    # cylindrical arch would create an approximated cylinder-cylinder intersection.
    w, wh = spec.window_width_mm, spec.window_height_mm
    z_w = base_top + 4.0
    rect = wh - w / 2
    side = w / math.sqrt(2)
    for sign in (-1, 1):
        cut = Pos(0, 0, z_w) * Box(w, 2 * r_out, rect, align=MIN)
        roof = Pos(0, 0, z_w + rect) * (Rot(0, 45, 0) * Box(side, 2 * r_out, side)
                                          & Box(w, 2 * r_out, w / 2, align=MIN))
        tower -= Pos(0, sign * r_out / 2, 0) * (cut + roof)
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(spec.plate_screw_radius_mm, a)
        tower -= Pos(x, y, top) * Cylinder(spec.m3_tap_pilot_mm / 2, spec.plate_screw_pilot_depth_mm, align=MAX)
    hx, hy = spec.base_x_mm / 2 - spec.base_hole_inset_mm, spec.base_y_mm / 2 - spec.base_hole_inset_mm
    for x in (-hx, hx):
        for y in (-hy, hy):
            tower -= Pos(x, y, bottom) * Cylinder(spec.base_hole_mm / 2, spec.base_thickness_mm, align=MIN)
    # Zip-tie anchors behind the rear window.
    y_tie = (r_out + spec.base_y_mm / 2) / 2
    for x in (-8.0, 8.0):
        tower -= Pos(x, y_tie, bottom) * Box(2.5, 5.0, spec.base_thickness_mm, align=MIN)
    tower.label = "tower_base"
    tower.color = Color(0.32, 0.36, 0.40)
    return tower


def motor_references(spec):
    """Simplified supplier-nominal envelopes: stationary section, rotating bell and boss."""
    r = spec.motor_diameter_mm / 2
    stationary = Cylinder(r, spec.motor_stationary_height_mm, align=MIN)
    stationary.label, stationary.color = "motor_stationary_reference", Color(0.12, 0.12, 0.13)
    bell = (Pos(0, 0, spec.motor_stationary_height_mm)
            * Cylinder(r, spec.motor_body_height_mm - spec.motor_stationary_height_mm, align=MIN))
    bell -= Cylinder(7.5 / 2, spec.motor_body_height_mm, align=MIN)
    bell.label, bell.color = "motor_rotor_reference", Color(0.45, 0.47, 0.50)
    boss = Cylinder(spec.motor_boss_diameter_mm / 2, spec.motor_boss_height_mm, align=MAX)
    boss.label, boss.color = "motor_boss_reference", Color(0.70, 0.55, 0.20)
    return stationary, bell, boss


def rotating_keepouts(spec):
    """Envelopes nothing fixed may enter: bell with radial clearance, boss with 1 mm margin."""
    c = spec.rotor_radial_clearance_mm
    bell = (Pos(0, 0, spec.motor_stationary_height_mm)
            * Cylinder(spec.motor_diameter_mm / 2 + c, spec.motor_body_height_mm, align=MIN))
    boss = Cylinder(spec.motor_boss_diameter_mm / 2 + 1, spec.motor_boss_height_mm + 1, align=MAX)
    return {"rotor_bell": bell, "rotor_boss": boss}


def encoder_envelopes(spec, standoff):
    """Largest supported board at one standoff length, any rotation: chip side, PCB, stack below."""
    r_board = spec.encoder_board_max_square_mm * math.sqrt(2) / 2
    t = spec.encoder_pcb_thickness_mm
    chip = Pos(0, 0, -standoff) * Cylinder(spec.encoder_chip_side_radius_mm,
                                          spec.encoder_chip_side_height_mm, align=MIN)
    pcb = Pos(0, 0, -standoff) * Cylinder(r_board, t, align=MAX)
    below = Pos(0, 0, -standoff - t) * Cylinder(r_board, spec.encoder_below_pcb_depth_mm, align=MAX)
    standoffs = [Pos(*polar(rr, a), 0) * Cylinder(spec.encoder_standoff_hex_corner_mm / 2, standoff, align=MAX)
                 for a in (90.0, 270.0)
                 for rr in (spec.motor_inner_hole_circle_mm / 2, spec.motor_outer_hole_circle_mm / 2)]
    return {"chip_side": chip, "pcb": pcb, "below_pcb": below, "standoffs": standoffs}


def as5600_reference(spec, standoff=4.5):
    """Jamie's AS5600 stack for review: 33 mm board, corners on the Y standoff axis."""
    t = spec.encoder_pcb_thickness_mm
    board = Pos(0, 0, -standoff) * Rot(0, 0, 45) * Box(33, 33, t, align=MAX)
    board.label, board.color = "as5600_board_reference", Color(0.10, 0.35, 0.65)
    chip = Pos(0, 0, -standoff) * Box(5, 6, 1.7, align=MIN)
    chip.label, chip.color = "as5600_chip_reference", Color(0.08, 0.08, 0.08)
    parts = [board, chip]
    r = spec.motor_inner_hole_circle_mm / 2
    for a in (90.0, 270.0):
        x, y = polar(r, a)
        silver = Pos(x, y, 0) * Cylinder(2.5, standoff, align=MAX)
        silver.label, silver.color = f"as5600_standoff_{a:g}_reference", Color(0.78, 0.79, 0.80)
        brass = Pos(x, y, -standoff - t) * Cylinder(2.5, 7.0, align=MAX)
        brass.label, brass.color = f"as5600_brass_{a:g}_reference", Color(0.80, 0.65, 0.25)
        parts += [silver, brass]
    for sign in (-1, 1):
        plug = Pos(sign * 9, 0, -standoff - t) * Box(6, 10, 7.2, align=MAX)
        plug.label, plug.color = f"as5600_connector_{'p1' if sign < 0 else 'p2'}_reference", Color(0.92, 0.90, 0.84)
        parts.append(plug)
    return parts


def screw_references(spec):
    """Motor screws (M2.5 countersunk from below) and plate screws (M3, heads on top)."""
    z0, z1 = plate_z(spec)
    screws = []
    for a in (0.0, 180.0):
        x, y = polar(spec.motor_outer_hole_circle_mm / 2, a)
        sink_r = spec.m25_countersink_diameter_mm / 2
        s = Pos(x, y, z0) * (Cone(sink_r, 1.25, sink_r - 1.25, align=MIN)
                             + Cylinder(1.25, spec.motor_screw_length_mm, align=MIN))
        s.label, s.color = f"m25_motor_screw_{a:g}_reference", Color(0.75, 0.75, 0.78)
        screws.append(s)
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(spec.plate_screw_radius_mm, a)
        s = Pos(x, y, z1) * Cylinder(2.75, 2.0, align=MIN)
        s += Pos(x, y, z1) * Cylinder(1.5, 10.0, align=MAX)
        s.label, s.color = f"m3_plate_screw_{a:g}_reference", Color(0.75, 0.75, 0.78)
        screws.append(s)
    return screws
