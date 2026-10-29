"""Pinned pocket plate: holds a small outrunner by its stator ring on the existing stand tower.

Frame: motor axis on Z, Z=0 at the motor's stationary (wire-side) face, rotor up (+Z).
No screws enter the stator face. The stator ring sits in a shallow pocket gripped by crush
ribs, and a pin on the floor engages the stator's locating hole so the motor cannot turn.
All four stator holes stay free for the encoder board, which hangs through the center opening.
"""
import math

from build123d import Box, Color, Cone, Cylinder, Pos, Rot

from cad.assemblies.bldc_stand import MAX, MIN, PLATE_SCREW_ANGLES, make_tower, polar, radial_slot

STATOR_HOLE_ANGLES = (45.0, 135.0, 225.0, 315.0)
ENCODER_ANGLES = (135.0, 315.0)  # review reference only; either diagonal pair is supported


def plate_z(spec):
    """Plate underside (tower top) and top (pocket rim) heights."""
    return -spec.floor_thickness_mm, spec.pocket_depth_mm


def rib_angles(spec):
    """Evenly spaced ribs, skipping any that would fall in the lead notch."""
    step = 360.0 / spec.rib_count
    half = math.degrees(math.asin(min(1.0, (spec.lead_notch_width_mm / 2 + spec.rib_radius_mm + 1)
                                       / (spec.motor_diameter_mm / 2))))
    angles = [i * step for i in range(spec.rib_count)]
    return [a for a in angles if abs((a - spec.lead_angle_deg + 180) % 360 - 180) > half]


def make_ribs(spec):
    """Vertical crush ribs whose inner faces sit `rib_interference_mm` inside the stator ring radius."""
    r_c = spec.motor_diameter_mm / 2 - spec.rib_interference_mm + spec.rib_radius_mm
    lead_in = min(0.8, spec.pocket_depth_mm / 2)
    ribs = None
    for a in rib_angles(spec):
        x, y = polar(r_c, a)
        rib = Pos(x, y, 0) * Cylinder(spec.rib_radius_mm, spec.pocket_depth_mm - lead_in, align=MIN)
        rib += Pos(x, y, spec.pocket_depth_mm - lead_in) * Cone(spec.rib_radius_mm, spec.rib_radius_mm * 0.3,
                                                                lead_in, align=MIN)
        ribs = rib if ribs is None else ribs + rib
    return ribs


def make_pin(spec):
    x, y = polar(spec.locating_hole_radius_mm, spec.locating_hole_angle_deg)
    r, tip = spec.pin_diameter_mm / 2, 0.4
    pin = Pos(x, y, 0) * Cylinder(r, spec.pin_height_mm - tip, align=MIN)
    pin += Pos(x, y, spec.pin_height_mm - tip) * Cone(r, r - tip, tip, align=MIN)
    return pin


def make_plate(spec, ss):
    z0, z1 = plate_z(spec)
    h = z1 - z0
    plate = Pos(0, 0, z0) * Cylinder(spec.plate_diameter_mm / 2, h, align=MIN)
    r_pocket = (spec.motor_diameter_mm + spec.pocket_diametral_clearance_mm) / 2
    plate -= Cylinder(r_pocket, spec.pocket_depth_mm, align=MIN)
    r_open = spec.center_opening_mm / 2
    plate -= Pos(0, 0, z0) * Cylinder(r_open, h, align=MIN)
    plate -= radial_slot(r_open - 1, spec.lead_notch_outer_radius_mm, spec.lead_notch_width_mm,
                         spec.lead_angle_deg, z0, z1)
    # Tab carrying the pin across the opening edge.
    r_tab = spec.pin_tab_inner_radius_mm
    tab = Pos((r_tab + r_open + 1) / 2, 0, z0) * Box(r_open + 1 - r_tab, spec.pin_tab_width_mm, -z0, align=MIN)
    tab += Pos(r_tab, 0, z0) * Cylinder(spec.pin_tab_width_mm / 2, -z0, align=MIN)
    plate += Rot(0, 0, spec.locating_hole_angle_deg) * tab
    plate += make_pin(spec)
    plate += make_ribs(spec)
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(ss.plate_screw_radius_mm, a)
        plate -= Pos(x, y, z0) * Cylinder(ss.m3_clearance_mm / 2, h, align=MIN)
    plate.label = "motor_plate_2804"
    plate.color = Color(0.20, 0.22, 0.25)
    return plate


def make_tower_at(spec, ss):
    """The existing printed tower, moved so its top meets this plate's underside."""
    return Pos(0, 0, ss.floor_thickness_mm - spec.floor_thickness_mm) * make_tower(ss)


def locating_hole(spec):
    x, y = polar(spec.locating_hole_radius_mm, spec.locating_hole_angle_deg)
    return Pos(x, y, 0) * Cylinder(spec.locating_hole_diameter_mm / 2, spec.locating_hole_depth_mm, align=MIN)


