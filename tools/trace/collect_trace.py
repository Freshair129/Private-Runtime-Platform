#!/usr/bin/env python3
"""Collect requirement/acceptance markers from every Python project into docs/registry/code-trace.json.

SDD-PRP-REPO section 9 items 2-3 and ADR-PRP-012 action item 5. For each project under apps/* and
workers/* that has a pyproject.toml and a tests/ directory, run ``uv run --locked pytest
--collect-only`` inside that project's own locked environment with tools/trace/pytest_trace_plugin.py
loaded, then merge the collected items into one deterministic JSON document.

Markers never change an acceptance status. Only an evidence receipt in docs/evidence/ does, and
tools/docs/validate_docs.py refuses any status other than NOT_RUN without both a collected test here
and a complete receipt there.

Usage:
  python tools/trace/collect_trace.py           # write docs/registry/code-trace.json
  python tools/trace/collect_trace.py --check   # exit 1 when the committed file is stale or markers are invalid

Requires uv on PATH and every project synced (uv sync --locked --group dev). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = Path(__file__).resolve().parent
REGISTRY = ROOT / "docs" / "registry"
OUTPUT = REGISTRY / "code-trace.json"
PROJECT_GLOBS = ("apps/*/pyproject.toml", "workers/*/pyproject.toml")
NO_TESTS_COLLECTED = 5  # pytest exit code


def discover_projects() -> list[Path]:
    projects: list[Path] = []
    for pattern in PROJECT_GLOBS:
        for pyproject in sorted(ROOT.glob(pattern)):
            if (pyproject.parent / "tests").is_dir():
                projects.append(pyproject.parent)
    return projects


def collect(project: Path) -> list[dict[str, Any]]:
    rel = project.relative_to(ROOT).as_posix()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "trace.json"
        env = dict(os.environ)
        env["PRP_TRACE_OUT"] = str(out)
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(PLUGIN_DIR) + (os.pathsep + existing if existing else "")
        env.setdefault("PYTHONUTF8", "1")
        command = [
            "uv", "run", "--locked", "pytest", "--collect-only", "-q", "-p", "pytest_trace_plugin", "tests",
        ]
        result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True)
        if result.returncode not in (0, NO_TESTS_COLLECTED):
            sys.stderr.write(result.stdout[-3000:] + result.stderr[-3000:])
            raise SystemExit(f"test collection failed in {rel} (exit {result.returncode})")
        if not out.exists():
            return []
        loaded: list[dict[str, Any]] = json.loads(out.read_text(encoding="utf-8"))
        return loaded


def tier_of(nodeid: str) -> str:
    parts = nodeid.split("::", 1)[0].replace("\\", "/").split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "tests" else "other"


def build(collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    registry = json.loads((REGISTRY / "requirements.json").read_text(encoding="utf-8"))
    requirement_ids = {r["id"] for r in registry["requirements"]}
    requirement_ids |= {r["id"] for r in registry.get("phase2_envelope", [])}
    acceptance_ids = {r["test"] for r in registry["requirements"] if r.get("test")}

    requirements: dict[str, list[str]] = {}
    acceptance: dict[str, dict[str, Any]] = {}
    projects: dict[str, Any] = {}
    errors: list[str] = []
    unmarked = 0

    for project, items in sorted(collected.items()):
        tiers: dict[str, int] = {}
        for item in items:
            tier = tier_of(item["nodeid"])
            tiers[tier] = tiers.get(tier, 0) + 1
            ref = f"{project}::{item['nodeid']}"
            if not item["req"] and not item["at"]:
                unmarked += 1
            for requirement in item["req"]:
                if requirement not in requirement_ids:
                    errors.append(f"{ref}: unknown requirement {requirement}")
                requirements.setdefault(requirement, []).append(ref)
            if len(item["at"]) > 1:
                errors.append(f"{ref}: a test may reference one acceptance case, found {item['at']}")
            for case in item["at"]:
                if case not in acceptance_ids:
                    errors.append(f"{ref}: unknown acceptance case {case}")
                entry = acceptance.setdefault(case, {"tests": [], "tiers": set()})
                entry["tests"].append(ref)
                entry["tiers"].add(tier)
        projects[project] = {"tests_collected": len(items), "tiers": dict(sorted(tiers.items()))}

    return {
        "kind": "CODE_TRACE",
        "generated_by": "tools/trace/collect_trace.py",
        "note": (
            "Derived from pytest markers req(...) and at(...). Markers never change acceptance "
            "status; a complete receipt in docs/evidence/ does (validate_docs.py enforces both)."
        ),
        "projects": projects,
        "requirements": {k: sorted(v) for k, v in sorted(requirements.items())},
        "acceptance": {
            k: {"tests": sorted(v["tests"]), "tiers": sorted(v["tiers"])}
            for k, v in sorted(acceptance.items())
        },
        "tests_without_markers": unmarked,
        "errors": sorted(errors),
    }


def render(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify the committed file instead of writing it")
    args = parser.parse_args()

    projects = discover_projects()
    if not projects:
        print("no Python projects with tests found under apps/* or workers/*", file=sys.stderr)
        return 1
    collected = {p.relative_to(ROOT).as_posix(): collect(p) for p in projects}
    data = build(collected)
    text = render(data)

    for error in data["errors"]:
        print(f"ERROR {error}", file=sys.stderr)
    if data["errors"]:
        return 1

    total = sum(p["tests_collected"] for p in data["projects"].values())
    summary = (
        f"{len(projects)} project(s), {total} tests, {len(data['requirements'])} requirements and "
        f"{len(data['acceptance'])} acceptance cases referenced"
    )
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if current != text:
            print(f"STALE {OUTPUT.relative_to(ROOT).as_posix()}; run: python tools/trace/collect_trace.py", file=sys.stderr)
            return 1
        print(f"OK: code-trace.json is current ({summary})")
        return 0
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT).as_posix()} ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
