# Geared string winch for the BLDC stand — v1 development design

Requested by Jamie on October 12, 2026: a controlled torque load for the 4015 motor on
the printed stand. Choices: a 9:1 gear train from a rotor gear to a string drum lifting a
hanging weight, a magnetic encoder on the output shaft, and an 8 inch (203.2 mm) drop.
Purchased parts are the seller nominals from the shopping list; none has been measured.

Specification: `specs/bldc_4015_winch_v1.yaml` (reads the stand spec for the motor,
plate and tower). CAD: `cad/assemblies/bldc_winch.py`. Checks and build:
`src/mech_lab/winch_build.py`. Candidate: `builds/bldc-winch-v2/` with interactive
`review.html` (run the winch, lift slider, cutaway, group toggles).

## Layout

Frame and units are the stand's: motor axis on Z, Z=0 at the motor's stationary face,
rotor face at Z=25, millimeters.

| Item | Value |
|---|---|
| Stage 1 | 26T on the rotor → 78T on shaft A, module 1, 6 mm face, center distance 52 |
| Stage 2 | 23T on shaft A → 69T on shaft B, module 1, 8 mm face, center distance 46 |
| Ratio | (78/26)·(69/23) = **9:1**; output turns the same way as the rotor |
| Shaft A / B | (45.03, −26.00) / (45.03, 20.00); 5 mm D-shafts, 100 mm, flats facing +X |
| Gear planes | Stage 1 Z 27–33 (2 mm above the rotor face); stage 2 Z 35–43 |
| Drum | V groove Ø70 at the bottom (radius 35.15 to the string center), rims Ø76; groove at Z 56 |
| Travel | 203.2 mm = **0.92 output turn** = 8.3 motor turns (2,981°) |
| Pulley | Sheave groove Ø21 on a 625ZZ and M5 bolt, center (90, 55, 45.5) |
| Hanging string | x = 100.65, **25.65 mm beyond the base's +X edge** |
| Deck | Z 61.5–67.5; output magnet top at Z 75, **7.5 mm above the deck** |

Because the full drop is under one output turn, a single-turn encoder on shaft B reads
absolute weight position over the whole stroke. The motor encoder sees about 8.3 turns;
comparing the two shows the gear backlash directly.

Torque for a hanging mass m, before gear and pulley friction: output torque is
m · 9.81 · 0.03515 N·m, so the motor sees m · 38.3 mN·m per kg. Examples: 100 g →
3.8 mN·m; 500 g → 19.2 mN·m (172 mN·m at the drum). The supplier's 0.32 N·m rated motor
torque could ideally put about 2.9 N·m on the output, far beyond anything these printed
teeth have been shown to carry. **The teeth are not load rated. Set a conservative driver
current limit before any powered test.**

## Printed parts (10)

| Part | Size (mm) | Print orientation |
|---|---|---|
| `rotor_gear` (26T) | 28 × 28 × 8 | Teeth face down (counterbores on the bed) |
| `stage_gear_78t_23t` | 80 × 80 × 22 | 78T face down; pinion and set-screw hub on top |
| `output_gear_69t_drum` | 76 × 76 × 26.5 | 69T face down; drum cones are 45° |
| `winch_frame` (with 4 columns) | 151 × 94 × 60 | As assembled, columns up |
| `winch_deck` (with pulley fork) | 120 × 109 × 29 | Upside down: top face on the bed, fork up |
| `pulley_sheave` | 26 × 26 × 6 | Retaining lip down |
| `magnet_holder` | 10 × 10 × 7 | Magnet pocket up |
| `spacer_a_lower`, `spacer_a_upper`, `spacer_b_lower` | Ø8 × 19.5 / 12.5 / 27.5 | Upright |

No part needs supports in these orientations. The STLs in `print/` are already placed
in these orientations. Not sliced yet.

## Hardware

