# Agentic 3D Mechanical Design Lab

## Project implementation plan

**Project owner:** Jamie Haas  
**Target workstation:** Jamie’s MacBook, with a native Apple-silicon macOS installation preferred  
**Target printer:** Bambu Lab P2S Combo  
**AI operators:** Codex and/or Claude Code  
**Document version:** 1.0  
**Created:** September 6, 2026  
**Status:** Proposed architecture and execution plan; not an installation or validation report

> Build a local, code-first mechanical design environment in which an AI agent can create parametric components, assemble mechanisms, run engineering checks, prepare manufacturing artifacts, and learn from measured prototypes. Start with one useful finger joint. Earn the right to build the whole robot hand.

---

## 1. Executive decision

Use **build123d as the authoritative CAD authoring engine**, **OCP CAD Viewer as the interactive review surface**, **FreeCAD as the complementary engineering desktop**, and **Bambu Studio as the manufacturing endpoint**.

Codex or Claude Code will edit Python CAD source and structured specifications, invoke deterministic local tools, inspect their reports and images, and propose revisions. The agent will not be expected to operate CAD primarily through mouse clicks.

The valuable custom work is the layer around CAD: reusable mechanical interfaces, validation tools, calibrated manufacturing rules, and controlled release procedures. A language model that can create a solid is not yet a mechanical design system.

### Primary outcomes

1. Rebuild a design from its specification, source revision, and locked environment.
2. Produce inspectable parts and assemblies, including STEP and printable mesh exports.
3. Verify important dimensions, interfaces, and sampled motion configurations using geometry, not screenshots alone.
4. Prepare a traceable, human-approved print package for the actual P2S configuration.
5. Use physical measurements to improve subsequent fits and design decisions.

### Definition of success for the first release

The first project release contains a **physically assembled, bearing-supported finger-joint demonstrator** with a removable cover, defined mounting interface, controlled shaft/magnet/PCB geometry, and a documented manual motion test. It includes design source, a purchased-parts list, validation reports, reviewed print settings, calibration evidence, and recorded observations.

Unknown load requirements must remain explicit. Completing this demonstrator does **not** establish a torque rating, fatigue life, safety certification, or suitability for use on a person.

---

## 2. Scope and boundaries

### Minimum viable system

- Local Python CAD builds and a version-controlled repository.
- Structured specifications with explicit units and approved assumptions.
- Parametric parts, named assemblies, purchased-component envelopes, and interfaces.
- Geometry and dimensional checks, followed by simple motion-sweep checks.
- Standard review views, sections, and assembly illustrations.
- STEP and per-part mesh exports with a manufacturing manifest.
- P2S fit coupons, measured process rules, and a manually reviewed slicer workflow.
- One finger-joint reference design and an agent-driven change-and-rebuild demonstration.

### Subsequent expansion

- A qualified spur-gear geometry workflow, then a simple gearbox.
- Multiple linked finger modules and tendon or cable routing.
- Additional material/process calibrations and physical load testing.
- Automated slicing after qualification on the installed Mac and Bambu Studio version.
- Optional FreeCAD MCP integration, selected FEM analyses, and more sophisticated mechanism checks.

### Explicitly outside the initial scope

- Unattended printer operation or unrestricted remote printer control.
- Safety-certified robotic operation, wearable use, or human-contact validation.
- Automatically certified load ratings for printed gears or links.
- A full humanoid hand before a single joint has been validated.
- GUI-only CAD automation as the main modeling method.
- Simultaneous competing CAD sources in build123d, CadQuery, and FreeCAD.
- An OpenAI API integration: existing Codex/Claude Code tooling is sufficient for the initial workflow.

---

## 3. Architecture decisions and software selection

| Layer | Selection | Role and boundary |
|---|---|---|
| AI operator | Codex or Claude Code | Plan changes, edit permitted source, invoke tools, interpret evidence. |
| Geometry authoring | build123d | Own parametric CAD construction in Python. |
| Interactive review | OCP CAD Viewer | Inspect geometry and capture standardized views where supported. |
| Engineering desktop | FreeCAD | Inspect exchanged geometry, support drawings, and handle explicitly designated native CAD work. |
| Standard components | bd_warehouse, selectively adopted | Supply reusable component geometry after dimensional verification. |
| Gear geometry | Qualify py_gearworks or a FreeCAD Gears workflow | Generate candidate geometry; do not treat generation as strength verification. |
| Validation | Python, pytest, CAD-kernel operations; NumPy/SciPy as needed | Produce numerical, geometric, and regression evidence. |
| Print preparation | Bambu Studio | Apply the actual P2S machine, nozzle, material, and process profiles. |
| Environment and history | uv and Git | Lock dependencies, record changes, reproduce candidate builds. |
| Optional later tools | FEM tools, Blender, MCP bridge | Add only for a demonstrated requirement. |

