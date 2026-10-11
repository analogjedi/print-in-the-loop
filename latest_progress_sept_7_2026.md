# Latest progress — September 7, 2026

Handoff for Jamie Haas. Repository: `/Users/jhaas/Development/3d-design-and-print`.
This records completed work and the next project intent; it is not a print release.

## Latest continuation — gearbox CAD completed September 7

This section supersedes the original “next project” and continuation prompt below,
which are retained as the earlier handoff history. Jamie selected **Waveshare ST3215**,
approved **27:1**, and authorized reasonable development assumptions (G001/G002).
His corrected case footprint is **45.2 × 24.6 mm** and measured spline OD **5.8 mm**;
published nominal spline data is **25T / 5.9 mm**, with an M3 × 6 retaining screw.

The completed candidate is [builds/gearbox-v4](builds/gearbox-v4/): four 60T/20T
compound gears, integral plastic shafts, a back plate, retainers, supplied-metal-horn
adapter and removable servo cradle. **15 printable parts; 174 × 109 × 75.9 mm** overall,
excluding protruding hardware and cables. The three meshes give a −1/27 output speed.

- [Interactive assembly, animation, assembly guide and BOM](builds/gearbox-review-v5/review.html).
- [Assembly STEP](builds/gearbox-v4/assembly.step) and [individual STLs](builds/gearbox-v4/print/).
- [BOM and assembly instructions](docs/gearbox_build_and_assembly.md).
- [Current verification status](docs/status.md) and [design decisions](decisions/0003-gearbox-trial.md).

**PASS:** 49 tests, candidate geometry/mesh/motion checks, independent assembly STEP
inspection, Bambu native import of the input gear and back plate, and interactive
assembled/exploded review with working animation. All 55 artifact hashes match. The vendor STEP
has defects; three simplified, dimensioned servo/horn references are used in the CAD,
with the original supplier file preserved separately. Physical fit, load capacity,
printing and powered testing remain **BLOCKED** pending actual hardware/process
verification and approval. There is no manufactured spline: use the supplied metal horn.

To resume, read this section, `docs/status.md`, `docs/gearbox_build_and_assembly.md`,
and `AGENTS.md`. Preserve the completed candidate and measurements. Continue from
physical fit/process review if requested; do not restart the historical layout proposal.
The project files contain the new implementation; generated builds are local, ignored
artifacts and are not automatically included in a fresh clone.

## Restart and resume

Jamie reports enabling Terminal Accessibility and receiving a notice that a restart
may be needed. The subsequent check in this running session still returned `false`:

```bash
osascript -e 'tell application "System Events" to get UI elements enabled'
```

Screen Recording is already granted and actual desktop screenshots work. Accessibility
is a separate permission needed for mouse/keyboard control. Finish this session,
save any other Terminal work, fully quit Terminal, and reopen it. Recheck permission
from the resumed session before attempting GUI interaction. A Mac reboot has not
been established as necessary. If access remains unavailable after relaunch, inspect
which application macOS identifies as requesting access before changing more settings.

