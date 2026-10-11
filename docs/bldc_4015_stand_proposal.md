# 4015 BLDC motor — face-up desktop evaluation stand (proposal, rev. 3)

Status: **v1 CAD BUILT**, October 11, 2026 (see *Built candidate* below). Jamie approved
printing after reviewing the 3D model; printed in black PLA (AMS slot 2),
13:04–15:29: `FINISH`, `print_error 0`, 280/280 layers, no new HMS notices. A brief pause
with `0500-806E` during bed preheat cleared without intervention from this session; its
meaning is not documented anywhere found. Physical fit checks are next. The rotor indicator disc is designed but **on hold** until a second motor
type is known. Purpose: hold a 4015 hollow-shaft BLDC (24N22P) rotor-face-up on a
desk for developing Jamie's motor driver and FOC control. It must accept **both**
encoder boards, the supplied round MT6701 and Jamie's retrofitted 33 × 33 AS5600,
plus boards up to 20 mm larger or smaller, with flexible standoff positions.
Sources: [bldc_4015/](../components/drawings/bldc_4015/) and
[as5600_encoder_board/](../components/drawings/as5600_encoder_board/), hashes in each
`source_checksums.json`. All values are supplier nominals or drawing readings until measured.

## Motor outline

Outrunner: the rotor bell, including the top face and outer wall, turns. Below the seam,
the bottom 5.5 mm of casing and the wire-side face are stationary.

| Feature | Value | Source / confidence |
|---|---|---|
| Body | Ø45, 25 tall; 26 overall including bottom boss | Drawing + table |
| Rotating bell | Top 19.5 mm of the body, Ø45 | Drawing side view |
| Stationary section | Bottom 5.5 mm of the outer casing, below the seam (25 − 19.5) | Derived from drawing |
| Bottom center boss | About 1 mm proud of the stator face; Ø11 outer, Ø7 inner | Section B–B, labeled "radial magnets rotate with the rotor": treat as **rotating** |
| Hollow shaft bore | Ø7.5 through | Drawing + table |
| Stator face holes | 4 × M2.5 on Ø39 and 4 × M2.5 on the inner circle, all on 0/90/180/270°, 3 deep | **Ø28.** Jamie confirms the AS5600 mounts through its corner slots (Ø28–34) into these inner holes, which a Ø26 circle could not do. The table's Ø26 and the drawing's pixel scale were wrong. Not caliper-measured |
| Rotor face holes | 4 × M2.5 on Ø15 (0/90/180/270°) and 4 × M2.5 on a 14 mm square (45°, diagonal 19.6), 3.5 deep | Drawing. Table's "Ø49" cannot fit a Ø45 rotor. Accessories use only Ø15 |
| Screw engagement | ≤ 3 mm stator (table); 3.5 mm rotor (drawing) | Use ≤ 3 mm on both |
| Motor lead | 3-wire PH2.0-3P from a tab at the stator rim, about 225° (between the 180° and 270° holes) | Drawing; measure the angle |
| Encoder magnet | Diametric ring OD10 × ID5.5 × 2.5 at the stator-face end of the shaft | Table + section |
| Bearings / mass | Two 6800ZZ / 145 g | Drawing / table |

Electrical data for driver setup (supplier table):

- 11 pole pairs, so electrical angle = 11 × mechanical. Delta winding.
- 5.4 Ω per phase and 3.6 Ω terminal-to-terminal. These agree: a delta reads 2/3 × 5.4 between two leads.
- 1.3 mH (convention not stated).
- 12–36 V (40 V max); at 24 V: 1,000 rpm, 1.4 A, 0.32 N·m rated. Peak 0.68 N·m; stall 4.9 A.
- Kv 54 rpm/V implies 0.177 V·s/rad, the table states 0.16 V/(rad/s), and Kt is 0.23 N·m/A. The conventions differ; identify them on the driver.

## Encoder boards

