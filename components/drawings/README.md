# Supplier drawings

Third-party supplier drawings, CAD and listing images are **not redistributed** in this
repository. Each folder keeps a `*checksums.json` file recording what was used and its
SHA-256, so a downloaded copy can be verified byte for byte.

| Folder | Source | Needed for |
|---|---|---|
| `waveshare_st3215/` | [ST3215 STEP archive](https://files.waveshare.com/upload/5/59/ST3215-3D.zip) → extract `ST3215.step`; [2D archive](https://files.waveshare.com/upload/0/08/ST3215-2D.zip); [wiki](https://www.waveshare.com/wiki/ST3215_Servo) | Gearbox build (`specs/gearbox_v1.yaml` checks the STEP's SHA-256) and one gearbox test, which skips without it |
| `waveshare_st3215/` (Feetech) | [ST-3215-C018 datasheet](https://www.feetechrc.com/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf) | Reference only |
| `bldc_4015/` | Seller listing for the "4015 brushless DC motor, 24N22P, hollow shaft, MT6701 encoder" (URL not recorded) | Reference only; dimensions used are written into `specs/bldc_4015_stand_v1.yaml` and `docs/bldc_4015_stand_proposal.md` |
| `as5600_encoder_board/` | Seller listing for the 33 × 33 mm AS5600 magnetic encoder board (URL not recorded) | Reference only |

To build the gearbox, place `ST3215.step` at `components/drawings/waveshare_st3215/ST3215.step`.
Its SHA-256 must match `58e38e4dc49f97df738c5f229f9aa8a7dce64a0a1d01335486a52d53e6017e8a`.

For each new component, record the supplier part number, drawing URL and revision, nominal
dimensions with units, tolerances, and provenance in the component registry before modeling.
