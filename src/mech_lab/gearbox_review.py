"""Offline, self-contained WebGL review of actual exported CAD meshes."""
import base64
import json
import html
import re
from pathlib import Path
from cad.assemblies.gearbox import layout


def assembly_guide_html(root):
    """Render the guide's assembly-facing Markdown subset without remote assets."""
    source = (root / "docs/gearbox_build_and_assembly.md").read_text()
    source = source[source.index("## What you need beyond the printed parts"):]

    def inline(text):
        text = html.escape(text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        return re.sub(r"\[([^\]]+)\]\((https://[^\s)]+)\)",
                      r'<a href="\2">\1</a>', text)

    result = []
    for block in re.split(r"\n\s*\n", source.strip()):
        lines = block.splitlines()
        if lines[0].startswith("## "):
            result.append(f"<h3>{inline(lines[0][3:])}</h3>")
        elif lines[0].startswith("|"):
            rows = [[inline(cell.strip()) for cell in line.strip().strip('|').split('|')]
                    for line in lines]
            head = '<tr>' + ''.join(f'<th scope="col">{c}</th>' for c in rows[0]) + '</tr>'
            body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>'
                           for row in rows[2:])
            result.append(f'<div class="table-scroll"><table><thead>{head}</thead><tbody>{body}</tbody></table></div>')
        elif re.match(r"\d+\. ", lines[0]):
            items = re.split(r"\n(?=\d+\. )", block)
            result.append('<ol>' + ''.join('<li>' + inline(re.sub(r"^\d+\. ", '', item).replace('\n', ' ')) + '</li>' for item in items) + '</ol>')
        else:
            result.append(f"<p>{inline(' '.join(lines))}</p>")
    return '\n'.join(result)


def create_review(stage,manifest,spec,root):
    (stage/"assembly_guide.md").write_text((root/"docs/gearbox_build_and_assembly.md").read_text())
    meshes=[]
    color={p["id"]:p["color"][:3] for p in manifest["parts"]}
    for path in sorted((stage/"review_meshes").glob("*.stl")):
        name=path.stem; i=int(name[-1])-1 if name.startswith("compound_gear_") else None
        gear=i is not None
        attached=name in ("servo_horn_adapter","servo_horn_reference")
        rotor=i if gear else (0 if attached else -1)
        meshes.append({"name":name,"data":base64.b64encode(path.read_bytes()).decode(),
                       "color":color.get(name,[.38,.41,.44]) if name!="servo_horn_reference" else [.7,.7,.66],
                       "rotor":rotor,"center":layout()[rotor] if rotor>=0 else [0,0],
                       "cradle":name.startswith(("servo_cradle","cradle_post","servo_reference")),
                       "explode":(18+8*i if gear else 52 if attached else 80 if name.startswith("servo") else 44 if "retainer" in name else 0)})
    template=Path(__file__).with_name("gearbox_viewer.html").read_text()
    (stage/"review.html").write_text(template.replace("__MESH_DATA__",json.dumps(meshes))
                                   .replace("__ASSEMBLY_GUIDE__",assembly_guide_html(root)))
