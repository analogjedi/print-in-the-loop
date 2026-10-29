# Foundation status

Latest handoff: [September 7 progress and proposed gearbox project](../latest_progress_sept_7_2026.md),
then [October 11 first print](first_print_gear2.md). Proposed next project:
[4015 BLDC face-up evaluation stand](bldc_4015_stand_proposal.md) — rev. 3 (two-screw motor plate; the encoder
uses the other hole pair, so either board fits); v1 CAD built (`specs/bldc_4015_stand_v1.yaml`,
84 checks PASS, 75 tests pass, interactive review in `builds/bldc-stand-v4/review.html`);
sliced at 2 h 16 min, 99.7 g; printed 13:04–15:29 in black PLA, completed with no error;
physical fit not yet checked; Jamie reports the whole assembly worked. Next: a
[geared string winch](bldc_winch_design.md) as a controlled torque load — 9:1, output encoder,
203.2 mm drop (`specs/bldc_4015_winch_v1.yaml`); v1 CAD built in `builds/bldc-winch-v2/`,
365 checks PASS, 92 tests pass; purchased parts not yet measured, not sliced or printed,
teeth not load rated. Its review page is published with GitHub Pages at
https://analogjedi.github.io/print-in-the-loop/winch/ (copied into `site/`; see `site/README.md`).
A second motor plate for the same tower holds a [2804 outrunner](bldc_2804_plate_design.md)
with its AS5600 kit by the stator ring (pocket, crush ribs, pin in the Ø2 locating hole; no
screws into the stator face); `specs/bldc_2804_plate_v1.yaml`, built in `builds/bldc-2804-plate-v2/`,
79 checks PASS, 110 tests pass; printed October 27 in white PLA (29 min, 16.8 g, no errors),
second white tower printed the same evening (1 h 56 min, 86 g, no errors) so both motors stay mounted. October 28: Jamie reports the motor fits the pocket
and the pin goes into the locating hole with some force; rib grip and the kit's board spacing are not yet reported.
A [degree dial](bldc_2804_dial_design.md) for the 2804 rotor (Ø110 white, red inlaid 0–360° scale, red
pointer on a plate screw; `specs/bldc_2804_dial_v1.yaml`, `builds/bldc-2804-dial-v1/`, 332 checks PASS) is
being printed October 28 in white with black markings instead of red: the dial finished with no errors
(52 min, 24.8 g + 0.9 g) and Jamie reports it printed perfectly; the pointer (12 min, 1.3 g) is printing
after it; 128 tests pass.
The rotor indicator disc
(`specs/indicator_disc_v1.yaml`) is built but on hold for a second motor type.
Jamie reports enabling Terminal Accessibility; the subsequent check in the existing
session still returned `false`. Relaunch and recheck before resuming GUI commissioning.

## October 11: first physical print — compound gear 2

At Jamie's request, one gearbox part was sliced and sent to the P2S over LAN:
`compound_gear_2`, flipped so the 60T face is on the plate, with no supports.
Stock P2S 0.4 / 0.20 mm Standard / PLA Basic presets, Textured PEI, orange AMS slot,
9.01 g, about 28 min. Full record: [first_print_gear2.md](first_print_gear2.md).

| Check | Status | Evidence / scope |
|---|---|---|
| Printer configuration | PASS | Read from the printer: 0.4 mm hardened-steel nozzle, Textured PEI, AMS 2 with four PLA Basic spools. |
| Slice | PASS | `builds/gear2-testprint-v1/gear2_orange.gcode.3mf`; flattened system presets, full P2S start block, MD5 matches. An earlier unflattened CLI slice was defective and was not sent. |
| LAN delivery | PASS | FTPS upload to `/cache/`; H2-style `project_file` accepted; printer reached `RUNNING`. A first P1-style attempt was rejected (0x05004002) without starting. |
| Print completion | PASS | `FINISH`, `print_error 0`, 45/45 layers; final camera frame shows a complete gear. Two HMS notices logged during the job have not been looked up. |
| Printed-part measurements | BLOCKED | Measure bore, tip diameters, pinion underside and first layer; record in `measurements/`. |
| Gear fit and mesh | BLOCKED | Needs printed mating parts and measurements. |

The printer was driven by one-off session scripts. No printer-control tool was added;
AGENTS.md policy is unchanged.

## Gearbox continuation — September 7: development CAD complete

Jamie selected Waveshare ST3215, approved the four-compound-gear 27:1 layout (G001),
and authorized reasonable trial assumptions for the end-to-end CAD exercise (G002).
The implemented design has four 60T/20T module-1 gears on integral plastic shafts,
a back plate, retainers, metal-horn adapter and removable servo cradle. It contains
15 printable parts and measures **174 × 109 × 75.9 mm**, excluding projecting hardware
and cables. Three external meshes give an output speed of −1/27 of the input.

