# Agentic 3D Mechanical Design Lab

Work with Jamie Haas (GitHub: analogjedi), project owner. Use local SSH for
authorized GitHub operations. This directory is the repository root.

## Working contract

Read `specs/`, `components/component_registry.yaml`,
`validation/release_policy.yaml`, and relevant `decisions/` before CAD edits.
The original `Agentic_3D_Mechanical_Design_Project_Plan.md` is the project brief.
`docs/status.md` records commissioning progress; the plan is not evidence of completion.

State the bounded change, affected interfaces, and verification before editing.
Python in `cad/` and validated specifications are authoritative. Exported files
are derived. Keep nominal purchased dimensions distinct from process compensation.
Units are millimeters; global coordinates are right-handed with +Z up.

Keep assumptions proposed until Jamie explicitly approves them. Never invent
component facts, printer profiles, magnet gaps, loads, or calibration measurements.
Do not change acceptance thresholds to make a design pass. Policy changes need
Jamie’s review; software tolerances do not establish manufacturing tolerances.

Use one operating agent. After three unsuccessful repairs of the same failure,
preserve diagnostics and report the blocker. Do not repeat a failed operation
without new evidence. Required checks use PASS, FAIL, BLOCKED, NOT_APPLICABLE;
the last requires a reason. Missing checks are BLOCKED. Explain material limitations.

Run relevant tests and inspect generated review views. A development build never
authorizes a release, print, or powered test. Those require Jamie’s explicit approval.
Never overwrite releases or measurement records. No printer control is implemented.
Ask before system-wide installation or writing outside the project. Project-local
dependencies listed in pyproject.toml are part of the authorized foundation work.
Keep credentials out of files/logs and verify authorization before sending proprietary
drawings or CAD to cloud services. No API integration is needed for this project.

## Commands implemented here

Use `.tools/uv/bin/uv` on this workstation (or `uv` when already installed).
Run from the repository root:

```bash
.tools/uv/bin/uv sync --locked
.tools/uv/bin/uv run --locked pytest -q
.tools/uv/bin/uv run --locked validate_spec specs/smoke_test.yaml
.tools/uv/bin/uv run --locked validate_spec specs/finger_joint_v1.yaml --scope schema
.tools/uv/bin/uv run --locked build_design specs/smoke_test.yaml --output builds/new-candidate
.tools/uv/bin/uv run --locked inspect_geometry builds/new-candidate/assembly.step --spec specs/smoke_test.yaml
.tools/uv/bin/uv run --locked render_review builds/new-candidate/build_manifest.json --output builds/new-review
.tools/uv/bin/uv run --locked environment_report
```

Choose new output/report paths for each run. CLI tools emit JSON and a concise
summary, with exit 0 for PASS, 1 for FAIL, 2 for BLOCKED. CAD workers default to
120-second timeouts. Read README for scope limits; no other proposed tools exist yet.
