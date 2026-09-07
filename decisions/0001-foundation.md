# D001 — Local foundation and explicit unknowns

Recorded: 2026-09-06 (America/New_York).

Jamie asked to continue the plan in this directory. Apply its kickoff scope,
Phases 0–2, directly here rather than creating a nested repository. Preserve the
original plan unchanged. Initialize local Git; no remote repository is requested.

Observed platform: arm64, macOS 26.0 build 25A354. Existing native Homebrew
Python 3.12.6 is used. uv 0.12.10 is installed in `.tools/uv`, dependencies in
`.venv`, caches inside the workspace. No global Python or shell configuration changes.

Use build123d as master CAD, OCP viewer for eventual interactive inspection,
FreeCAD for exchange inspection, and Bambu Studio for reviewed slicing. Only the
Python toolchain is commissioned in this increment. App installation/commissioning
remains a separate platform action. Record actual installed versions in the environment report.

The first mechanism remains a proposed manual, non-load-rated kinematic demonstrator.
Its assumption A001 is not approved. Target printer is P2S per the brief; actual
nozzle, filament, profiles, and component drawings are unresolved.

Software smoke dimensions (10 × 20 × 5 mm) are the plan’s known-size fixture.
Synthetic interface tests are software tests and are not purchased-part recommendations.
The initial policy is proposed. Release evaluation deliberately remains BLOCKED.

During commissioning, build123d 0.11.1 failed to export an individual part after
it was attached to a Compound assembly. The builder exports individual parts first,
then creates and exports the assembly. The pipeline test covers both STEP round trips.