Current candidate: [builds/gearbox-v4](../builds/gearbox-v4/).
The updated [HTML review with assembly guide and BOM](../builds/gearbox-review-v5/review.html)
embeds the nonprinted hardware list, tools, powered-operation equipment and assembly
sequence. Its `review_manifest.json` records a documentation refresh of unchanged v4
STEP/STL geometry; `geometry_build_manifest.json` preserves the original build record.
[Assembly guide and BOM](gearbox_build_and_assembly.md) records hardware and fits;
[D003](../decisions/0003-gearbox-trial.md) explains the authorized assumptions.

| Check | Status | Evidence / scope |
|---|---|---|
| Regression tests | PASS | 49 tests, including gearbox geometry and seeded mesh/phase defects. |
| Candidate build | PASS | `builds/gearbox-v4/build_manifest.json`; 15 valid printed solids, STEP round trips, grounded manifold STLs. |
| Independent STEP inspection | PASS | `builds/gearbox-inspection-v4.json`; all 18 assembly solids checked against specified geometry and placement. |
| Static and moving clearances | PASS | `geometry_report.json`; printed parts and dimensioned servo references, plus full-revolution moving envelopes against fixed structures. |
| Tooth motion | PASS | `motion_report.json`; 181 samples per mesh across one tooth period, interval clearance bound approximately 0.090 mm; nominal contact ratio 1.671. Software geometry results, not measured manufacturing performance. |
| Bambu native mesh import | PASS | `builds/gearbox-verification-v4/bambu-gear1.txt` and `bambu-backplate.txt`; both one manifold part at expected millimeter dimensions. |
| Interactive review | PASS | `builds/gearbox-verification-v4/browser.json`; assembled, gear-only, exploded and top views inspected; animation/pause/reset and −1/27 endpoint checked, WebGL error 0. |
| Artifact provenance | PASS | All 55 artifact hashes match; CAD/specification/policy/dependency/viewer sources unchanged since build. D003 received a documented explanation-only correction. |
| Physical fit, load capacity, print and powered test | BLOCKED | Hardware threads/lengths, printed clearances, material/process, cables, and actual servo assembly still need physical verification and approval. A single-gear test print began October 11 (see above). |

The supplier STEP has an invalid casing solid and unstable re-export volumes in other
solids. The candidate uses three explicitly dimensioned case/horn/wheel references,
omitting spline teeth, threads and internal detail; it preserves the original supplier
file separately. `servo_reference_report.json` records this limitation. The actual
servo connection uses the supplied metal horn.

Jamie's corrected footprint is **45.2 × 24.6 mm** and measured spline OD **5.8 mm**.
Original records remain unchanged, including the superseded 26.6 mm width. Published
nominal values remain separate: footprint 45.22 × 24.72 mm; Feetech ST-3215-C018 item
6-9 specifies **25T/OD5.9 mm** and item 6-13 **M3 × 6 output retaining screw**.
These do not establish every accessory thread. Source documents and applicability
notes are in [servo dimensions](waveshare_st3215_dimensions.md).

The earlier layout-only report is preserved in `builds/gearbox-layout-v1/`; detailed
CAD supersedes its former input blockers. Desktop commissioning history below remains
separate from completion of this digital gearbox trial. Generated files are local and
ignored by Git. As of September 7, no release, print or powered test had occurred.

## September 7 continuation: desktop configuration and cube/sphere

Implemented the requested parametric cube/sphere model; **41 tests pass**.
Source: `cad/parts/cube_sphere.py`; specification: `specs/cube_sphere.yaml`.
The model is one valid solid: 20 mm cube, radius-8 mm sphere, 1 mm overlap,
20 × 20 × 35 mm overall. Kernel volume: 10,120.575041 mm³. Reopened STEP
checks include sphere radius/center and analytical volume, in addition to bounds.

Installed FreeCAD 1.1.3 (native arm64), Bambu Studio 2.8.2.61 (universal with
arm64), and VS Code OCP CAD Viewer 4.0.1. Python dependencies remain locked.
VS Code selects `.venv/bin/python` through project settings.

Current evidence:

- `builds/cube-sphere-v1/`: STEP/STL, manifest, passing geometry report.
- `builds/cube-sphere-review/`: four standard projections and HTML index.
- OCP standalone viewer: model rendered and visually inspected;
  `output/playwright/cube-sphere-ocp.png`.
- FreeCAD imported both smoke and cube/sphere STEP models: dimensions, solid
  count, validity, and volumes PASS in `builds/commissioning/freecad-verification.json`.
  Native documents and rendered PNGs are alongside the report; the cube/sphere
  render and actual FreeCAD window have been visually inspected.
- Bambu Studio `--info`: one manifold mesh part, 20 × 20 × 35 mm, 6,994 facets.
  Mesh volume 10,116.881836 mm³ differs from the exact solid through tessellation.
  `builds/commissioning/bambu-model-info.txt` records the application’s measurements.
