# D002 — Desktop commissioning and cube/sphere test

September 7, 2026. Jamie requested completing the CAD environment configuration
and creating a cube with a sphere on top. This authorizes the previously proposed
desktop installation. The larger finger-joint/physical calibration roadmap remains
a subsequent project; it is not required to author and inspect this software test.

The test uses a 20 mm cube and radius-8 mm sphere centered above its top face.
The sphere extends 1 mm into the cube, creating one connected solid, 35 mm tall.
These are changeable test-model design variables, not purchased-component facts,
load requirements, or printer calibration values. No print is authorized.

Installed official FreeCAD 1.1.3 arm64 and Bambu Studio 2.8.2.61 universal macOS apps
under /Applications. Installer SHA-256 hashes matched GitHub asset digests.
Installed bernhard-42.ocp-cad-viewer 4.0.1 into VS Code; retained the locked
ocp-vscode 3.4.0 Python client, which successfully displays the model in standalone mode.

FreeCAD exchange verification must inspect objects that contain solids. Its assembly
origin includes infinite construction planes that have misleading nonzero Volume
values; filtering by volume alone selects those planes. The corrected macro selects
solid-bearing objects and checks validity, dimensions, and analytical volume.

Bambu Studio CLI requires separate invocations for PNG and 3MF export. Absolute
paths are necessary for this installation because its working directory changes.
CLI --info confirms 20 × 20 × 35 mm, one manifold mesh part. Its default-profile 3MF
is an unsliced import test only; actual P2S nozzle/material/process remain unverified.
The STL is the preferred initial GUI import, avoiding unrelated preset import prompts.