**Cost boundary:** The proposed core CAD/modeling tools are free or open-source. AI subscriptions, purchased hardware, filament, and optional services are separate costs. Do not assume the complete printer connectivity ecosystem is open-source merely because the slicer is.

### Source-of-truth policy

- Python CAD source and approved specification files are authoritative.
- STEP files, meshes, pictures, and FreeCAD imports are derived artifacts.
- STEP exchange does not recreate the original Python construction history as a native FreeCAD feature tree.
- A geometric change made downstream must be ported into the authoritative source before the next release.
- An exception for a native FreeCAD-authored component requires a recorded decision identifying its master file and exchange boundary.

### Reproducibility policy

Reproducibility means equivalent geometry, dimensions, and test results within declared tolerances. It does not require byte-identical exported files when metadata or timestamps differ. Record environment versions and use geometry-aware comparisons.

### Deployment policy

Begin with local command-line tools, not a custom service or multi-agent platform. Add an MCP adapter only when a live-document or interoperability requirement justifies it. Keep geometry validation separate from the agent’s natural-language reasoning.

---

## 4. End-to-end workflow

```text
Design intent + component drawings + known constraints
                         |
                         v
       Structured specification and approved assumptions
                         |
                         v
                 Codex / Claude Code
        Plan -> change source -> invoke local tools
                         |
                         v
                 Python CAD build
             Parts + assembly + artifacts
                         |
             +-----------+-------------+
             |                         |
             v                         v
    Geometry / dimension checks   Review views / sections
             |
             v
       Interface and motion checks
             |
             v
   Manufacturing rules + engineering calculations
             |
       FAIL / BLOCKED -----------> Evidence-led revision
             |
       Required gates pass
             v
          Human design review
             |
             v
   Bambu Studio preparation and human print approval
             |
             v
       Physical assembly and characterization
             |
             v
  Measurement records -> calibrated rules -> next revision
```

The stages form an iteration loop. An early fit coupon can be printed before a full joint is finalized, but its release class and approval requirements must be clear.

---

## 5. Repository layout and design conventions

```text
jamie-mech-lab/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── pyproject.toml
├── uv.lock
├── specs/
│   ├── finger_joint_v1.yaml
│   └── approved_assumptions.yaml
├── cad/
│   ├── parts/
│   ├── assemblies/
│   ├── interfaces/
│   └── standard_components/
├── components/
│   ├── drawings/
│   └── component_registry.yaml
├── validation/
│   ├── geometry/
│   ├── dimensions/
│   ├── motion/
│   ├── engineering/
│   └── release_policy.yaml
├── manufacturing/
│   ├── printer_profiles/
│   ├── process_profiles/
│   ├── calibration/
│   └── orientation_rules/
├── tools/
├── tests/
├── measurements/
├── decisions/
├── builds/                     # Generated working output; normally ignored
└── releases/                   # Immutable approved prototype packages
```

### Conventions to establish before modeling

- CAD length unit: millimeters. Use unit-bearing field names for other quantities, such as `torque_nm` and `speed_rpm`.
- Define one global right-handed coordinate frame and named local frames for each mechanical interface.
- Give every part, interface, keep-out, and motion axis a stable identifier.
- Keep nominal component dimensions separate from manufacturing compensation.
- Store component drawing provenance, revision, and dimension confidence.
- Separate cosmetic geometry from critical mating geometry.
- Prefer references to named features or construction geometry over fragile face/edge indexing.
- Record numerical modeling tolerances separately from manufacturing clearances.
- Keep large generated assets out of ordinary Git history when practical; preserve release hashes and access instructions.

---

## 6. Specification and evidence models

Implement a validated schema before relying on YAML as an engineering contract. Reject missing required units, unknown fields, invalid ranges, and contradictory settings.

The following is a **proposed schema example**, not an already implemented API. Null values are deliberately unresolved. These nulls may be acceptable for a clearly limited demonstrator, but must block any release class that depends on them.

