# Desktop commissioning record

The installation request was subsequently authorized by Jamie’s instruction to
complete the CAD environment. FreeCAD 1.1.3, Bambu Studio 2.8.2.61, and the
OCP viewer extension 4.0.1 are now installed. STEP imports in FreeCAD, standalone
OCP visualization, and Bambu mesh import/render/export are verified. See
[current status](status.md) for evidence and the remaining GUI setup interaction.

The original proposed action is retained below for provenance.

The project brief’s kickoff says: “Ask before installing system-level tools or
making changes outside this project.” The Python foundation is already local to
the repository. Completing desktop commissioning adds the following applications:

| Tool | Proposed installation | Primary source checked September 7, 2026 |
|---|---|---|
| FreeCAD 1.1.3 | Official native Apple-silicon macOS app under `/Applications` | [Official release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3) |
| Bambu Studio 2.8.2.61 | Official macOS app under `/Applications`, choosing native arm64 where supplied | [Official release](https://github.com/bambulab/BambuStudio/releases/tag/v02.08.02.61) |
| OCP CAD Viewer | VS Code extension `bernhard-42.ocp-cad-viewer` in Jamie’s VS Code profile; record exact version and confirm compatibility with locked ocp-vscode 3.4.0 | [Marketplace](https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer) |

At proposal time no desktop installers had been executed. Confirm the exact macOS release assets
and their integrity before installation. If the viewer requires a different Python
client, treat that as a dependency update with a lockfile change and regression run.

After installation:

1. Open the 10 × 20 × 5 mm smoke solid in the viewer and FreeCAD; verify geometry
   dimensions and record application versions and screenshots.
2. Import `builds/baseline/parts/smoke_block.stl` into Bambu Studio. Verify 100% scale
   and 10 × 20 × 5 mm dimensions; record the actual P2S machine/nozzle/material setup.
3. Save commissioning evidence and update the environment/status records. Printer
   profile selection still depends on Jamie’s physical configuration.

This action commissions software only. Print review and approval occur after there
is an actual slicer project and a defined physical sample to review.