def motor_references(spec):
    """Supplier-nominal envelopes: stationary ring with its holes, rotating bell, rotating boss."""
    r = spec.motor_diameter_mm / 2
    stationary = Cylinder(r, spec.motor_stationary_height_mm, align=MIN) - locating_hole(spec)
    for a in STATOR_HOLE_ANGLES:
        x, y = polar(spec.stator_hole_circle_mm / 2, a)
        stationary -= Pos(x, y, 0) * Cylinder(1.25, spec.stator_thread_depth_mm, align=MIN)
    stationary.label, stationary.color = "motor_stationary_reference", Color(0.12, 0.12, 0.13)
    bell = (Pos(0, 0, spec.motor_stationary_height_mm)
            * Cylinder(r, spec.motor_body_height_mm - spec.motor_stationary_height_mm, align=MIN))
    bell -= Cylinder(spec.shaft_bore_mm / 2, spec.motor_body_height_mm, align=MIN)
    bell.label, bell.color = "motor_rotor_reference", Color(0.45, 0.47, 0.50)
    boss = Cylinder(spec.motor_boss_diameter_mm / 2, spec.motor_boss_height_mm, align=MAX)
    boss -= Cylinder(spec.shaft_bore_mm / 2 - 0.5, spec.motor_boss_height_mm, align=MAX)
    boss.label, boss.color = "motor_boss_reference", Color(0.70, 0.55, 0.20)
    return stationary, bell, boss


def lead_envelope(spec):
    """Motor lead leaving the stator ring: radial run out to the notch end and room to drop below."""
    r0 = spec.motor_diameter_mm / 2 - 2
    r1 = spec.lead_notch_outer_radius_mm - 2
    w = spec.lead_envelope_width_mm
    z0 = -spec.floor_thickness_mm
    env = Pos((r0 + r1) / 2, 0, z0) * Box(r1 - r0, w, spec.motor_stationary_height_mm - z0, align=MIN)
    return Rot(0, 0, spec.lead_angle_deg) * env


def rotating_keepouts(spec):
    """Envelopes nothing fixed may enter: bell with radial clearance above the ring, boss with margin."""
    c = spec.rotor_radial_clearance_mm
    bell = (Pos(0, 0, spec.motor_stationary_height_mm)
            * Cylinder(spec.motor_diameter_mm / 2 + c, spec.motor_body_height_mm, align=MIN))
    m = spec.boss_clearance_mm
    boss = Cylinder(spec.motor_boss_diameter_mm / 2 + m, spec.motor_boss_height_mm + m, align=MAX)
    return {"rotor_bell": bell, "rotor_boss": boss}


def encoder_envelopes(spec, standoff):
    """Largest supported board at one standoff length, any rotation, on either diagonal hole pair."""
    r_board = spec.encoder_board_max_square_mm * math.sqrt(2) / 2
    t = spec.encoder_pcb_thickness_mm
    chip = Pos(0, 0, -standoff) * Cylinder(spec.encoder_chip_side_radius_mm,
                                          spec.encoder_chip_side_height_mm, align=MIN)
    pcb = Pos(0, 0, -standoff) * Cylinder(r_board, t, align=MAX)
    below = Pos(0, 0, -standoff - t) * Cylinder(r_board, spec.encoder_below_pcb_depth_mm, align=MAX)
    standoffs = [Pos(*polar(spec.stator_hole_circle_mm / 2, a), 0)
                 * Cylinder(spec.encoder_standoff_hex_corner_mm / 2, standoff, align=MAX)
                 for a in STATOR_HOLE_ANGLES]
    return {"chip_side": chip, "pcb": pcb, "below_pcb": below, "standoffs": standoffs}


def as5600_reference(spec, standoff):
    """Kit AS5600 board for review only: chip toward the magnet, connectors away; spacing illustrative."""
    t = spec.encoder_pcb_thickness_mm
    turn = Rot(0, 0, ENCODER_ANGLES[0] - 90.0)  # board's center-slot axis onto the encoder diagonal
    board = Pos(0, 0, -standoff) * turn * Box(33, 33, t, align=MAX)
    board.label, board.color = "as5600_board_reference", Color(0.10, 0.35, 0.65)
    chip = Pos(0, 0, -standoff) * turn * Box(5, 6, 1.5, align=MIN)
    chip.label, chip.color = "as5600_chip_reference", Color(0.08, 0.08, 0.08)
    parts = [board, chip]
    for a in ENCODER_ANGLES:
        x, y = polar(spec.stator_hole_circle_mm / 2, a)
        spacer = Pos(x, y, 0) * Cylinder(2.5, standoff, align=MAX)
        spacer.label, spacer.color = f"as5600_spacer_{a:g}_reference", Color(0.78, 0.79, 0.80)
        parts.append(spacer)
    for sign in (-1, 1):
        plug = Pos(0, 0, -standoff - t) * turn * Pos(sign * 11.5, 0, 0) * Box(6, 10, 5.4, align=MAX)
        plug.label, plug.color = f"as5600_connector_{'p1' if sign < 0 else 'p2'}_reference", Color(0.92, 0.90, 0.84)
        parts.append(plug)
    return parts


def lead_reference(spec):
    """Approximate motor lead tab for review (drawing shows about 2.6 mm wide)."""
    r = spec.motor_diameter_mm / 2
    tab = Pos(r + 2.0, 0, 0.8) * Box(6.0, 2.6, 2.0, align=MIN)
    tab = Rot(0, 0, spec.lead_angle_deg) * tab
    tab.label, tab.color = "motor_lead_reference", Color(0.80, 0.20, 0.15)
    return tab


def screw_references(spec, ss):
    """M3 plate screws into the existing tower pilots (heads on the plate top)."""
    z0, z1 = plate_z(spec)
    screws = []
    for a in PLATE_SCREW_ANGLES:
        x, y = polar(ss.plate_screw_radius_mm, a)
        s = Pos(x, y, z1) * Cylinder(2.75, 2.0, align=MIN)
        s += Pos(x, y, z1) * Cylinder(1.5, spec.plate_screw_length_mm, align=MAX)
        s.label, s.color = f"m3_plate_screw_{a:g}_reference", Color(0.75, 0.75, 0.78)
        screws.append(s)
    return screws