| Qty | Part | Use |
|---|---|---|
| 5 | 625ZZ 5×16×5 | Frame A/B, deck A/B, pulley |
| 2 | 5 mm D-shaft, 100 mm | Shafts A and B, uncut; the lower ends hang beside the tower |
| 4 | M2.5 × 6 socket head | Rotor gear to the rotor face (2.5 mm engagement, 3 mm allowed) |
| 4 | M3 × 16 | **Replace the plate screws**: frame + plate + 6 mm into the tower pilots |
| 4 | M3 × 16 | Deck to the columns (10 mm into 12 mm pilots) |
| 2 + 2 | M3 × 4 set screw + M3 nut | Shafts A and B, on the flats, nuts in slots |
| 1 + 1 | M5 × 20 + nylock nut | Pulley axle |
| 1 | 6 × 2.5 diametric magnet | Output encoder |
| — | M2.5 male-female standoffs | Encoder board to the deck's Ø28 pilots (8 positions, 45° apart) |

The shaft collars from the shopping list aren't needed: printed spacers locate the
shafts between the bearing inner races. Keep the collars as spares.

## Assembly order

1. Remove the four plate screws. Fit the rotor gear with 4 × M2.5 × 6.
2. Press two 625ZZ into the frame from above. Seat the frame on the plate and fit
   4 × M3 × 16 through the frame and plate into the tower.
3. Shaft A: lower spacer, then the 78T/23T gear (78T down; nut in its slot), then the
   upper spacer. Slide the shaft in from the top through the lower bearing, mesh the 78T
   with the rotor gear, and set the screw on the flat.
4. Shaft B: lower spacer, then the 69T/drum (nut in its slot, dropped in from the top
   face). Slide the shaft in, mesh, and set the screw.
5. Press two 625ZZ into the deck from below and the pulley bearing into the sheave.
   Bolt the sheave into the fork. Lower the deck onto the shafts and columns; 4 × M3 × 16.
6. Push the magnet holder onto shaft B with the magnet in it. Mount the encoder board on
   standoffs from the deck pilots.
7. Thread the string through the drum anchor (radial hole at −X, out the top face) and
   knot it. Wind it under one turn, take it over the pulley, and hang the weight.

## Encoder magnet gap

The magnet top is 7.5 mm above the deck. The gap is set by the standoff length you
choose for the board: gap = standoff − 7.5 − (chip height, if the chip faces down).
This design deliberately doesn't pick a gap. The board envelope checked is a 53 mm
square at any rotation, from the deck up 25 mm.

## Checks (365 PASS)

- Every printed part is one valid solid. No static overlaps among the printed parts,
  stand, motor and all hardware. The only exceptions are intended threads: screws in
  their pilots, set screws in their nuts, and rotor screws in the rotor.
- Every rotating part lies inside its rotation envelope. Those envelopes clear all fixed
  parts by 1 mm, and clear each other across axes by 1 mm (about 0.7 mm normal on the 45°
  drum cones). Nothing on shafts A or B enters the space above the rotor bell.
- Both meshes are swept through one full pinion tooth with the interval bound used for
  the gearbox. Minimum gaps are 0.090 and 0.090 mm, and the contact ratios 1.72 and 1.70.
  A seeded quarter-pitch phase error is detected.
- String run, hanging string and full weight travel are clear of every part and
  envelope. The weight's edge is 10.65 mm past the base edge (5 mm required).
- Screw engagement, both bearings on each shaft, magnet-holder engagement, and the
  encoder envelope are all checked.
- STEP round trips, grounded print STLs and manifold meshes all pass. The review
  renders with WebGL error 0.

## Risks and open items

- **Current limit.** As above: the motor can strip printed teeth. Start with light
  weights and a low current limit.
- **Backdriving.** A printed 9:1 spur train will backdrive. If the driver faults, the
  weight drops and spins the motor at 9× drum speed. Put something soft under the
  weight, and set firmware travel limits from the output encoder. There is no hard stop
  at the top, so the weight can be wound into the pulley.
- **Returned energy.** Lowering under control pushes energy back to the driver.
  A bench supply can't absorb it; watch the bus voltage on fast descents.
- **Clamp the stand.** The weight hangs 25 mm past the base edge, and the motor reacts
  against the base. Screw or clamp the base to the desk through its Ø5.5 holes.
- **Fits are nominal.** Bearing seats are 16.1 mm and D-bores 5.2 mm with a 2.1 mm flat
  offset, with no process compensation. Measure the bearings and shafts when they
  arrive, then print a fit coupon before the big parts.
- **PLA.** Bearing seats creep and soften with heat. Avoid long stalls; consider PETG
  for the frame and deck if the motor runs warm.
- Weight envelope (Ø30 × 60) is an assumption until the hooked weight set arrives.
