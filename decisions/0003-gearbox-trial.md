# D003 — End-to-end gearbox trial

Jamie approved the four-compound-gear 27:1 layout and then instructed: “This is an
end to end trial so make reasonable assumptions based on the servo model in use.”
This authorizes choosing development dimensions without repeated assumption approvals.
It does not convert assumptions into component facts, calibrations, or print/powered-test
approval. Original measurement records remain unchanged.

Implement 60T/20T module-1, 20° unshifted involute gears, with three external meshes,
each 3:1. The small gear is behind the large gear toward the back plate. Tooth
thickness is reduced by 0.12 mm per gear at the pitch circle for trial running clearance.
Use 5 mm plastic shafts integral with the 174 × 109 × 5 mm back plate, 5.4 mm bores,
and 0.3 mm clearance below fixed top retainers. No process compensation is applied.
Root transitions are radial, not production hob-generated fillets; no stress rating.

The servo drives the first compound gear through its existing metal 25T horn and
a removable adapter. The source STEP has four radius-1.25 mm horn holes on a 14 mm
circle, consistent with an M3 tapping pilot, but does not model threads. M3 threaded
horn holes remain a trial assumption. Preserve 5.9 mm published / 5.8 mm reported
spline diameters; do not manufacture an invented spline profile.

The adapter uses four underside countersunk M3 horn holes, four outer M3 attachments
at radius 20 mm and captive nut pockets. Trial fasteners: M3 × 6 countersunk horn
screws, M3 × 8 countersunk gear/adapter screws, M3 nuts, M3 × 8 retainer screws into
tapped 2.5 mm printed pilots, and four M3 × 85 threaded rods with nuts for the cradle.
Hardware envelope/assembly access must be checked; purchase/fit is not established.
The adapter is 4 mm thick so M3 × 8 outer screws end flush at Z=35, below the
tray at Z=35.2. The front-right cradle post was moved clear of G2 after a detected
3.57 mm³ collision; final full-revolution envelopes must also pass.

The source servo is aligned above G1 with the horn's outer face at Z=35. A removable
tray, locating rails, four posts, and lid retain its body. Small case-clearance gaps
are intentional trial fits; adjust with thin shims on assembly if needed, without
claiming measured backlash or load capability. Cable connectors need an accessible
exit, and the cradle should be removable without disturbing the other three gears.

Verification: valid solids, per-part STEP round trips, assembly placement and collisions,
mesh profiles/ratio/phase, sampled planar tooth motion plus a conservative interval
clearance bound, STL exports, rendered assembled/exploded views, and meaningful defect
tests. The supplied STEP has internal overlapping component representations; reference
parts must be checked separately from printable parts, not falsely counted as one solid.

Trial clearance and fit assumptions are design inputs, not changes to acceptance policy.
Use the existing geometric policy for kernel round-trip checks. Any additional numerical
error bounds must be declared as software checks rather than manufacturing tolerances.

The vendor STEP contains one invalid casing solid (`BRepCheck_SubshapeNotInShape`).
Shape fixing and reconstruction from its valid constituent shells did not resolve it;
those diagnostic STEP files remain under `builds/`. Other vendor solids also changed
volume during STEP re-export beyond the existing tolerance. Stop repair attempts and
use three analytic purchased-component references: a case bounding envelope, front
horn with the supplier mounting-hole pattern, and rear wheel envelope. The front horn
reference omits the spline and threads. The original eight-solid supplier file remains
unchanged and is copied separately into the candidate. The physical design uses the
supplied metal horn. Do not claim a fully repaired vendor model.
Extract each envelope's actual enclosed Solid:
build123d's Box wraps a Compound, and treating that wrapped Compound as a Solid causes
inconsistent nested assembly export/volume accounting.

STL manifold checks exposed near-zero coordinate residues from separately tessellated
circular faces. Normalize coordinates below 0.001 × the existing linear policy tolerance
to zero in derived meshes, record before/after hashes and the maximum movement, then
require exact edge manifoldness and consistent orientation. Observed corrections were
below 9e-14 mm; no acceptance threshold or manufacturing clearance was relaxed.
