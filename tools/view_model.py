"""Send the requested test model to the local OCP CAD Viewer (VS Code or standalone)."""
import argparse
from pathlib import Path

from build123d import import_step
from ocp_vscode import show, set_port

parser = argparse.ArgumentParser()
parser.add_argument("step", nargs="?", default="builds/cube-sphere-v1/assembly.step")
parser.add_argument("--port", type=int, default=3939)
args = parser.parse_args()
shape = import_step(Path(args.step))
set_port(args.port)
show(shape, names=["Cube with sphere"], colors=["#2e85bf"], axes=True, axes0=True,
     grid=(True, False, False), reset_camera="reset")
