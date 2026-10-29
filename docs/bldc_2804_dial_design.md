# 2804 rotor degree dial — v1 development design

Requested by Jamie on October 28, 2026: a white "step-down" plate on top of the 2804 rotor with red
0–360° markings, turning above the fixed Ø90 plate. Jamie chose a Ø110 dial that overhangs the plate
(over a Ø76 dial inside it, or a motor-size cap) and degrees only (no radians).

Specification: `specs/bldc_2804_dial_v1.yaml`. CAD: `cad/parts/rotor_dial.py`. Checks and build:
`src/mech_lab/dial_build.py`. Candidate: `builds/bldc-2804-dial-v1/` (review page `review.html`, views in
`builds/bldc-2804-dial-v1-views/`). The motor, plate and tower come from `specs/bldc_2804_plate_v1.yaml`.

## Parts

| Part | Description |
|---|---|
| Dial (white + red) | Ø110 × 3.5. Underneath, a 1 mm step (Ø34.8) drops over the rotor rim and centers the dial; 2.5 mm hub on the rotor face; Ø8 center hole keeps the hollow shaft open |
| Dial screws | 4 × M2.5 × 5 countersunk into the rotor face (Ø16, on the axes). 2.5 mm into the rotor; the supplier limit is 3 mm |
| Scale (red inlay, 0.6 deep, flush) | 72 ticks: every 5° (3 mm), longer every 10° (5 mm), longest every 30° (7 mm, 1.2 wide). Numbers every 30° in Arial Bold, about 5.9 mm tall, reading outward. A triangle marks 0 |
| Pointer (red) | Clamped under the plate's M3 screw at 315° (front right) with Jamie's existing M3 × 10 in a counterbore (4 mm into the tower pilot instead of 5). A lip hooks the plate rim so it cannot swing. The tip stops 1.5 mm outside the dial rim, level with the dial face |

**Direction.** The numbers increase clockwise around the dial, seen from above, like a clock face. Zero
sits on the rotor's +Y screw hole. Because the dial turns under a fixed pointer, the reading under the
pointer goes **up when the rotor turns counter-clockwise** seen from above, which is positive rotation
about the rotor-up axis. The motor-to-encoder zero is arbitrary, so the dial is zeroed against software,
not the other way round. `scale_direction` flips the whole scale if the other sense is wanted.

**Access.** The dial covers the four plate screws. Remove the four M2.5 screws to reach them.

## Print

- **Dial:** face down on Textured PEI, so the scale is in the first three layers and the face has the
  plate texture. P2S, 0.4 mm, 0.2 mm layers, Bambu PLA Basic white plus red: **52 min 17 s, 24.6 g
  white and 1.0 g red, 4 colour changes** (`builds/bldc-2804-dial-print-v1/dial_white_red.gcode.3mf`).
  Auto-arrange turned the whole two-part object 11.43° on the bed. The inlay and body turn together,
  so this is harmless. Layer 1 rendered from the G-code (`layer1_from_gcode.png`) shows red in all 72
  ticks, the 12 numbers and the zero triangle. In layers 2–3 the four axis-aligned major ticks are
  hollow outlines, which is hidden under the face.
- **Pointer:** on its side, no supports, red: **11 min 40 s, 1.3 g**
  (`builds/bldc-2804-dial-print-v1/pointer_red.gcode.3mf`).
- **Printed in black instead of red (October 28, Jamie):** no red spool was loaded, so the same STLs were
  re-sliced with black (`builds/bldc-2804-dial-print-v2/`): dial 52 min 13 s, 24.8 g white and 0.9 g black,
  layer 1 again checked for all 72 ticks; pointer 11 min 40 s, 1.3 g black. The dial was started over LAN with
  white from AMS slot 1 and black from slot 2 after a camera check of the bed and **finished with no errors (17/17 layers)**; the camera shows it face
  down on the bed with the rotor step and four countersinks up (`dial_finished.jpg`). Jamie reports it printed
  perfectly. The pointer was started in black from AMS slot 2 after a camera check of the cleared bed.

## Checks (332 PASS)

- The dial is one valid solid of the specified size. Every one of the 85 scale solids is flush with the
  face, does not overlap the body, and body plus scale exactly fill the blank.
- The ticks are at their scale angles (±0.05°). The numbers are within 2° and 1 mm of their places
  and clockwise. The numbers stay 2.1 mm or more from any tick, and the zero triangle 2.8 mm from the "0".
- The hub seats on more than 75% of the rotor face. The step clears the rotor rim by 0.15 mm radially.
  The center hole keeps the Ø6.5 bore open. The screws pass the dial and reach 2.5 mm into the rotor.
- The swept dial plus 1 mm clears the plate, tower, stator ring, all four M3 heads (3 mm tall) and the
  pointer.
- The pointer is one solid. It rests on the plate without overlap, its lip hooks the rim, and its M3 gets
  4 mm into the pilot. Its top is level with the dial face, its tip is 1.5 mm from the rim, at 315°.
- STEP round trips, STL placements and manifold meshes pass for the dial, scale and pointer. Seeded
  defects fail: a reversed scale, an oversized dial, an unhooked pointer and numbers crowding the ticks.

## Risks and open items

- **Rotor nominals.** The Ø16 screw circle, the 3 mm thread limit and the Ø34.5 rim are drawing values.
  If the step does not drop over the rim, sand the step.
- **Inertia.** The dial weighs about 25 g at Ø110, roughly 3.7 × 10⁻⁵ kg·m², likely several times the bare rotor (not measured).
  Expect to retune velocity and position loops with it on. It also makes a decent test flywheel.
- **Legibility.** Glyph stroke widths are not checked geometrically. The first-layer render looks clean.
  0.6 mm ticks are near the limit for a 0.4 mm nozzle.
- **Hardware.** Needs 4 × M2.5 × 5 countersunk screws. M2.5 × 6 would go 3.5 mm into the rotor and is
  not allowed.
- Physical fit is unverified. No release or powered test is authorized by this build.