```yaml
schema_version: 1
project_id: finger_joint_v1
release_class: kinematic_demonstrator
length_unit: mm

requirements:
  external_envelope_mm: null
  joint_range_deg: null
  continuous_torque_nm: null
  peak_torque_nm: null
  output_speed_rpm: null
  backlash_limit_deg: null
  maximum_mass_g: null

mechanism:
  drive_type: manual
  bearing_support: paired
  removable_cover: true
  mechanical_stops: true

components:
  shaft: null
  bearings: []
  fasteners: []
  magnet: null
  sensor_pcb: null

manufacturing:
  printer_id: bambu_p2s
  machine_profile_id: null
  nozzle_diameter_mm: null
  material_profile_id: null
  fit_calibration_id: null

assumptions:
  - id: A001
    statement: Initial testing is manual and non-load-rated.
    approval_state: proposed
    approved_by: null
    approval_date: null

release_controls:
  human_design_review_required: true
  human_print_approval_required: true
  human_powered_test_approval_required: true
```

### Parameter classes

| Class | Meaning | Change authority |
|---|---|---|
| Requirement | Externally imposed constraint or approved acceptance threshold. | Jamie or a designated reviewer. |
| Design variable | Geometry or configuration the agent may optimize. | Agent within approved bounds. |
| Component fact | Dimension or rating from a specific purchased part. | Verified component registry update. |
| Process calibration | Measured compensation for a printer/material/process combination. | Evidence-backed update with review. |
| Assumption | Temporary design input without complete evidence. | Explicit approval; never silently promoted to fact. |

### Validation status vocabulary

Use `PASS`, `FAIL`, `BLOCKED`, and `NOT_APPLICABLE` at the individual-check level. A skipped or unavailable required check is `BLOCKED`, not `PASS`. Every `NOT_APPLICABLE` result needs a reason. Report limitations separately from the pass/fail outcome.

---

## 7. Local tool contracts

The names below describe **tools to build**, not commands already supplied by build123d. Begin as Python CLI entry points. They should be callable identically by a person or an AI agent.

| Proposed tool | Inputs | Required outputs |
|---|---|---|
| `validate_spec` | Specification and release policy | Schema errors, missing inputs, unresolved approval states. |
| `build_design` | Valid specification, source revision | Parts, assembly, build manifest, structured errors. |
| `inspect_geometry` | Built geometry and dimensional requirements | Solid checks, dimensions, volume, interface measurements. |
| `check_interfaces` | Assembly, interface registry, allowed-contact rules | Alignment, fits, keep-out and access findings. |
| `sweep_motion` | Assembly, joints, evaluated range, sampling policy | Evaluated poses, interference results, closest approaches, limitations. |
| `render_review` | Assembly and standard camera/section definitions | Labeled images and a view manifest. |
| `prepare_print` | Candidate release and qualified process profile | Oriented exports, manifest, and slicer handoff information. |
| `package_release` | Approved candidate and validation evidence | Immutable package, revision metadata, checksums, release status. |
| `record_measurement` | Physical sample identity and measurements | Traceable observations linked to the exact printed revision. |

All tools should return nonzero exit codes on relevant failures, machine-readable reports, and concise human summaries. Validate paths, use argument lists rather than shell-concatenated strings, enforce timeouts, and write outputs atomically.

Example **illustrative** finding:

```json
{
  "schema_version": 1,
  "check_id": "encoder_pcb_keepout",
  "status": "FAIL",
  "components": ["housing_rib_03", "encoder_pcb_keepout"],
  "measured_clearance_mm": -1.2,
  "required_clearance_mm": 0.5,
  "measurement_convention": "negative values indicate penetration",
  "pose_deg": 35.0,
  "evidence": ["views/encoder_section.png"],
  "message": "Housing rib intrudes into the reserved PCB volume."
}
```

The clearance values above are examples, not requirements for the actual joint. A tool may report a penetration depth only when its geometry algorithm has actually computed that quantity; overlap volume alone is not equivalent.

---

## 8. Verification and release gates

| Gate | Required evidence | Pass condition |
|---|---|---|
| G0: Specification | Valid schema, input provenance, approval record. | Requirements necessary for the requested release class are resolved. |
| G1: Geometry | Validity report, part count, dimensions, bounding envelopes. | Required solids and geometry checks pass without hidden exceptions. |
| G2: Assembly | Interface, keep-out, alignment, access, and assembly-sequence review. | No unexplained interference or inaccessible required assembly operation. |
| G3: Motion | Pose manifest, sweep results, sampling limits. | Evaluated configurations meet approved clearances; uncertainty is disclosed. |
| G4: Manufacturing | Actual profile, orientations, fit-calibration references, slicer review. | Parts are compatible with the approved process and reviewed for printing. |
| G5: Engineering | Relevant calculations and physical test evidence. | Evidence supports the requested functional or load-related claims. |
| G6: Release | Complete package and explicit human approvals. | Required gates for this release class pass; limitations are carried forward. |

