# Jamie’s Mechanical Design Lab

Local parametric CAD using build123d, Python 3.12, uv, and explicit validation reports.
The [original plan](Agentic_3D_Mechanical_Design_Project_Plan.md) remains the brief;
[current status](docs/status.md) records what has actually been verified.

The working foundation builds a cube with a sphere on top and a 10 × 20 × 5 mm block, exports per-part STEP/STL
and an assembly STEP, reopens the STEP geometry, checks dimensions/origin/volume,
and generates four review projections. The finger-joint specification records
unknowns and deliberately blocks mechanism builds and releases.

## Cube with a sphere

The requested model is a **20 mm cube with a 16 mm diameter sphere**, centered
on its top face and embedded 1 mm for one connected solid. Overall size: **20 × 20 × 35 mm**.
Edit [specs/cube_sphere.yaml](specs/cube_sphere.yaml) to change the dimensions.

```bash
.tools/uv/bin/uv run --locked build_design specs/cube_sphere.yaml --output builds/my-cube-sphere
.tools/uv/bin/uv run --locked inspect_geometry builds/my-cube-sphere/assembly.step --spec specs/cube_sphere.yaml
.tools/uv/bin/uv run --locked render_review builds/my-cube-sphere/build_manifest.json --output builds/my-cube-review
```

Current artifacts: [STEP](builds/cube-sphere-v1/parts/cube_sphere.step),
[STL](builds/cube-sphere-v1/parts/cube_sphere.stl),
[FreeCAD document](builds/commissioning/CubeSphere.FCStd), and
[review views](builds/cube-sphere-review/index.html).
The FreeCAD document is derived from STEP; the Python source remains authoritative.

FreeCAD and Bambu Studio are installed in `/Applications`. VS Code is configured
to use this project’s `.venv`, with OCP CAD Viewer installed. For an immediately
usable standalone interactive viewer, run this in one terminal:

```bash
.tools/uv/bin/uv run --locked python -m ocp_vscode --host 127.0.0.1 --port 3939 --theme light
```

Open `http://127.0.0.1:3939`, then in another terminal:

```bash
.tools/uv/bin/uv run --locked python tools/view_model.py
```

If that port is already running, reuse it. In VS Code, use **OCP CAD Viewer: Open
viewer**, then pass its displayed port to `tools/view_model.py --port PORT`.
For desktop inspection:

```bash
open -a FreeCAD builds/commissioning/CubeSphere.FCStd
open -a BambuStudio builds/cube-sphere-v1/parts/cube_sphere.stl
```

The Bambu 3MF under `builds/commissioning/` is an unsliced default-profile import
experiment, not a reviewed print project. Select and review your actual P2S nozzle,
filament, plate, and process before slicing. No print has been started.

## Setup

On this Mac, uv is installed locally at `.tools/uv/bin/uv`. Python 3.12.6 was
already installed. No global Python or shell configuration was changed.

For a fresh checkout with Python 3.12 available:

```bash
python3.12 -m venv .tools/uv
.tools/uv/bin/python -m pip install --disable-pip-version-check --no-cache-dir uv==0.12.10
.tools/uv/bin/uv sync --locked
.tools/uv/bin/uv run --locked pytest -q
```

If `uv` is already installed, use it instead of `.tools/uv/bin/uv`. Dependencies
are locked in `uv.lock`; Python auto-download is disabled. Install a supported
Python 3.12 first if it is missing. The environment is commissioned on native arm64
macOS only; other platforms remain unverified. Network access is needed for an
initial dependency download. Package and font caches stay inside the workspace.

## Build and review

Run from the repository root. Use a new output directory on each build:

```bash
.tools/uv/bin/uv run --locked validate_spec specs/smoke_test.yaml
.tools/uv/bin/uv run --locked build_design specs/smoke_test.yaml --output builds/my-smoke
.tools/uv/bin/uv run --locked inspect_geometry builds/my-smoke/assembly.step --spec specs/smoke_test.yaml
.tools/uv/bin/uv run --locked render_review builds/my-smoke/build_manifest.json --output builds/my-review
.tools/uv/bin/uv run --locked environment_report
```

