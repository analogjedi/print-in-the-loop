# Validation scope

Implemented: strict smoke/joint specification schema; smoke single-solid validity,
dimensions, global origin, and volume checks; STEP part and assembly round trips;
binary STL bounds; source/spec/policy/artifact hashes; standard review projections.

Not implemented: general interface evaluation, keep-outs, assembly sequence/access,
motion sweeps, section reviews, engineering calculations, process qualification,
release evaluator, and physical tests. These remain BLOCKED where required.

The proposed policy defines initial release classes and software tolerances.
Passing a smoke check never grants release approval. Do not weaken checks to pass.