### Release classes

**Fit coupon:** Used to measure process behavior. Requires safe, reviewed geometry and print preparation; does not claim mechanism functionality.

**Kinematic demonstrator:** Used to validate assembly and movement under controlled conditions. May have unresolved strength requirements if clearly labeled non-load-rated.

**Functional prototype:** Requires defined operating conditions, relevant calculations, and an approved physical test plan. Any rated performance must be supported by evidence.

**Qualified design:** Not an initial project deliverable. Requires a separately approved reliability, environmental, and safety qualification program.

### Important checking rules

- Query CAD geometry for critical dimensions; use screenshots as complementary review evidence.
- Distinguish intended bearing contact, gear contact, and approved fits from accidental collisions.
- Scope any permitted interference to a named interface and bounded condition. Never disable checks globally for a whole component to hide a failure.
- Report sampled motion honestly; adaptively refine close approaches and do not claim continuous collision freedom from sparse sampling.
- Protect acceptance thresholds from unilateral designer-agent edits. Require review of policy changes and retain the policy revision in every report.
- Include deliberately bad models in the test suite to prove checks can fail.

---

## 9. Phased implementation roadmap

Use acceptance-gated milestones rather than a fixed calendar. No phase is complete merely because the model rendered successfully.

### Phase 0 — Freeze the charter and initial interface decisions

**Dependencies:** None.

**Work:** Confirm Mac hardware/OS, available editor and AI tooling, printer/nozzle configuration, intended materials, and the first prototype’s purpose. Select the first shaft/bearing arrangement and establish whether actual magnet/PCB drawings are available. Record unresolved load and packaging inputs.

**Deliverables:** Project charter, decision log, initial specification, component-information checklist, release-class policy.

**Exit criteria:** The first deliverable is explicitly a fit/kinematic prototype or has sufficient inputs for a higher class. No fabricated motor, bearing, magnet-gap, or load specifications are treated as facts.

### Phase 1 — Commission the local CAD toolchain

**Dependencies:** Phase 0 platform decisions.

**Work:** Install and verify the selected Python environment, build123d, viewer, FreeCAD, and Bambu Studio. Create a simple known-dimension solid; export and reopen it. Confirm native Apple-silicon compatibility where applicable. Record actual application and package versions.

**Deliverables:** Repository, `uv.lock`, setup instructions, environment report, smoke-test geometry and screenshots.

**Exit criteria:** A fresh checkout can rebuild the smoke test. Its dimensions and units remain correct in the viewer, FreeCAD, and Bambu Studio. Failures have reproducible diagnostics.

### Phase 2 — Build the deterministic CAD foundation

**Dependencies:** Phase 1.

**Work:** Implement schema validation, part registration, named coordinate frames, build manifests, exports, and standard views. Create reusable mounting, bearing, shaft, and fastener interfaces. Add graceful handling of failed booleans/fillets and incomplete specifications.

**Deliverables:** `validate_spec`, `build_design`, initial `render_review`, reusable interface library, unit tests.

**Exit criteria:** Parameter changes rebuild the expected geometry; invalid inputs fail clearly; derived artifacts identify their specification and source revisions.

### Phase 3 — Implement geometry and assembly verification

**Dependencies:** Phase 2.

**Work:** Implement dimension, envelope, solid-count, alignment, and keep-out checks. Add a simple revolute-joint pose generator and sampled interference checks. Establish named contact exceptions. Validate checks against analytic test cases and deliberately defective assemblies.

**Deliverables:** `inspect_geometry`, `check_interfaces`, initial `sweep_motion`, protected release policy, regression fixtures.

**Exit criteria:** Seeded defects such as a shifted bearing seat, undersized hole, blocked screw path, and colliding cover are detected by the appropriate checks. Unsupported checks return `BLOCKED`.

### Phase 4 — Characterize the P2S printing process

**Dependencies:** Phase 2 export path; reviewed coupon designs.

**Work:** Print fit coupons using the actual selected material, nozzle, orientation, and process profile. Measure shaft holes, bearing seats, sliding gaps, fastener clearances, and insert pockets. Record results by sample and process combination.

