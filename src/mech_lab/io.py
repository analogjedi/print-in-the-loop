"""Atomic development output and traceable source identities."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def root_dir():
    root = Path.cwd().resolve()
    if not (root / "pyproject.toml").is_file() or not (root / "specs").is_dir():
        raise ValueError("run commands from the project root")
    return root


def input_path(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("input must be an existing file inside the project")
    return path


def output_path(root, value):
    path = (root / value).resolve()
    allowed = root / "builds"
    if allowed.is_symlink() or path == allowed or not path.is_relative_to(allowed):
        raise ValueError("outputs must be inside project builds/ (no escaping symlinks)")
    return path


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".report-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
    return result.stdout.strip() if result.returncode == 0 else None


def source_identity(root):
    names = ["pyproject.toml", "uv.lock", ".python-version", "AGENTS.md", "CLAUDE.md"]
    files = [root / name for name in names if (root / name).is_file()]
    for folder in ("src", "cad", "specs", "validation", "components", "decisions", "tools"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files.append(path)
    hashes = {str(p.relative_to(root)): sha256(p) for p in sorted(files)}
    content_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {"git_revision": git(root, "rev-parse", "HEAD"),
            "git_status": git(root, "status", "--porcelain"),
            "source_sha256": content_id, "files": hashes}