Return to this repository and resume the conversation, or start a new conversation
with the continuation prompt below. For Codex CLI, `codex resume` opens the saved-chat
picker ([official documentation](https://learn.chatgpt.com/docs/codex/cli)).

## Completed environment and test model

| Item | Status | Evidence / scope |
|---|---|---|
| Local Python CAD foundation | PASS | Locked Python 3.12 environment; build123d 0.11.1, CAD kernel 7.9.3.1.1, ocp-vscode 3.4.0; project-local uv. |
| Automated checks | PASS | Recorded 41 passing tests, including a fresh checkout run; `builds/commissioning/cube-reproducibility.json`. Tests were not rerun for this documentation-only handoff. |
| Cube and sphere CAD | PASS | One valid solid, exact STEP geometry checks and STL export. |
| FreeCAD installation/import | PASS | FreeCAD 1.1.3; smoke and cube/sphere import checks in `builds/commissioning/freecad-verification.json`; native model and rendered review inspected. |
| Bambu installation/mesh exchange | PASS | Bambu Studio 2.8.2.61; cube/sphere mesh is one manifold part, 6,994 facets; native PNG preview inspected. |
| Standalone OCP viewer | PASS | Model displayed and visually inspected; `output/playwright/cube-sphere-ocp.png`. |
| Bambu GUI onboarding | BLOCKED | Last observed at the first-run welcome wizard; GUI control unavailable in the current process. |
| VS Code in-editor viewer | BLOCKED | OCP CAD Viewer 4.0.1 installed, project interpreter configured; live in-editor display still needs verification. |
| Physical printer configuration | BLOCKED | P2S profiles are installed; actual nozzle, filament, plate, process, and fit calibration are unverified. |

The test model has a 20 mm cube and a sphere of radius 8 mm centered above it,
embedded 1 mm into the cube. Overall dimensions are **20 × 20 × 35 mm**.
Exact solid volume is 10,120.575041 mm³. These are editable demonstration dimensions.

Useful files:

- Source: [cad/parts/cube_sphere.py](cad/parts/cube_sphere.py).
- Specification: [specs/cube_sphere.yaml](specs/cube_sphere.yaml).
- FreeCAD document: [CubeSphere.FCStd](builds/commissioning/CubeSphere.FCStd).
- Exchange files: [STEP](builds/cube-sphere-v1/parts/cube_sphere.step) and [STL](builds/cube-sphere-v1/parts/cube_sphere.stl).
- Review views: [index.html](builds/cube-sphere-review/index.html).
- Bambu import measurements: [bambu-model-info.txt](builds/commissioning/bambu-model-info.txt).
- Unsliced Bambu project: [cube_sphere.3mf](builds/commissioning/cube_sphere.3mf), using generic defaults; not a reviewed print configuration.

Latest commit before this handoff: `28f8ec0` (reproducibility record).
CAD implementation commit: `d6705f8`. The worktree was clean before this document update.
Generated files under `builds/` and `output/playwright/` are local, ignored artifacts;
they are not carried into a fresh Git clone automatically.

## Next project — compact compound gear reducer

Jamie's requested concept: **four gears in series, with a smaller gear behind the
larger gear on the same rotating gear assembly, each assembly spinning on a simple
plastic shaft supported by a back plate, creating a dense gearbox reducer.**

Preserve these requirements:

- Four serial gear assemblies as the initial interpretation of “4 in series.”
- A coaxial large gear and smaller rear pinion rotating together on each compound assembly.
- Simple plastic shafts and a common back plate.
- Compact packaging and speed reduction as the design intent.
- The first gear must connect to an off-the-shelf standard servo motor (Jamie's
  added requirement). Include the servo-to-input-gear interface in the design scope.

The assembly count is not yet a frozen transmission topology: confirm whether Jamie
means four compound assemblies or four reduction meshes, and how the input and output
connect. Do not silently equate those counts. “Behind” needs an explicit orientation
relative to the back plate in the first layout sketch. The input gear's support also
needs resolution: determine whether it mounts directly on the servo output or rotates
on a separately supported plastic shaft with a coupling to the servo.

Servo interface details remain open: exact manufacturer/model, output spline or
supplied horn dimensions, retention screw, mounting pattern, and positional versus
continuous-rotation operation. “Standard servo” alone is not a dimensioned interface.
Use the selected servo's authoritative drawing or Jamie's measurements before freezing
the connection. Direct spline engagement versus a gear attached to the supplied horn
is a proposed design choice, not an approved assumption. Do not choose or purchase a
servo on Jamie's behalf from this handoff alone.

Before detailed CAD, propose a reviewable layout showing which small pinion drives
which large gear and the axial positions that place each meshing pair in the same
plane. Check that the stacked gears clear neighboring gear bodies and the plate.

Still open for Jamie's review: overall footprint and depth, desired reduction ratio,
tooth counts and tooth geometry, gear thicknesses, shaft diameters and attachment,
gear retention, running clearances, material, and intended input speed/load or manual
demonstration use. No numerical design assumptions or manufacturing fits are approved
by this handoff. The plastic-shaft concept does not establish a load rating.

Proposed next work sequence:

1. Recheck Accessibility after restart; finish Bambu onboarding and verify the VS Code viewer.
2. Read `AGENTS.md`, `specs/`, `components/component_registry.yaml`,
   `validation/release_policy.yaml`, and relevant `decisions/` before CAD edits.
3. Draft the gearbox topology/layout and proposed parameters for Jamie's review.
4. After resolving the necessary design inputs, implement parametric gears, shafts,
   and back plate; generate an assembly plus individual STEP/STL parts and review views.
5. Verify geometry, gear mesh alignment, shaft/bore interfaces, axial retention,
   clearances, reduction ratio, and motion/interference through a rotation cycle.
   Record missing checks as BLOCKED. Physical fit requires measured calibration.

The gearbox is the next requested design project. The earlier finger-joint roadmap
remains documented, but should not displace this new priority. No gearbox CAD has
been created yet. No release, print, or powered test has been authorized.

## Continuation prompt

> Read `latest_progress_sept_7_2026.md` and `AGENTS.md` in this repository. Terminal
> Accessibility was enabled, but the previous running session still reported false;
> recheck it after restart. Finish the remaining desktop commissioning checks, then
> continue the proposed compact four-gear compound reducer on plastic shafts and a
> back plate, with its first gear connecting to an off-the-shelf standard servo motor.
> Identify the servo and its spline/horn interface, confirm the transmission topology,
> and propose dimensions for my review
> before treating them as approved. Preserve the completed cube/sphere model and evidence.

Further context: [docs/status.md](docs/status.md),
[docs/desktop_commissioning.md](docs/desktop_commissioning.md), and
[D002](decisions/0002-desktop-and-test-model.md).