**Deliverables:** Calibration CAD, reviewed slicer project, measurement records, provisional fit rules, process identifiers.

**Exit criteria:** Recommended compensations are traceable to measurements, with their conditions and uncertainty. Geometry unit and scale checks are complete. Coupon conclusions are not generalized to untested materials or orientations.

### Phase 5 — Build and validate the reference finger joint

**Dependencies:** Phases 3 and 4; sufficient component dimensions.

**Work:** Create the modular bearing-supported joint with removable cover, mounting pattern, mechanical stops, and a simple manual lever or tendon pulley. Include actual or explicitly provisional sensor/magnet envelopes. Run validation, print, assemble, inspect, and revise.

**Deliverables:** CAD source, assembly, exploded view, purchased-parts list, interface report, motion report, approved print package, physical test record.

**Exit criteria:** The printed revision assembles as planned, moves through the specified test range, and passes its declared fit/kinematic checks. Remaining limitations and changes for the next revision are documented.

### Phase 6 — Close the agent-driven design loop

**Dependencies:** Phase 5 baseline and deterministic tooling.

**Work:** Write `AGENTS.md` and `CLAUDE.md`; define planning, editing, checking, and release roles. Demonstrate an instructed change such as increased bearing spacing while preserving the mounting pattern and magnet/PCB keep-out. Add retry limits and evidence-led failure recovery.

**Deliverables:** Agent instructions, tool invocation examples, change summary format, independently reviewed automated change demonstration.

**Exit criteria:** The agent can complete a bounded design revision, regenerate evidence, and explain consequences without weakening acceptance thresholds. It does not print or run powered tests without approval.

### Phase 7 — Qualify gear geometry and build a simple gearbox

**Dependencies:** Phase 6; approved operating inputs for the intended test class.

**Work:** Evaluate one gear generator, verify a simple spur pair, establish center distance and angular phasing, and test export fidelity. Add bearing support, housing, service access, and a gearbox test plan. Measure backlash, running drag, and wear under defined conditions.

**Deliverables:** Gear-generator qualification record, reusable gear-pair model, gearbox assembly, calculations, print package, test results.

**Exit criteria:** The geometry and physical mechanism perform as required for the test class. Torque, speed, temperature, and life claims are limited to supported conditions.

### Phase 8 — Extend to fingers, hands, and advanced analysis

**Dependencies:** Successful reusable joint and gearbox modules.

**Work:** Build multi-joint fingers, integrate routing and packaging, add repeatable performance tests, and introduce advanced tooling only where it closes a demonstrated gap. Consider FEM, live FreeCAD integration, additional materials, and qualified slicer automation.

**Deliverables:** Expansion roadmap, reusable mechanism library, selected analysis integrations, revised system acceptance tests.

**Exit criteria:** Complexity increases without losing traceability, reproducibility, or clear physical-test boundaries.

---

## 10. Reference joint design brief

### Initial design content

- A housing with two defined bearing-support locations, subject to the selected bearing arrangement.
- A shaft or axle interface and replaceable finger-link attachment.
- A removable cover with accessible fasteners.
- A stable external mounting pattern and named joint axis.
- Mechanical stops with an explicitly specified motion range.
- A manual actuation interface or tendon pulley for low-risk kinematic testing.
- A shaft-mounted magnet envelope and sensor-PCB envelope with controlled relative placement.
- A deliberate wire exit and reserved routing volume.

Actual magnet alignment, gap, runout, and PCB-clearance requirements must come from the selected sensor/component documentation and approved design intent. Do not invent acceptable values.

### Initial physical checks

Record assembly order, purchased-part fit, shaft freedom, observed wobble, cover fit, fastener access, motion limits, and any rubbing. Capture annotated photographs and measurements tied to the printed revision.

The first demonstrator should preferably use purchased bearings, shafts, and fasteners with printed housings and links. Fully printed construction is not an objective in itself.

### Standard agent change test

> Increase bearing spacing by 4 mm, preserve the mounting pattern, maintain the approved sensor/magnet relationship, and report the resulting changes in envelope, mass estimate, and clearances.

This is a proposed benchmark, not an approved change to an existing design. The test passes only if the agent preserves controlled interfaces and reports any requirement it cannot satisfy.

---

## 11. Manufacturing calibration and physical feedback

### Process identity

