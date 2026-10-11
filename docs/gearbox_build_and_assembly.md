# 27:1 ST3215 gearbox trial

Four compound 60T/20T gears run on plastic shafts integral with a 174 × 109 × 5 mm
back plate. Three external meshes reduce speed 27:1 and reverse the output direction.
Each small pinion is behind its large gear, toward the plate. The servo sits above G1
in a removable cradle and drives it through its supplied metal horn and a printed adapter.

Authoritative CAD is in `cad/assemblies/gearbox.py` and `cad/parts/spur_gear.py`;
the validated inputs are in `specs/gearbox_v1.yaml`. G001 records Jamie's layout
approval and G002 his authorization to make reasonable development assumptions.
[D003](../decisions/0003-gearbox-trial.md) records those choices and their limitations.

## Build and review

```bash
.tools/uv/bin/uv run --locked validate_spec specs/gearbox_v1.yaml
.tools/uv/bin/uv run --locked build_design specs/gearbox_v1.yaml --output builds/my-new-gearbox --timeout 600
```

Use a new output path when rebuilding. The larger explicit timeout accommodates
multi-part STEP round trips and collision checks; acceptance tolerances are unchanged.
The build contains:

- `assembly.step`: all printable parts and the purchased-servo reference in position.
- `parts/*.step`: individual parts in assembly coordinates.
- `print/*.stl`: each printable part centered in XY and grounded at Z=0.
- `review.html`: self-contained interactive 3D view using actual exported meshes,
  orbit/zoom, explode, servo/cradle visibility and geared animation.
- Geometry, motion, and build manifests, including source and artifact hashes.

The completed development build is in `builds/gearbox-v4/`: 15 printable parts,
174 × 109 × 75.9 mm assembled, excluding projecting hardware and cables. All 49
tests and the candidate geometry/motion checks passed. Independent STEP inspection,
Bambu mesh import and browser review are recorded in `docs/status.md`. Scroll to
zoom out when using the full exploded view.

The purchased servo reference is excluded from the printable set. One vendor casing
solid is invalid (`BRepCheck_SubshapeNotInShape`), and other vendor solids did not
survive STEP re-export within the existing volume tolerance. The assembly therefore
uses three simplified, dimensioned reference solids: the case envelope, front horn,
and rear wheel envelope. Body bounds and horn mounting dimensions come from the
supplier geometry; spline teeth, threads and internal details are omitted.
`servo_reference_report.json` records the substitution. The original vendor STEP
is preserved separately and unchanged; no fully repaired supplier model is claimed.
STL placements are starting orientations, not sliced or approved printer jobs.
Compound gears are exported pinion-down, leaving the 60T gear unsupported; print them
flipped with the large gear face on the plate ([first_print_gear2.md](first_print_gear2.md)).

## What you need beyond the printed parts

Keep your ST3215, its matching metal horn and original center retaining screw.
For the current mechanical design, gather:

| Nonprinted item | Quantity | Use |
|---|---:|---|
| M3 × 6 countersunk screws, 90° head | 4 | Metal horn to printed adapter |
| M3 × 8 countersunk screws, 90° head | 4 | Input gear to adapter |
| M3 × 8 pan-head screws | 3 | Gear shaft retainers |
| M3 threaded rod, 85 mm length | 4 | Cradle tie rods; longer stock can be cut to fit |
| M3 hex nuts | 12 total | 4 captive adapter nuts plus 8 cradle nuts |
| M3 flat washers | 8 | Cradle tie rods |
| Thin case shims | As needed | Remove case movement after checking the actual fit |

These are trial hardware dimensions. Check that the supplied horn's four mounting
holes accept M3 threads before buying its screws; the supplier CAD shows Ø2.5 mm
holes but does not establish their thread. Verify screw engagement and flush head
seating during assembly. No separate bearings or metal gear shafts are needed by
this design: the gears run directly on the printed plastic shafts.

## Tools and powered-operation equipment

For assembly, have an M3 tap and tap wrench, drivers matching the chosen screw heads,
a small wrench for M3 nuts, calipers, and a deburring tool or small file. If cutting
threaded rod, also have a suitable saw and a file for the cut ends.

For a later powered run, you also need a compatible TTL serial-bus servo controller
or USB bus-servo adapter, a matching servo bus cable, and an external DC supply
matched to your exact servo variant and controller. Add the controller's USB cable
if using a computer. An existing compatible setup can be reused.