Open `builds/my-review/index.html` in a browser to see isometric, top, front,
and right projections. SVGs come from CAD-kernel projection. They complement the
numerical report; they are not interactive-viewer, FreeCAD, or slicer commissioning.

Build output includes `build_manifest.json`, `geometry_report.json`, copies of
the specification/policy, `assembly.step`, and `parts/smoke_block.step` / `.stl`.
The manifest records dependency versions, source hashes, Git revision and dirty
state, frames, units, artifact hashes, and limitations. Expect equivalent geometry,
not byte-identical STEP metadata. STL’s millimeter convention is recorded in the
manifest; actual slicer import scale still needs verification.

Outputs are confined to `builds/`. Existing candidate/report paths are refused.
Artifacts are staged then published together; failed candidates retain diagnostic
directories. JSON reports are written atomically. CAD worker timeout is 120 seconds
by default (`--timeout`); timed-out staging files can remain for diagnosis.

## Tool contracts and limits

Every public command supports `--report builds/reports/<new-name>.json`.
If omitted, a report with a unique ID is created under `builds/reports/`.
JSON goes to stdout, a summary to stderr. Exit codes: **0 PASS, 1 FAIL, 2 BLOCKED**.

| Command | Implemented scope |
|---|---|
| `validate_spec SPEC [--scope schema\|build\|release]` | Strict schema; explicit unknowns; development readiness. Default is build. Release always BLOCKED. |
| `build_design SPEC --output DIR` | Smoke block or cube/sphere, named assembly, exports, checks, manifest. Joint builder BLOCKED. |
| `inspect_geometry STEP --spec SPEC` | Validity, dimensions, origin, analytic volume; sphere radius and center for cube/sphere. |
| `render_review MANIFEST --output DIR` | Check assembly hash and generate four labeled SVG projections plus view manifest/HTML. |
| `environment_report` | Python/package versions and known desktop app locations; inventory only. |

`check_interfaces`, `sweep_motion`, `prepare_print`, `package_release`, and
`record_measurement` are **not implemented**. No printer or powered-hardware control
exists. Reusable shaft/bearing/fastener cut tools and mounting frames live in
`cad/interfaces/features.py`; they require explicit dimensions and compensation.

## Specifications and approval

```bash
.tools/uv/bin/uv run --locked validate_spec specs/finger_joint_v1.yaml --scope schema
.tools/uv/bin/uv run --locked validate_spec specs/finger_joint_v1.yaml
```

The first command passes structural validation. The second returns **BLOCKED / 2**
and lists missing engineering inputs. This difference is intentional. Unknown fields,
missing units, invalid ranges, duplicate YAML keys, contradictory torques, and
inconsistent approval metadata fail validation.

The component registry is empty. No shaft, bearing, fastener, magnet, sensor PCB,
printer profile, or fit calibration is verified. Approval metadata structure is
validated, but identity authentication and approval-ledger reconciliation are not
implemented. Proposed assumptions and policy must not be treated as approvals.
All release requests remain blocked, including smoke-test release requests.

## Layout

- `cad/`: authoritative parts, assemblies, frames, and mating-feature tools.
- `src/mech_lab/`: schema, CLI, validation, build, export, and review tooling.
- `specs/`, `components/`, `validation/`: inputs, provenance, and proposed policy.
- `manufacturing/`, `measurements/`, `releases/`: documented future process boundaries.
- `tests/`: parameter rebuilds, intentionally bad geometry, schema rejection, pipeline tests.
- `decisions/`, `docs/`: charter, decisions, commissioning status and instructions.
- `builds/`: ignored generated artifacts and diagnostics.

## Upstream references

The workflow follows [build123d installation](https://build123d.readthedocs.io/en/latest/installation.html),
[its export/projection interfaces](https://build123d.readthedocs.io/en/latest/import_export.html),
[uv isolated environments](https://docs.astral.sh/uv/pip/environments/), and the
[OCP CAD Viewer project](https://github.com/bernhard-42/vscode-ocp-cad-viewer).
The lockfile and executed reports identify the actual commissioned versions.