Each calibration record must identify the printer, nozzle, build plate, material/product, relevant conditioning, orientation, layer height, slicer version, machine/material/process profiles, and physical sample revision. Record machine/environment conditions when they are important to interpretation.

Do not hard-code printer limits from memory. Read and verify the installed P2S configuration during commissioning.

### Initial coupon matrix

| Coupon | Experimental variable | Measurements |
|---|---|---|
| Sliding interfaces | Per-side clearance | Fit, binding, free play, and dimensional measurements. |
| Shaft holes | Nominal diameter and compensation | Diameter and fit with the actual shaft; orientation noted. |
| Bearing seats | Seat size and geometry | Assembly fit, retention, distortion, and serviceability. |
| Fastener holes | Clearance and orientation | Screw passage, seating, and access. |
| Insert pockets | Supplier-directed starting geometry | Installation observations and retention evidence appropriate to the intended use. |
| Gear pair | Approved mesh-clearance variation | Backlash, drag, tooth contact, and visible wear. |

An initial **experimental** sliding-fit set may use 0.15, 0.20, 0.25, 0.30, and 0.40 mm per-side clearances. These are test candidates, not a claimed P2S tolerance specification. For example, 0.20 mm radial clearance around a nominal 4.00 mm shaft corresponds to a nominal 4.40 mm hole before separate process compensation.

Use repeated samples for critical interfaces; three initial replicates can screen variability but do not establish statistical process capability. Select measuring instruments appropriate to the tolerance and record their resolution and limitations.

### Slicing policy

- Begin with a reviewed GUI workflow in Bambu Studio.
- Confirm model scale, orientation, supports, mating-surface quality, and estimated material use.
- Preserve the slicer project and the exact process configuration used for a print.
- STL does not carry a reliable unit contract by itself; record millimeters in the manifest and verify import scale.
- Let Bambu Studio create the sliced job. Do not have the language model author printer G-code directly.
- Qualify CLI slicing on the installed Mac/version before treating it as an automated dependency. Fall back to the GUI on failure.
- Check exact flexible-filament and feed-path compatibility before using TPU through the Combo’s material system.

### Feedback rule

A physical measurement may update a process compensation or reveal a design error. Keep these separate: do not distort a nominal purchased-part definition merely to compensate for one print process.

---

## 12. Agent operating rules and security

Store the canonical workflow in `AGENTS.md`; make `CLAUDE.md` direct Claude Code to the same policies and project commands. Avoid maintaining two contradictory instruction sets.

### Required behavior

1. Read the specification, component registry, release policy, and relevant decision records before editing.
2. Propose a bounded change and identify affected interfaces and tests.
3. Modify authoritative source, not only generated artifacts.
4. Run required checks and inspect relevant review views.
5. Report failures, blocked checks, assumptions, and material consequences.
6. Stop after a configured repair-attempt limit and preserve the best candidate plus diagnostics.
7. Request required release, print, or powered-test approval through the recorded workflow.

### Prohibited shortcuts

- Editing acceptance thresholds to make a failing design pass.
- Marking unexecuted checks as successful.
- Substituting screenshots for critical dimensional measurements.
- Claiming continuous motion verification from limited sampled poses.
- Overwriting approved release packages or removing inconvenient measurement records.
- Launching prints or powered mechanisms without authorization.
- Downloading and executing arbitrary third-party macros or packages without review.

### Workstation boundaries

Restrict tool writes to the project and explicit output directories. Keep printer credentials out of source and agent logs. Review external package installation and network access. If adding an MCP server, keep it local, pin its dependency versions, and treat arbitrary Python execution as a privileged capability.

Before sending proprietary CAD, drawings, or component information to any cloud AI service, verify the relevant organizational and service data-handling permissions. A local CAD build does not make the surrounding AI workflow automatically local or private.

---

## 13. Starter implementation backlog

Owners below describe responsibilities, not assigned individuals or background jobs. `Agent` means Codex/Claude Code operating under review; `Human` means Jamie or a designated reviewer.