- Bambu’s own `--export-png` preview was visually inspected. The unsliced
  default-profile 3MF was also exported, without printing.
- Installed Bambu P2S machine/process profiles are present. Actual hardware nozzle,
  filament, plate, and process remain unverified.
- Fresh local checkout of `d6705f8`: locked dependencies installed offline into a
  separate environment, all 41 tests passed, and cube/sphere build geometry reports
  exactly match the main worktree. `builds/commissioning/cube-reproducibility.json`.

Remaining desktop interaction: Bambu Studio’s first-run wizard is open. macOS
Screen Recording is now granted, but Accessibility has denied GUI control.
Jamie has been asked to enable Terminal Accessibility or complete the wizard.
The VS Code extension is installed; its in-editor viewer still needs a live check.
Standalone OCP viewing is already operational. See D002 and README for commands.

The earlier foundation snapshot below is retained as history; its original
“apps not found” entries are superseded by the installation evidence above.

Recorded for the continuation begun September 6, 2026. This is an implementation
record, not a declaration that Phases 0–2 have passed all acceptance gates.

## Implemented and tested

- Local Git repository and project-local uv 0.12.10; Python 3.12.6 / native arm64.
- Locked build123d 0.11.1, CAD kernel package 7.9.3.1.1, ocp-vscode 3.4.0,
  Pydantic 2.13.5, PyYAML 6.0.3, and pytest 9.1.1.
- README, shared agent rules, charter, coordinate conventions, decision log,
  unresolved joint specification, empty component registry, proposed release policy.
- Five working CLI commands; strict schema validation and explicit BLOCKED states.
- Parametric smoke part, named assembly/frame, per-part STEP/STL exports,
  build/source/specification/policy manifests and checksums.
- Native and reopened STEP validity, one-solid count, dimensions, origin, and volume.
  Binary STL bounds/scale checks; manifoldness is not evaluated.
- Four standard SVG review projections and an HTML review page.
- Synthetic reusable shaft, bearing-seat, fastener-hole, and mounting-frame tools.
- 36 passing tests, including seeded size/origin/solid-count/volume defects,
  invalid specifications, failed construction diagnostics, and worker timeout handling.

## Executed evidence

- `uv sync`: dependencies installed and `uv.lock` generated.
- `uv run --locked pytest -q`: 36 passed after correcting export order.
- `build_design specs/smoke_test.yaml --output builds/smoke-v2`: PASS;
  measured 10 × 20 × 5 mm, 1,000 mm³, one valid solid, STEP round trips and STL bounds pass.
- `render_review builds/smoke-v2/build_manifest.json --output builds/review-v2`: PASS, four views.
- `validate_spec specs/finger_joint_v1.yaml`: expected BLOCKED, exit 2.
- `environment_report`: PASS inventory; desktop import checks BLOCKED.
- `inspect_geometry` on the exported assembly: PASS independently of the builder.
- Browser review of all four smoke-v2 projections: rendered successfully;
  screenshot at `output/playwright/smoke-review.png`. Review-v3 improves line contrast.
- Committed baseline `c7ddc80` rebuilt in `builds/clean-checkout` using a separate
  virtual environment, `uv sync --locked --offline`, and the existing download cache.
  All 36 tests pass there; source hashes, dependency versions, and geometry reports
  match the clean main-worktree build. Evidence: `builds/reports/reproducibility.json`.
  Main committed-source artifacts: `builds/baseline/`.

The initial export failed when exporting an assembly child. Its failure report and
candidate are retained under `builds/`; D001 explains the correction. No acceptance
threshold was changed. Generated evidence can be reproduced with README commands.

## Open gates

| Gate / phase | Status and next evidence |
|---|---|
| Phase 0 input freeze | BLOCKED: printer/nozzle/material, component drawings, envelope, mounting pattern, motion range, and A001 approval remain open. |
| Phase 1 Python build/export | PASS for the known-size smoke fixture on this Mac. |
| Phase 1 desktop commissioning | BLOCKED: FreeCAD and Bambu Studio not found in standard app directories; viewer extension not found in initial inventory. Install/inspect and record actual dimension/scale checks. |
| Phase 2 foundation | Initial tools work. Joint builder, section workflow, approval reconciliation, and full interface registry remain unfinished. Phase 1 exit is still open. |
| Phase 3 onward | Not commissioned; motion, assembly/keep-out checks, calibration, printing, physical assembly, and release remain future work. |

Next acceptance gate: commission the desktop viewer/FreeCAD/Bambu Studio path
with the same smoke fixture and collect actual printer/component inputs. Installation
outside this project needs Jamie’s approval under the kickoff instructions.
The concrete installation and verification scope is in
[desktop_commissioning.md](desktop_commissioning.md).

No print, release, physical measurement, powered test, or load rating has occurred.
