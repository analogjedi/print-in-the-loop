"""Generate the explicitly proposed gearbox envelope review; not a CAD build."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(root / "builds"):
        parser.error("output must be under the project builds directory")
    output.mkdir(parents=True, exist_ok=False)

    centers = [(37., 37.), (77., 37.), (97., 37.+20*math.sqrt(3)),
               (137., 37.+20*math.sqrt(3))]
    large_z = [(27.-5*i, 31.-5*i) for i in range(4)]
    small_z = [(22.-5*i, 26.-5*i) for i in range(4)]
    checks = []

    def check(name, passed, **details):
        checks.append(dict(name=name, status="PASS" if passed else "FAIL", **details))

    for i in range(3):
        distance = math.dist(centers[i], centers[i+1])
        check(f"mesh_{i+1}_pitch_spacing", math.isclose(distance, 40., abs_tol=1e-9),
              measured_mm=distance, expected_mm=40.)
        check(f"mesh_{i+1}_axial_alignment", small_z[i] == large_z[i+1],
              driver_span_mm=small_z[i], driven_span_mm=large_z[i+1])
    for i in range(4):
        x, y = centers[i]
        check(f"G{i+1}_tip_envelope_inside_plate",
              x-31 >= 0 and x+31 <= 174 and y-31 >= 0 and y+31 <= 109)
        for j in range(i+2, 4):
            gap = math.dist(centers[i], centers[j])-62
            check(f"G{i+1}_G{j+1}_nonadjacent_tip_gap", gap > 0, gap_mm=gap)
    for name in ("servo_connection", "detailed_teeth_and_motion", "shaft_fit_and_retention",
                 "physical_verification", "release_and_print"):
        checks.append(dict(name=name, status="BLOCKED", reason="Unresolved inputs or unimplemented geometry/checks; see proposal."))
    report = dict(status="BLOCKED", scope="proposed envelope layout only",
                  approval_state="proposed", signed_output_input_ratio=-1/27,
                  centers_mm=centers, large_z_mm=large_z, rear_pinion_z_mm=small_z,
                  checks=checks)
    (output / "layout_report.json").write_text(json.dumps(report, indent=2)+"\n")

    canvas = Image.new("RGB", (1400, 1060), "#f5f7fa")
    draw = ImageDraw.Draw(canvas)
    font = lambda size: ImageFont.load_default(size=size)
    ink = "#172c40"
    colors = ["#2879ae", "#b97216", "#398368", "#8954a3"]

    def text(x, y, value, size=20, fill=ink):
        draw.text((x, y), value, font=font(size), fill=fill)

    text(45, 25, "COMPOUND GEARBOX / PROPOSED LAYOUT", 32)
    text(45, 70, "Four assemblies | Three meshes | 27:1 reduction | Servo interface unresolved", 22)
    text(45, 110, "TOP VIEW - pitch circles and tip envelopes; tooth geometry is not drawn", 18)
    scale = 4.0
    ox, oy = 55, 150
    draw.rectangle((ox, oy, ox+174*scale, oy+109*scale), fill="#e4e9ee", outline="#7c8b98", width=2)
    for i, ((x, y), color) in enumerate(zip(centers, colors)):
        cx, cy = ox+x*scale, oy+(109-y)*scale
        for radius, width in ((31, 2), (30, 3), (11, 2), (10, 3)):
            draw.ellipse((cx-radius*scale, cy-radius*scale, cx+radius*scale, cy+radius*scale), outline=color, width=width)
        draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill=color)
        text(cx-17, cy+16, f"G{i+1}", 22, color)
    text(800, 160, "GEAR TRAIN", 24)
    for i in range(4):
        text(800, 210+i*55, f"G{i+1}: large 60T + rear 20T", 21, colors[i])
    text(800, 450, "P1 > G2; P2 > G3; P3 > G4", 20)
    text(800, 490, "Nominal adjacent centers: 40 mm", 20)
    text(800, 525, "Plate proposal: 174 x 109 x 5 mm", 20)
    text(55, 603, "DEPTH DIAGRAM - shafts spread horizontally for clarity; Z is to scale", 19)
    base_y, zscale = 900, 6
    draw.rectangle((60, base_y-5*zscale, 1330, base_y), fill="#bec9d2", outline=ink)
    text(65, base_y+10, "Back plate Z = 0...5 mm. Rear pinions face the plate.", 20)
    for i, color in enumerate(colors):
        cx = 210+i*320
        top = large_z[i][1]
        draw.rectangle((cx-7, base_y-(top+2)*zscale, cx+7, base_y), fill="#8896a2")
        draw.rectangle((cx-15, base_y-large_z[i][0]*zscale,
                        cx+15, base_y-small_z[i][1]*zscale), fill=color)
        for span, half in ((large_z[i], 100), (small_z[i], 34)):
            draw.rectangle((cx-half, base_y-span[1]*zscale, cx+half, base_y-span[0]*zscale), fill=color, outline=ink)
        text(cx-90, 650, f"G{i+1}: Z {large_z[i][0]:g}...{top:g}", 19, color)
        text(cx-90, 675, f"P{i+1}: Z {small_z[i][0]:g}...{small_z[i][1]:g}", 19, color)
    text(55, 957, "All dimensions are proposed. Servo mounting envelope, shaft retention and running fits remain open.", 21)
    text(55, 996, "Layout evidence only. Detailed CAD, motion verification and print approval are still pending.", 21)
    canvas.save(output / "layout.png")
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Proposed gearbox layout</title>'
        '<style>body{margin:0;background:#f5f7fa}img{display:block;width:100%;max-width:1400px;margin:auto}</style>'
        '<img src="layout.png" alt="Proposed four-compound-gear layout, top and axial views">'
        '<p style="text-align:center"><a href="layout_report.json">Layout verification report</a></p></html>')
    print(json.dumps({"status": "BLOCKED", "reason": "Design inputs pending; layout checks only",
                      "output": str(output), "layout_failures": sum(c["status"] == "FAIL" for c in checks)}))
    return 1 if any(c["status"] == "FAIL" for c in checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
