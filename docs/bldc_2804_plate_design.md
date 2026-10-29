# 2804 motor plate for the BLDC stand — v1 development design

Requested by Jamie on October 27, 2026: hold a 2804 hollow-shaft outrunner with its AS5600
encoder kit on the existing printed stand. The tower and base are reused unchanged; only
this Ø90 plate is new. Sources: supplier drawings and a kit photo in
[components/drawings/bldc_2804/](../components/drawings/bldc_2804/) (not redistributed;
hashes in `source_checksums.json`). Every motor value is a drawing nominal; none is measured.

Specification: `specs/bldc_2804_plate_v1.yaml`. CAD: `cad/assemblies/bldc_pinned_plate.py`.
Checks and build: `src/mech_lab/plate_build.py`. Candidate: `builds/bldc-2804-plate-v2/`.

## Motor outline (drawing nominals)

| Feature | Value |
|---|---|
| Body | Ø34.5 × 15: rotor cup 11 mm (top, turns), stator ring 4 mm (bottom, fixed) |
| Encoder boss | Ø12, 4.5 mm proud of the stator face, holds the radial magnet; treated as rotating |
| Stator face | 4 × M2.5 on Ø19 at 45° (13.4 spacing), ≤ 4 mm deep; Ø2 × 4 locating hole at r14 |
| Lead | Tab at the stator ring, about 2.6 mm wide. Looking at the stator face: hole at 9 o'clock, lead at 12. From the rotor side the lead is 90° **counter-clockwise** from the hole |
| Rotor face | 4 × M2.5 on Ø16 on the axes, ≤ 3 mm deep (not used here) |
| Hollow shaft | Ø6.5 bore |

## Why no screws into the stator face

The 4015 plate screws through its floor into one pair of stator holes and leaves the other
pair to the encoder. On the 2804 the holes sit at r9.5, only 3.5 mm from the rotating Ø12
boss. A flush M2.5 head there either leaves no plastic between the countersink and the boss
opening, or hangs below the floor where the encoder board goes. Instead:

- **Pocket.** The 4 mm stator ring drops 2.5 mm into a Ø34.8 pocket. Its rim stays 1.5 mm
  below the rotor cup.
- **Crush ribs.** Six vertical ribs (Ø1.5) reach 0.15 mm inside the ring's radius and grip
  it. They have lead-in tips and skip the lead notch.
- **Pin.** A printed Ø1.8 × 3 pin on a floor tab engages the Ø2 locating hole and takes the
  motor torque. If it shears, drill it out and fit a short 2 mm rod.
- **Center opening Ø27.** This clears the boss by 7.5 mm radially and passes encoder
  spacers on **any** of the four stator holes. The board can use either diagonal pair in
  any orientation.
- **Lead notch** 7 mm wide at 90°, through the plate, so the lead can drop into the tower
  toward the rear window.

## Encoder kit

The kit uses the same 33 × 33 AS5600 board as the 4015. Its two center slots (16–19 mm
spacing) take one diagonal pair of the Ø19 holes, with the chip toward the magnet and the
PH2.0 connectors (5.4 mm) away from it. The kit's motor-to-board spacing isn't given
anywhere. The boss plus the chip imply at least about 6.2 mm. The plate is checked against
any spacing from 4.5 to 10 mm. The review shows 7 mm for illustration only. The stand never
sets or loads the magnet gap.

## Print

One part, 90 × 90 × 5.4, printed as assembled: underside on the bed, pin and ribs up, no
supports. A trial slice (`builds/bldc-2804-plate-slice-v2/`, P2S, 0.4 mm, Bambu PLA Basic
black, Textured PEI, 0.2 mm layers, 15% infill) gives **29 min 34 s total and 16.8 g**.
The start block matches the 4015 stand print (bed leveling, AMS load).

**Printed October 27, 2026**, with Jamie's approval, in **white** Bambu PLA Basic (AMS slot 1). It was
re-sliced from the same STL (`builds/bldc-2804-plate-print-v1/`; the G-code is identical apart from the
colour tag) and sent over LAN. It finished with all 27 of 27 layers, `print_error 0` and no new HMS notices.
**Fit, October 28 (Jamie):** the motor fits right in the plate, and the Ø1.8 pin goes into the Ø2 locating hole with some force. Rib grip and the kit's board spacing are not reported yet. A second tower and base in white printed
straight after (`builds/bldc-stand-tower-white-print-v1/`, same STL as the 4015 tower, about 1 h 56 min and
86 g) so that both motors can stay mounted. It finished with all 280 of 280 layers, `print_error 0` and no
new HMS notices, and the camera shows a clean part.

## Assembly

1. Unscrew the 4015 plate (4 × M3 × 10) and lift it off the tower.
2. Mount the encoder kit on the 2804 as supplied.
3. Feed the encoder cable and motor lead down through the opening and notch. Press the stator
   ring into the pocket with the locating hole over the pin. Ribs should take firm thumb
   pressure.
4. Fit the plate to the tower with the same 4 × M3 × 10 (5 mm thread engagement in the
   tapped pilots). Route cables out through the rear window.

## Checks (79 PASS)

- The plate is one valid solid. Its only overlap with the stator ring is the crush-rib
  interference (0.97 mm³ in total). The pin fully enters the locating hole without
  touching its wall, and the seat supports over 75% of the stator annulus.
- It is clear of the rotating cup (3 mm radial) and boss (1 mm), and the lead envelope
  passes the notch.
- Over six spacings from 4.5 to 10 mm, it is clear of the largest encoder envelope
  (53 mm board at any rotation, chip side, 25 mm below the PCB) and of standoffs on all four
  stator holes.
- It sits on the tower top without overlap and covers the tower. The M3 screw paths are
  clear, with 5 mm engagement.
- STEP round trip, STL placement and a manifold mesh all pass. Seeded defects fail: a pin
  off by 5°, an undersized pocket, a small opening, a blocked notch and a thicker floor.

## Risks and open items

- **Rib grip is uncalibrated.** 0.15 mm interference with no process compensation. Too
  tight: shave the ribs with a knife. Too loose: a drop of hot glue or tape on a rib. Either
  way the result tells us this printer's pocket allowance.
- **Lead position is from the drawing.** The pin allows only one orientation. Before
  printing, check on the motor that, looking down on the rotor, the lead leaves the stator
  ring 90° counter-clockwise from the small Ø2 hole. If not, change `lead_angle_deg` and
  rebuild.
- **Axial retention is friction only.** Fine on a desk; add a retainer before side loads
  like the winch.
- Motor and pin fit are confirmed by hand (October 28). Rib grip, the board spacing and anything
  powered are still unverified. No release or powered test is authorized by this build.