Waveshare documents 6–12.6 V for its standard ST3215 and recommends 12 V; the selected
controller can impose its own supply limits. Supply current capacity must accommodate
the servo's load and startup/stall demand. Power and control equipment has not been
selected or tested for this gearbox. Sources: [ST3215 documentation](https://www.waveshare.com/wiki/ST3215_Servo)
and [Bus Servo Adapter A documentation](https://docs.waveshare.com/Bus_Servo_Adapter_A).

## Bill of materials

| Item | Quantity | Trial specification |
|---|---:|---|
| Back plate with four integral plastic shafts | 1 | Printed; shafts nominal Ø5, gears bored Ø5.4 |
| Compound gears | 4 | Module 1, 20°, 60T/20T; G1 has adapter attachment holes |
| Shaft retainers | 3 | G2–G4; G1 retained through servo/horn connection |
| Horn adapter | 1 | Ø50 × 4 mm; horn-hole circle Ø14; outer attachment circle Ø40 |
| Cradle posts | 4 | Printed, through holes for M3 threaded rods |
| Cradle tray and lid | 1 each | Removable frame and locating rails |
| Waveshare ST3215 with supplied metal horn | 1 | Jamie's selected servo; retain its existing center screw |
| Horn-to-adapter screws | 4 | M3 × 6, 90° countersunk; assumed tapped metal-horn holes |
| Gear-to-adapter screws and captive nuts | 4 each | M3 × 8, 90° countersunk; nominal M3 nuts in trial 5.8 mm AF pockets |
| Shaft-retainer screws | 3 | M3 × 8 pan head; tap Ø2.5 mm pilots in plastic shafts |
| Cradle threaded rods | 4 | M3 × 85 mm, trim only after checking the assembled stack |
| Cradle nuts and washers | 8 each | M3, one set above and below each rod |
| Case locating shims | As needed | Fit at assembly; thickness is not a claimed calibration measurement |

Screw heads and threads are not detailed CAD solids. Countersunk seats assume a
6 mm head diameter and 90° included angle; verify the actual hardware. The horn
STEP has four Ø2.5 mm holes but no threads: M3 tapping is an authorized trial
assumption, not a claim that all ST3215 mounting holes are M3. Use the supplied metal
horn to preserve the actual spline fit. Published spline OD is 5.9 mm; Jamie measured
5.8 mm. The corrected measured case footprint is 45.2 × 24.6 mm.

## Assembly sequence for review

1. Inspect printed parts and clear bores without assuming a calibrated fit. Tap the
   three shaft-retainer pilots M3; verify the shaft/bore fit by hand before assembly.
2. Install the cradle posts/rods on the plate. Install G2–G4,
   leaving access to mesh G1. Place the servo in the cradle tray before fitting
   the adapter, so its horn passes through the tray opening. Seat four M3 nuts in
   the adapter's outer hex pockets. Attach the adapter to the
   supplied metal horn with four M3 × 6 countersunk screws from the adapter underside.
   Retain the original center servo screw; the adapter center opening provides access.
3. Attach G1 to the adapter using four M3 × 8 countersunk screws from the underside
   of its large gear into those captive nuts. Heads must be flush with the gear face,
   and tips must not project beyond the adapter into the cradle tray.
4. Lower the servo/tray/adapter/G1 assembly along the cradle posts, seating G1 over
   its plastic shaft and the tray on the post collars. Follow
   the assembly STEP/review tooth phase: initial rotations are 0°, 177°, 198°, 111°
   relative to the generated local tooth-zero direction. Mesh by hand without force.
5. Install G2–G4 retainers and M3 × 8 screws. The retainers seat on shaft ends,
   leaving nominal 0.3 mm axial freedom above each gear; they must not clamp gears.
6. Install the cradle lid, washers and nuts. The tray
   has clearance for the output horn. Fit thin shims to remove case movement without
   distorting the servo housing. Route the two bus connectors upward toward the lid
   access opening; verify plug access and cable bend clearance using the actual cable.
7. Inspect tooth engagement, free motion, retention, screw lengths and cable access.
   Any physical test or powered run requires Jamie's explicit approval separately.

This is a geometry-verified trial design when its reports pass. Trial clearances,
materials, shrinkage, durability, torque capacity, servo load limits in this assembly,
and physical backlash are not established by CAD. One test gear (G2) was printed on
October 11 with stock P2S PLA Basic presets. That is a single-part geometry test, not
a selected production profile or fit result. There is no powered-hardware control.
