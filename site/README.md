# Published review pages

Served by GitHub Pages from this folder (`.github/workflows/pages.yml`) at
https://analogjedi.github.io/print-in-the-loop/.

| Page | Copied from | SHA-256 of the source `review.html` |
|---|---|---|
| `winch/index.html` | `builds/bldc-winch-v2/review.html` (`specs/bldc_4015_winch_v1.yaml`, 365 checks PASS) | `4ef8c3440a75570e41abd6725ef136b0b38d7aea5ea3601cbd3cdf9585819131` |

The pages are generated files, committed because CI doesn't run the CAD build. To refresh
one, rebuild into a new output directory and copy its `review.html` here:

```bash
uv run --locked build_design specs/bldc_4015_winch_v1.yaml --output builds/<new-dir>
cp builds/<new-dir>/review.html site/winch/index.html
```

Purchased parts in the pages are dimensioned reference envelopes, not supplier CAD.
