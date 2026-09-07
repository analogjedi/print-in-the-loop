"""Public commands: JSON stdout/reports; concise stderr; bounded CAD workers."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from .io import atomic_json, input_path, output_path, root_dir, sha256
from .schema import load_spec, load_yaml, readiness


def parser(command):
    p = argparse.ArgumentParser(prog=command)
    p.add_argument("--report", help="JSON report path inside builds/")
    return p


def finish(args, operation):
    report_path = None
    try:
        root = root_dir()
        report_path = output_path(root, args.report or f"builds/reports/{uuid.uuid4().hex}.json")
        if report_path.exists():
            raise ValueError("report already exists; choose a new report path")
        result = operation(root)
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "exception_type": type(exc).__name__}
    result = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), **result}
    if report_path is not None and not report_path.exists():
        try:
            atomic_json(report_path, result)
        except OSError as exc:
            result = {"schema_version": 1, "status": "FAIL", "error": f"cannot write report: {exc}"}
    print(json.dumps(result, indent=2, allow_nan=False))
    print(f"{result['status']}: {result.get('scope', result.get('error', 'see JSON report'))}", file=sys.stderr)
    return {"PASS": 0, "NOT_APPLICABLE": 0, "FAIL": 1, "BLOCKED": 2}[result["status"]]


def worker(root, task, *arguments, timeout):
    env = dict(os.environ, XDG_CACHE_HOME=str(root / ".tools/cache"))
    result = subprocess.run([sys.executable, "-m", "mech_lab.worker", task, *map(str, arguments)],
                            cwd=root, capture_output=True, text=True, timeout=timeout, env=env)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"CAD worker failed ({result.returncode}): {result.stderr[-4000:]}") from exc
    if result.returncode and data.get("status") == "PASS":
        raise ValueError("worker returned inconsistent exit status")
    if result.stderr:
        data["worker_diagnostics"] = result.stderr[-4000:]
    return data


def validate_spec():
    p = parser("validate_spec")
    p.add_argument("spec")
    p.add_argument("--scope", choices=["schema", "build", "release"], default="build")
    args = p.parse_args()

    def run(root):
        path = input_path(root, args.spec)
        spec = load_spec(path)
        blockers = readiness(spec, args.scope)
        policy_path = input_path(root, "validation/release_policy.yaml")
        policy = load_yaml(policy_path)
        if args.scope == "release" and policy["approval_state"] != "approved":
            blockers.append("release policy is proposed, not approved")
        return {"status": "BLOCKED" if blockers else "PASS", "scope": args.scope,
                "project_id": spec.project_id, "schema_status": "PASS", "blockers": blockers,
                "specification_sha256": sha256(path), "policy_sha256": sha256(policy_path),
                "limitations": ["Schema validity does not establish engineering readiness or approval."]}

    sys.exit(finish(args, run))


def build_design():
    p = parser("build_design")
    p.add_argument("spec")
    p.add_argument("--output", required=True, help="new directory inside builds/")
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()

    def run(root):
        path = input_path(root, args.spec)
        spec = load_spec(path)
        blockers = readiness(spec, "build")
        if blockers:
            return {"status": "BLOCKED", "scope": "build", "blockers": blockers}
        return worker(root, "build", path, output_path(root, args.output), timeout=args.timeout)

    sys.exit(finish(args, run))


def inspect_geometry():
    p = parser("inspect_geometry")
    p.add_argument("step")
    p.add_argument("--spec", required=True)
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()
    sys.exit(finish(args, lambda root: worker(root, "inspect", input_path(root, args.step),
        input_path(root, args.spec), timeout=args.timeout)))


def render_review():
    p = parser("render_review")
    p.add_argument("manifest")
    p.add_argument("--output", required=True)
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()
    sys.exit(finish(args, lambda root: worker(root, "render", input_path(root, args.manifest),
        output_path(root, args.output), timeout=args.timeout)))


def environment_report():
    p = parser("environment_report")
    args = p.parse_args()
    sys.exit(finish(args, lambda root: worker(root, "environment", timeout=30)))
