# Waveshare ST3215 — dimensions for Jamie's confirmation

Recorded September 7, 2026. Jamie identified the servo as **Waveshare ST3215**.
The model selection is user-provided; the dimensions below are manufacturer-published
nominal values, not measurements of Jamie's unit. Their use in the interface remains
pending Jamie's confirmation.

## Jamie's footprint measurement

Jamie's corrected measurement is **45.2 × 24.6 mm** on his ST3215. Compared with the
published footprint this is −0.02 mm in length and **−0.12 mm in width**. His earlier
26.6 mm width was a reporting error, explicitly corrected by Jamie. Do not rescale
the output-axis or horn geometry from this footprint measurement. Mount clearance
remains a separate design parameter; retain the manufacturer's nominal envelope.

The current observation and missing measurement metadata are preserved in the
[corrected measurement record](../measurements/2026-09-07_st3215_jamie_footprint_02.yaml).
The [original record](../measurements/2026-09-07_st3215_jamie_footprint_01.yaml) is
retained unchanged for history and is superseded by that correction.
This confirms a reported footprint, not the remaining horn/spline or height dimensions.

Jamie also reports **5.8 mm OD across the output shaft's outer ridges**, describing
the shaft as brass. This is the reported spline-tip diameter, not a smooth-bore fit
dimension. See the separate [spline OD record](../measurements/2026-09-07_st3215_jamie_spline_od_01.yaml).
The nominal tooth count and retaining-screw evidence found subsequently are recorded
below. Root diameter/profile and actual engagement geometry remain unresolved.
Neither measurement has been used as printer compensation.

## Spline reference supplied by Jamie, cross-checked with Feetech

Jamie supplied listings describing a 25T, approximately 5.9 mm output spline, a
dual-axis structure, and M3 fasteners. The
[Feetech ST-3215-C018 manufacturer datasheet](https://www.feetechrc.com/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf),
edition A/0 dated 2023-7-20, was downloaded and pages 4 and 6 visually inspected.

- Page 4, item 6-9: **25T / OD5.9 mm**.
- Page 4, item 6-13: output/rocker screw **M3 × 6**.
- The manufacturer describes the product as a dual-axis servo. This does not mean
  both sides are independently driven outputs.
- Page 6 includes other fastener callouts, including PA2.0 and PA3.0 × 5 self-tapping
  screws. Therefore M3 must not be assigned to every housing or horn attachment hole.

Use **5.9 mm as the manufacturer reference nominal spline OD** and retain **5.8 mm
as Jamie's measured OD**; the 0.1 mm difference is not an established tolerance or
print-fit allowance. The Feetech datasheet describes ST-3215-C018; Jamie's selected
product is Waveshare ST3215. It corroborates his supplied spline reference but is not
proof that every housing/accessory dimension is identical between supplied variants.
Keep the Waveshare outline and Jamie's measurements as separate sources.

The nominal 25T/5.9 designation does not fully define a manufacturable mating spline:
root diameter, tooth flank geometry and fit are absent. Existing matching horn/insert
geometry can provide that interface, subject to selecting and inspecting it. The
M3 × 6 stock screw length is not automatically suitable after adding a printed gear's
thickness; confirm actual thread engagement in the final axial stack.

Local primary source: `components/drawings/waveshare_st3215/FEETECH-ST-3215-C018-20230720.pdf`.
The PDF and two inspected page images are preserved with a separate checksum record.

## Sources inspected

- [Waveshare ST3215 wiki](https://www.waveshare.com/wiki/ST3215_Servo).
- [Product outline image](https://www.waveshare.com/img/devkit/accessories/ST3215-Servo/ST3215-Servo-details-size.jpg?v=26061202), visually inspected.
- [Official 2D archive](https://files.waveshare.com/upload/0/08/ST3215-2D.zip), containing PDF and DXF.
- [Official STEP archive](https://files.waveshare.com/upload/5/59/ST3215-3D.zip), downloaded for subsequent CAD integration; geometry not yet inspected.

Local copies are under `components/drawings/waveshare_st3215/`. The PDF was rendered
and visually inspected. Its title block says **SCS215**, dated 2022/6/8, even though
Waveshare links it as the ST3215 drawing. The current ST3215 product photograph has
the same outline dimensions, providing a separate visual cross-check. Do not conceal
the PDF title discrepancy or treat the STEP as physically calibrated evidence.

## Published dimensions (mm)

| Feature | Nominal dimension | Interpretation |
|---|---:|---|
| Case footprint, length × width | 45.22 × 24.72 | Viewed along the output axis. |
| Catalog dimension triplet | 45.22 × 35 × 24.72 | Wiki specification; not the complete horn-to-horn span. |
| Overall horn-to-horn span shown | 37.25 | Side-view dimension across the two fitted round horns; screw heads/cables require separate keep-outs. |
| Other side-view spans shown | 29, 32, 35 | Feature-to-feature dimensions; retain drawing datums rather than treating all as overall height. |
| Round horn diameter | 19.2 | Shown on both faces. |
| Opposite horn attachment-hole center spacing | 14 | Four equally positioned holes shown; nominal bolt-circle diameter inferred as 14. |
| Output-axis offset from nearest short end | 10.11 | Along the 45.22 mm case length. |
| Output-axis offset across width | 12.36, derived | Half of 24.72, based on the symmetric drawing; not a separately called-out dimension. |
| Case screw-center rectangle, connector face | 24.45 × 20.5 | Drawing shows housing fasteners; usable mounting/thread details are not specified. |
| Longitudinal case screw-center spacing, opposite face | 20.7 | Different from connector face; do not substitute one pattern for the other. |

Do not use nominal dimensions as print compensation or fit tolerances.

## Connection details still unresolved

The Waveshare outline drawing does **not** dimension the output spline tooth count/profile,
horn attachment-hole diameters/threads, center retaining-screw specification, or usable
thread engagement. The Feetech reference above subsequently provides nominal tooth
count/OD and the output retaining screw; exact spline profile, horn-hole threads and
usable engagement still require verified geometry or measurements.
Attaching the input gear to the existing metal horn is an available proposed approach;
it would avoid needing to manufacture the spline, but still needs the hole/thread
details and confirmation of the horn fitted to Jamie's servo.

Waveshare documents both angle-control and continuous-rotation modes. The requested
mechanical input should support the selected ST3215; its operating mode, applied loads,
and any powered test remain separate decisions.

## Approval state

Jamie approved the **27:1 gearbox layout for a test run** in this session, explicitly:
“Also, the 27:1 layout looks good. I approve since this is a test run.”
That approval does not confirm these servo dimensions, which Jamie asked to review next,
or authorize printing/powered operation. See `specs/approved_assumptions.yaml`.