| Board | Outline | Mounting | Height |
|---|---|---|---|
| AS5600 (Jamie's) | 33 × 33 with concave sides | 4 diagonal slots 3.1 wide spanning Ø28–34; 2 axis slots 2.9 wide spanning 16–19 spacing. Mounted on the motor's inner Ø28 holes through 2 opposite corner slots, on silver hex standoffs of about 4–5 mm. Brass 7 mm standoffs continue below the PCB | PCB 1.6, chip 1.7 above PCB, PH2.0-4P connectors below; 8.8 overall |
| MT6701 (supplied) | Round, size not given | 4 brass standoffs, apparently on the inner circle | Not given |

Both boards hang from the **motor's own inner holes** on standoffs, so the board's
standoff length sets the magnet-to-chip gap. The stand must not set or load it.
Jamie's stack is recorded in `measurements/2026-10-11_bldc4015_as5600_mount_jamie_01.yaml`:
motor face, then silver 4–5 mm standoff, PCB, and brass 7 mm standoff. Below the motor face, that
puts the PCB at −4 to −5 mm and the brass ends at about −13. The brass ends must not be
used to mount the motor, because that would route motor torque through the PCB.

## Hole sharing with the encoder

Both stator hole circles lie on the same four axes (0/90/180/270°), only 5.5 mm apart
radially. A standoff hex and a stand screw head therefore cannot share an axis. Jamie's
AS5600 hangs on **two** standoffs in one opposite pair of inner holes, so the other pair
is free. Rule: **the encoder takes one opposite pair, and the stand takes the
other.** A board needs only two standoffs, so the MT6701 can follow the same rule.

## Proposed stand: two-screw motor plate + open encoder cavity

```
        indicator disc Ø60 (rotor, Ø15 screws)          fixed index post
             ┌───────────────────────┐                     │▌
        ┌────┴───────────────────────┴────┐                │▌
        │ rotor bell Ø45 × 19.5 — TURNS    │  ≥3 mm gap     │▌
        ├──────────────────────────────────┤ ← seam         │▌
        │ stator section 5.5 — stationary  │                │▌
   ┌────┴─ motor plate, 2.5 floor + pocket ─┴────────────────┴▌───┐
   │  CSK screw ▼  standoff slot ║ 4–5 mm ║  ▼ CSK screw          │
   │                 ════ encoder board (any size ≤ ~55) ════      │
   │            open cavity Ø80, windows: probe + cables           │
 ══╧═══════════ base plate + clamp lips / screw-down holes ════════╧══
```

1. **Motor plate.** About Ø86 × 4 mm, part of the pedestal top, leaving a 2.5 mm floor under the motor.
   With 4–5 mm standoffs, the PCB clears the floor underside by 1.5–2.5 mm.
   - A 1.5 mm Ø45.4 pocket centers the motor, staying 4 mm below the rotor seam.
   - **Screw axes** (one opposite pair): countersunk M2.5 holes at both Ø28 and Ø39.
     M2.5 × 5 countersunk screws through the 2.5 mm floor give 2.5 mm of engagement, inside the 3 mm hole depth.
     The heads sit flush, so nothing projects into the cavity.
   - **Encoder axes** (the other pair): radial slots 6.5 mm wide from r 11 to r 22.5,
     so standoffs fit either hole circle.
   - Ø16 center hole for the rotating boss. Notches at all four 45° positions, so the
     motor lead exits whichever way the motor is turned.
   - Rotating the motor 90° on the plate swaps which pair the encoder uses.
2. **Assembly order.** Screw the motor to the plate first, then fit the standoffs through
   the slots, then the board. Two M2.5 screws at r = 19.5 carry the 0.68 N·m peak at about
   17 N each.
3. **Encoder cavity** about Ø80 × 40 below the plate.
   - It takes a board from a small round MT6701 up to about 55 mm square, on standoffs
     from about 4 mm (2.5 mm floor + 1.5 clearance) up to the cavity depth. Today's stack
     reaches about 13 mm below the motor face (brass ends); connectors and cables need more.
   - Front window: see, probe and adjust the encoder. Rear window: cables, with a zip-tie bar.
   - For standoffs shorter than 4 mm, add a recessed plate variant.
4. **Base plate** about 150 × 120 × 6: front/rear clamp lips, 4 × Ø5.5 screw-down holes,
   bumper recesses, and an optional driver deck later.
5. **Fixed index post** at r ≈ 33, outside the Ø60 disc, at disc height, for a zero reference.

## Indicator disc: built

The orange test gear's successor is designed and checked: `specs/indicator_disc_v1.yaml`,
`cad/parts/indicator_disc.py`, build `builds/indicator-disc-v1/`.

- Ø60 × 3.5 mm orange disc; Ø8 center hole over the hollow bore.
- 4 × M2.5 countersunk on the rotor's Ø15 pattern. With M2.5 × 6 countersunk screws, thread engagement is 2.5 mm.
- Black inlaid markers 8 mm, 0.6 deep, at r = 22: **0° circle, 90° triangle (pointing
  outward), 180° square, 270° cross**. Angles count counter-clockwise viewed from above.
- Printed marker face down for a smooth face; orange slot 4 plus black slot 2, about
  26 min and 9.7 g. Sliced as `builds/indicator-disc-print-v1/disc_orange_black.gcode.3mf`;
  the first layer was verified from the G-code. Not printed yet.

## Risks and reasoning

- **Reaction torque.** The motor pushes up to 0.68 N·m back on the stand; feet alone resist
  about 0.14 N·m (rough estimate). Clamp or screw the base down.
- **Thread depth.** Motor holes allow 3 mm of engagement. Use M2.5 × 5 countersunk screws through the 2.5 mm floor (2.5 mm engagement); longer screws can bottom out or damage the stator.
- **Heat.** PLA softens around 55–60 °C; the motor is rated to 100 °C. The seat and clamp
  touch the stator. Monitor long stall or hold tests, or reprint those parts in PETG.

## Built candidate — v1 (October 11)

Spec `specs/bldc_4015_stand_v1.yaml`, CAD `cad/assemblies/bldc_stand.py`, build
`builds/bldc-stand-v4/` (local, ignored), with an interactive `review.html` (orbit,
cutaway, explode, spinning rotor) and SVG projections in `builds/bldc-stand-v4-views/`.

**Two printed parts**, PLA, no supports, one plate: 2 h 16 min, 99.7 g (`builds/bldc-stand-print-v1/`):

| Part | Size | Notes |
|---|---|---|
| Motor plate | Ø90 × 4 | Motor-specific; Ø45.4 × 1.5 pocket, 2.5 floor, Ø31 center opening, standoff slots on Y, cable notches on the diagonals, 2 countersunk M2.5 on Ø39 (X axis) |
| Tower + base | 150 × 110 × 56 | Ø90 tower, 6 mm wall, Ø78 × 50 cavity, front/rear windows 40 × 32 with 45° pointed tops, 4 × Ø5.5 base holes, rear zip-tie slots, 4 M3 pilots |

**Hardware:**

| Item | Qty | Use |
|---|---:|---|
| M2.5 × 5 countersunk, 90° | 2 | Motor to plate, from below; 2.5 mm engagement |
| M3 × 10 pan head | 4 | Plate to tower; tap the Ø2.5 printed pilots by hand |
| C-clamps or M5 screws | 2 / 4 | Base to desk |
| Existing encoder standoffs | — | Unchanged: silver motor-to-PCB, brass below |

**Assembly:** screw the motor (pocket orientation: its free outer-hole pair on the plate X
axis) to the plate, then fit the silver standoffs through the slots and mount the board.
The board corners cover the motor screws, so remove the board before removing the motor.
Fix the plate to the tower with the four M3 screws, route cables out of the rear window,
and clamp the base.

**Checks: PASS** (84). Valid solids; no overlap with the motor, the rotating bell (3 mm
radial) or the boss. The encoder envelope is swept over standoffs 3–8 mm with a 53 mm
board at any rotation, 25 mm of stack below the PCB, and the chip side within r 15. Jamie's
AS5600 stack is modeled separately; standoffs pass the slots; motor seat and tower support
are present; screw engagement ≤ thread depth; windows leave the base and the wall above
intact. STEP round trips, manifold STLs, Bambu import of both parts.
75 tests pass, including seeded defects.

**Changes found in review:**
- Arched windows became 45° pointed tops. A cylinder-through-cylinder cut did not survive
  STEP within the volume tolerance; planar cuts are exact. The tolerance was not changed.
- The first pointed-top cut notched the base under each window. A visual review caught it,
  and new checks prevent it.
- The viewer grouped `motor_plate` with the motor references. Fixed and tested.

**Remaining for physical review:** clearances use supplier nominals and Jamie's approximate
stack. Hole sizes have no process compensation. After printing, check the pocket fit,
screw seating, standoff passage and the PCB-to-floor gap.

## Open inputs

1. Driver board for the base, if any; a deck can be added to the base later.
