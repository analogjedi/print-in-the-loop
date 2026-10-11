# First physical print — compound gear 2 test (October 11, 2026)

Jamie asked to print one gearbox gear as a test on the Bambu Lab P2S and chose the
orange AMS slot and LAN delivery. This is a one-part geometry test, not a release,
fit approval or calibration. No acceptance threshold, CAD dimension or process
compensation was changed. Evidence lives under the ignored `builds/gear2-testprint-v1/`.

## Part and orientation

`builds/gearbox-v4/print/compound_gear_2.stl` (60T/20T, Ø62 × 9 mm) was chosen because
it is the plain compound gear; G1 differs only by adapter attachment holes. As exported,
the 20T pinion is on the plate and the 60T gear overhangs it by about 2,700 mm²
(measured from downward-facing triangles). The print copy is rotated 180° about X
and regrounded: the large gear face sits on the plate (2,774 mm²) and needs no supports.
The remaining overhang is the pinion's 222 mm² step over the 1 mm hub, bridged without support.

| Artifact | SHA-256 (prefix) |
|---|---|
| Source STL `gearbox-v4/print/compound_gear_2.stl` | `d9b4438d5e6d…` |
| Flipped STL `compound_gear_2_large_face_down.stl` | `3c887440b485…` |
| Printed job `gear2_orange.gcode.3mf` | `fdcc82976b86…` |

Bambu `--info` on the flipped mesh: one manifold part, 61.95 × 61.95 × 9.00 mm.

## Printer configuration observed

Read-only MQTT status from the printer itself, not assumed:

- Bambu Lab P2S (model ID N7), LAN Only mode with Developer Mode enabled.
- 0.4 mm hardened-steel nozzle (`HS01`); plate base 4 = Textured PEI.
- AMS 2, unit 0: slots 1–4 white, black, green, orange; all Bambu PLA Basic (`GFA00`).
- LAN jobs require a USB stick in the top port. Without one the printer reports
  `sdcard: false` and FTPS uploads fail with `553`.

The IP address, access code and serial are on the printer's LAN Only screen and TLS
certificate. Keep them out of the repository and logs; refresh the access code
after sharing it.

## Slicing — Bambu Studio 2.8.2.61 CLI

Stock presets: `Bambu Lab P2S 0.4 nozzle`, `0.20mm Standard @BBL P2S`,
`Bambu PLA Basic @BBL P2S`, Textured PEI. Result: 45 layers, 2 walls, 20% infill,
no supports, 9.01 g, 20.6 min of model time and 27.6 min in total.

CLI pitfalls found:

1. **System presets are not resolved.** Passing the system JSON files directly gave a
   generic `G28; G1 Z5` start G-code with no AMS load, bed leveling or purge, and
   filament density 0. That job would have printed air. Flatten each preset first:
   merge its `inherits` chain (parents first) and its `include` templates (machine
   start/end/change G-code), then the leaf keys.
2. **Plate defaults to Cool Plate.** Set `curr_bed_type: "Textured PEI Plate"` in the
   flattened process JSON; PLA Basic then uses 55 °C.
3. `--export-3mf` needs an absolute path; `--export-png` cannot be combined with `--slice`.
   The CLI writes `result.json` into the current directory.
4. The `Invalid T command (T65535)` log error comes from the normal end-G-code AMS
   unload sentinel, not a defect.
5. `printer_model_id` stays blank in CLI output; the printer accepted the job regardless.

Verify after every CLI slice: header settings, `curr_bed_type`, the full P2S start
block (`M620 S0A`/`T0` load, `G29` leveling) and the `plate_1.gcode.md5` match.

## LAN delivery to the P2S

1. FTPS (implicit TLS, port 990, user `bblp`): upload to `/cache/<name>.gcode.3mf`.
2. MQTT over TLS (port 8883, topic `device/<serial>/request`), H2-style `project_file`:
   `url: ftp:///cache/<name>`, `file`, `param: Metadata/plate_1.gcode`, plate G-code
   MD5, matching **non-zero** `project_id`/`task_id`/`subtask_id`, integer 0/1 flags,
   `auto_bed_leveling: 1`, `cfg: "0"`, `nozzle_offset_cali: 2`, `ams_mapping: [3]`,
   `ams_mapping2: [{ams_id: 0, slot_id: 3}]`.

The P1/X1-style `url: file:///sdcard/<name>` with zero IDs was rejected: reply
`ERROR STATE`, `print_error 0x05004002` "Unsupported file path or name". It started
nothing, and the printer cleared the error. The working payload follows
[bambu-printer-mcp PR #15](https://github.com/DMontgomery40/bambu-printer-mcp/pull/15),
which reports it verified on P2S firmware 01.02.00.00. The printer answered
`SUCCESS`, then `PREPARE` → `RUNNING`.

Before starting, a camera frame (`rtsps://…:322/streaming/live/1`, LAN Only Liveview)
confirmed an empty plate. A read-only watcher logged status each minute and saved frames
to `builds/gear2-testprint-v1/frames/`.

These commands were run as one-off session scripts for this Jamie-approved print.
They were not added as project tools. AGENTS.md still states no printer control is
implemented; adding such a tool is a policy change for Jamie to review.

## Outcome and next checks

At the time of this record the job was printing. Record the outcome and any
measurements as new files under `measurements/`; never edit earlier records. Check:

- Bore against the Ø5.4 mm nominal (shaft Ø5.0 mm, 0.4 mm diametral clearance).
- Tip and root diameters against nominal: 60T outside Ø62.0, 20T outside Ø22.0.
- Pinion tooth underside, where it steps over the hub, for droop.
- First-layer elephant foot on the 60T teeth, which affects mesh with a second gear.

Fit with mating gears and shafts remains BLOCKED until more parts are printed and measured.