| ID | Priority | Task | Owner | Completion evidence |
|---|---|---|---|---|
| M01 | P0 | Confirm platform, printer configuration, and first release class. | Human + Agent | Charter and environment inventory. |
| M02 | P0 | Create repository, locked Python environment, and smoke test. | Agent | Rebuild log and verified imports. |
| M03 | P0 | Implement specification schema and approval-state handling. | Agent | Positive and negative schema tests. |
| M04 | P0 | Implement deterministic part/assembly build and exports. | Agent | Named artifacts and build manifest. |
| M05 | P0 | Define coordinates, interface naming, and component registry. | Human + Agent | Reviewed conventions and drawing references. |
| M06 | P0 | Implement geometry, dimension, and envelope checks. | Agent | Seeded defects detected. |
| M07 | P0 | Implement interface/keep-out checks and bounded contact exceptions. | Agent | Passing and failing assembly fixtures. |
| M08 | P0 | Implement basic revolute motion sampling and reports. | Agent | Pose manifest and known-collision tests. |
| M09 | P0 | Create standard views and section review workflow. | Agent | Consistent labeled images. |
| M10 | P0 | Generate and review calibration coupons. | Human + Agent | Approved coupon print package. |
| M11 | P0 | Print, measure, and register fit calibrations. | Human | Linked measurement records and provisional rules. |
| M12 | P0 | Model and verify the reference finger joint. | Agent | Required digital checks pass. |
| M13 | P0 | Slice, approve, print, assemble, and inspect the joint. | Human | Physical prototype and observations. |
| M14 | P0 | Package the first reproducible release. | Agent + Human | Approved package and limitations. |
| M15 | P1 | Add agent rules, retry limits, and evidence-led revision loop. | Agent | Controlled change demonstration. |
| M16 | P1 | Qualify one spur-gear generator and gear-pair fixture. | Agent + Human | Geometry checks and physical mesh record. |
| M17 | P1 | Define gearbox operating requirements and test protocol. | Human + Agent | Approved inputs and test boundaries. |
| M18 | P1 | Build and characterize the first gearbox. | Agent + Human | Measured performance under stated conditions. |
| M19 | P2 | Commission automated slicing on the actual Mac/version. | Agent + Human | Repeatable GUI/CLI comparison and fallback. |
| M20 | P2 | Add selected FEM, MCP, or multi-joint capabilities. | Agent + Human | Demonstrated benefit and regression coverage. |

P0 establishes the first validated prototype workflow. P1 extends automation and mechanism capability. P2 is optional expansion, not a dependency for getting useful parts printed.

---

## 14. Risks, mitigations, and decision triggers

| Risk | Mitigation | Trigger for review |
|---|---|---|
| CAD topology becomes fragile after parameter changes. | Stable construction references, simpler feature ordering, parameter-sweep regression tests. | A common edit repeatedly breaks unrelated features. |
| Agent produces plausible but mechanically incorrect geometry. | Independent numerical checks, component drawings, physical prototypes. | Geometry passes but assembly or motion fails. |
| Printed fits vary by process or material. | Process-specific coupons, repeated measurements, explicit compensation. | New material/orientation or unexplained fit drift. |
| Gear geometry is mistaken for a rated transmission. | Separate geometry qualification, calculations, and physical tests. | Any proposed torque, efficiency, or life claim. |
| Slicer automation is unreliable on the installed Mac. | GUI baseline, version pinning, explicit CLI commissioning. | Crash, profile mismatch, or inconsistent output. |
| STEP handoff causes editing confusion. | Enforce authoritative-source policy. | A downstream manual edit is proposed as the new master. |
| Multi-agent complexity obscures ownership. | One operating agent plus separate review initially. | Duplicate changes, contradictory reports, or unnecessary orchestration. |
| Unsupported material assumptions invalidate analysis. | Measured process evidence and clearly bounded calculations. | Load-bearing or temperature-sensitive deployment. |
| Confidential designs leave approved boundaries. | Data classification and service permission review before transmission. | Proprietary drawings or employer-related work enters the project. |
| Physical testing creates pinch, fragment, or overheating hazards. | Guards as appropriate, limited-energy tests, supervision, explicit approval. | First powered test or higher-energy operating condition. |

---

## 15. Metrics and release contents

### Metrics to record from the beginning

- Clean-checkout build and validation success.
- Regressions across representative parameter combinations.
- Detection rate for intentionally seeded geometry and interface defects.
- Number of agent repair iterations and whether policy changes were attempted.
- Agreement between specified, modeled, and measured dimensions.
- First-assembly fit results and causes of reprints.
- Traceability completeness from a physical part to its source and process.
- Gearbox backlash, drag, temperature, or wear only after those tests are implemented and defined.

Do not invent precision targets before the interface requirements and measurement method are established. For the initial system, require all mandatory checks to execute, all specified seeded defects to be detected, and every released artifact to identify its source and process.

### Required prototype release package

