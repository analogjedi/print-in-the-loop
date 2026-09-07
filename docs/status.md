# Foundation status

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
