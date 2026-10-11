# Gearbox layout for review — September 7, 2026

**Historical layout milestone:** detailed CAD is now implemented under G001/G002.
See the [completed build and assembly guide](gearbox_build_and_assembly.md) and
[current verification status](status.md). Open-input statements below describe the
earlier proposal, before Jamie authorized reasonable trial assumptions.

**27:1 layout approved by Jamie for a test run on September 7, 2026 (G001).**
The chosen servo is Waveshare ST3215; its
[published dimensions](waveshare_st3215_dimensions.md) await Jamie's confirmation.
This layout milestone does not establish manufacturing fits or a working servo connection.
See the [handoff](../latest_progress_sept_7_2026.md). The original generated drawing's
“proposed” label reflects its creation before this approval.

## Proposed topology and dimensions

Four compound assemblies, G1 through G4, each have a 60-tooth large gear and a
20-tooth pinion behind it, toward the back plate. The two gears rotate together.
The servo drives G1; P1 drives G2, P2 drives G3, and P3 drives G4. P4 remains part
of the requested compound geometry but does not add another reduction stage.

| Parameter | Proposed value |
|---|---|
| Number of compound assemblies / reduction meshes | 4 / 3 |
| Teeth per large gear / pinion | 60 / 20 |
| Module / pressure angle / profile shift | 1 mm / 20° / 0 |
| Reduction per mesh / total | 3:1 / 27:1 |
| Output speed relative to input | −1/27 (opposite direction) |
| Nominal pitch diameters, large / small | 60 / 20 mm |
| Nominal tip diameters, large / small | 62 / 22 mm |
| Adjacent shaft spacing | 40 mm |
| Face width, both gears | 4 mm |
| Axial spacing between large gear starts | 5 mm |
| Nominal plastic shaft diameter | 5 mm; fit and retention unresolved |
| Preliminary plate | 174 × 109 × 5 mm |

These numbers are candidate design variables, not purchased dimensions or printer
calibration values. A 27:1 reducer also reduces a positional servo's available output
angular travel by 27; the intended motion and servo type must be agreed before freezing
the ratio. No torque capacity or efficiency is established.

Nominal pitch diameter is module × tooth count; center distance is half the sum of
the mating pitch diameters. Standard unshifted tip diameter is module × (teeth + 2).
Reference: [KHK, gear dimension calculations](https://khkgears.net/gear-knowledge/gear-technical-reference/calculation-gear-dimensions/).

## Layout and axial stack

Coordinates are millimeters, right-handed, +Z away from the plate. The back plate
occupies Z=0…5. “Behind” means closer to that plate. Shaft axes are parallel to Z.

| Assembly | Shaft X | Shaft Y | Large gear Z span | Rear pinion Z span |
|---|---:|---:|---|---|
| G1, servo input | 37 | 37 | 27…31 | 22…26 |
| G2 | 77 | 37 | 22…26 | 17…21 |
| G3 | 97 | 71.641016 | 17…21 | 12…16 |
| G4, output | 137 | 71.641016 | 12…16 | 7…11 |

A coaxial connecting hub must bridge the 1 mm gap between the two gear faces in
each assembly. Adjacent large gears have 1 mm nominal axial separation. The rear
pinion of G4 starts 2 mm above the plate. These are nominal CAD separations, not
validated printed running clearances. Shaft lengths and retention must accommodate
the different heights.

The zigzag shaft arrangement packs the four axes into the plate footprint while
keeping nonadjacent gear tip envelopes apart. Servo mounting and its keep-out volume
are **excluded from the preliminary plate envelope** until the actual servo is known;
the overall gearbox size is therefore unresolved.

Run `.venv/bin/python tools/propose_gearbox.py --output builds/gearbox-layout-v1`
to create an envelope drawing and a numerical layout report. Use a new path on reruns.
Circles in that drawing represent pitch/tip envelopes; they are not manufactured
tooth profiles. Intended mating tooth-tip circles overlap; that is not by itself a
collision result. Detailed teeth, phasing, and motion checks remain to be implemented.

## Required input before detailed CAD

1. Four compound assemblies (three meshes), 27:1: approved for the test layout (G001).
2. Waveshare ST3215 selected. Confirm the published dimensions and resolve spline/horn details,
   retention screw and mounting geometry. Choose direct engagement or attachment to
   its supplied horn. Resolve how the servo input and the plastic shaft support coexist.
3. Review the proposed size/ratio and clarify intended motion, speed/load, material,
   physical printer setup, retention approach, and measured fit allowances as needed
   for the intended build/release scope.

## Verification status

The generated report checks nominal center spacing, matching axial mesh spans,
nonadjacent tip-envelope separation, and plate envelope containment. These checks
support layout review only. Detailed solid validity, tooth contact/interference over
motion, shaft/bore fit, retention, servo compatibility, and physical verification are
BLOCKED until their geometry and inputs exist. Release and print remain BLOCKED.