```text
release_<project>_<revision>/
├── README.md                   # Purpose, status, limitations, approvals
├── specification.yaml
├── source_manifest.json        # Source revision and environment versions
├── component_bom.csv
├── geometry/
│   ├── assembly.step
│   └── parts/
├── print/
│   ├── oriented_meshes/
│   ├── manufacturing_manifest.json
│   └── reviewed_slicer_project.3mf
├── validation/
├── views/
├── assembly_instructions.md
├── physical_test_plan.md
├── measurement_links.json
└── checksums.txt
```

The exact filenames are proposed conventions. A slicer project is included after it has actually been created and reviewed. Do not fabricate empty placeholder evidence to satisfy the package layout.

---

## 16. Bootstrap checklist and starter commands

These are starting commands carried forward from the architecture discussion. They have **not** been executed on Jamie’s Mac. Verify current package compatibility during Phase 1 and commit the successful lockfile.

With `uv` installed:

```bash
uv init --python 3.12 jamie-mech-lab
cd jamie-mech-lab

uv add build123d ocp-vscode pydantic pyyaml
uv add --dev pytest

uv run python -c \
'from build123d import Box, export_step; export_step(Box(10, 20, 5), "smoke_test.step")'
```

Add numerical, mesh, standard-component, and gear packages only as their use cases are implemented. Do not install every optional dependency before proving the basic build/export/view/slice path.

- [ ] Inspect the installed macOS version and chip architecture.
- [ ] Verify Python and CAD package installation without silently mixing incompatible architectures.
- [ ] Open the 10 × 20 × 5 mm smoke-test solid in the viewer and FreeCAD.
- [ ] Verify the same dimensions after Bambu Studio import.
- [ ] Record installed app/package versions and commit `uv.lock`.
- [ ] Implement the project schema before modeling the reference mechanism.
- [ ] Establish release rules and a calibration print workflow.

---

## 17. Agent kickoff prompt

Paste the following into the coding agent from the project workspace:

```text
Implement the initial foundation of the Agentic 3D Mechanical Design Lab
using Agentic_3D_Mechanical_Design_Project_Plan.md as the project brief.

Start with Phases 0–2. Inspect the local environment before changing it.
Use build123d as the authoritative CAD engine and Python as the modeling
language. Use uv for dependency management and pytest for tests. Keep
FreeCAD and Bambu Studio as explicit inspection/manufacturing boundaries.

Create the repository structure, README, AGENTS.md, CLAUDE.md, a validated
specification schema, a smoke-test part, a deterministic build command,
STEP/mesh export, and a build manifest. Define all proposed tool commands
before documenting them as available. Add negative tests for invalid
specifications and geometry failures.

Unknown engineering inputs must remain explicit. Do not invent motor
loads, bearing dimensions, magnet gaps, printer calibrations, or safety
ratings. Propose assumptions separately and preserve their approval state.

Do not weaken acceptance thresholds, claim an unexecuted check passed,
start a print, control powered hardware, or send proprietary files to an
unapproved service. Ask before installing system-level tools or making
changes outside this project.

Finish by reporting what was implemented, commands actually executed,
results, unresolved blockers, and the next acceptance gate. Preserve
useful partial work when something fails rather than hiding the failure.
```

---

## 18. Reference documentation

These links are retained from the preceding design discussion. Confirm the relevant versions, licenses, and platform compatibility during commissioning; this plan does not represent a fresh compatibility audit.

- build123d: <https://github.com/gumyr/build123d>
- build123d assemblies: <https://build123d.readthedocs.io/en/stable/assemblies.html>
- OCP CAD Viewer: <https://github.com/bernhard-42/vscode-ocp-cad-viewer>
- FreeCAD: <https://github.com/FreeCAD/FreeCAD>
- bd_warehouse: <https://bd-warehouse.readthedocs.io/en/latest/>
- py_gearworks: <https://github.com/GarryBGoode/py_gearworks>
- FreeCAD Gears: <https://github.com/looooo/freecad.gears>
- Bambu Studio: <https://github.com/bambulab/BambuStudio>
- Bambu Studio command-line documentation: <https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage>
- Bambu Lab P2S specifications: <https://bambulab.com/en/p2s/specs>
- uv project workflow: <https://docs.astral.sh/uv/guides/projects/>
- Optional community FreeCAD MCP bridge: <https://github.com/neka-nat/freecad-mcp>

**Operating principle:** Source is authoritative, checks are explicit, prints require approval, and measurements beat confident guessing. The robot hand does not care how eloquent the design review sounded.
