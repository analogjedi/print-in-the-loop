"""Kernel-projected SVG review views, separate from dimensional validation."""
import html
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from build123d import Color, ExportSVG, LineType, import_step
from .io import atomic_json, input_path, sha256


VIEWS = {
    "isometric": ((1, -1, 1), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "right": ((1, 0, 0), (0, 0, 1)),
}


def render(root, manifest_path, output):
    if output.exists():
        raise ValueError("output already exists; choose a new review directory")
    manifest = json.loads(manifest_path.read_text())
    source = input_path(root, str(manifest_path.parent / "assembly.step"))
    if sha256(source) != manifest["artifacts"]["assembly.step"]:
        raise ValueError("assembly STEP does not match build manifest checksum")
    shape = import_step(source)
    center = shape.bounding_box().center()
    distance = max(shape.bounding_box().size) * 4
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".views-", dir=output.parent))
    records, panels = [], []
    try:
        for name, (direction, up) in VIEWS.items():
            camera = tuple(c + d * distance for c, d in zip(center, direction))
            visible, hidden = shape.project_to_viewport(camera, viewport_up=up, look_at=center)
            exporter = ExportSVG(scale=5, line_weight=0.35, margin=1)
            exporter.add_layer("hidden", line_color=Color("gray"), line_type=LineType.ISO_DASH)
            exporter.add_layer("visible", line_color=Color("black"))
            if hidden:
                exporter.add_shape(hidden, layer="hidden")
            exporter.add_shape(visible, layer="visible")
            path = stage / f"{name}.svg"
            exporter.write(path)
            tree = ET.parse(path)
            title = ET.Element("{http://www.w3.org/2000/svg}title")
            title.text = f"{manifest['project_id']} — {name}; geometry unit: mm"
            tree.getroot().insert(0, title)
            tree.write(path, encoding="unicode", xml_declaration=True)
            records.append({"view_id": name, "file": path.name, "camera_origin_mm": camera,
                            "up_direction": up, "look_at_mm": list(center), "sha256": sha256(path)})
            panels.append(f'<figure><img src="{name}.svg" alt="{name} projection"><figcaption>{name}</figcaption></figure>')
        title = html.escape(manifest["project_id"])
        page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>{title} — CAD review</title><link rel="icon" href="data:,"><style>
body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#17212b;background:#f5f6f7}}
main{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0;padding:24px;background:white}}
img{{width:100%;height:230px;object-fit:contain}}figcaption{{text-transform:capitalize;margin-top:16px}}
code{{font-size:12px;overflow-wrap:anywhere}}</style>
<h1>{title} · CAD review</h1><p>Development evidence · geometry in millimeters · release BLOCKED</p>
<p>Kernel-projected views. Use geometry_report.json for measured dimensions. Hidden edges are dashed.</p>
<main>{''.join(panels)}</main><p>Build manifest SHA-256: <code>{sha256(manifest_path)}</code></p></html>'''
        (stage / "index.html").write_text(page)
        atomic_json(stage / "view_manifest.json", {"schema_version": 1, "status": "PASS",
                    "scope": "review_projection_generation", "build_manifest_sha256": sha256(manifest_path),
                    "views": records, "limitations": ["Human design review is not recorded.",
                        "Interactive viewer and section review are not commissioned."]})
        stage.rename(output)
        return {"status": "PASS", "output": str(output.relative_to(root)), "views": len(records)}
    except Exception:
        # Preserve intermediate projections for diagnosis; never publish a partial view set.
        raise
