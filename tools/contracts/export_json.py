#!/usr/bin/env python3
"""Export contracts/openapi/*.yaml (canonical) to sibling .json files (derived).

Usage:
  python tools/contracts/export_json.py          # (re)write every stale .json
  python tools/contracts/export_json.py --check  # exit 1 if any .json is missing or stale

YAML anchors/aliases are expanded on export. Output is UTF-8, two-space indented, key order
preserved, single trailing newline. Requires PyYAML (see tools/contracts/requirements.txt).
The .json files exist for stdlib-only consumers such as tools/docs/validate_docs.py; edit the YAML.
"""
from pathlib import Path
import argparse
import json
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "contracts" / "openapi"


def render(yaml_path: Path) -> str:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify exports instead of writing them")
    args = parser.parse_args()

    sources = sorted(OPENAPI.glob("*.yaml"))
    if not sources:
        print(f"no YAML contracts found under {OPENAPI}", file=sys.stderr)
        return 1

    stale: list[str] = []
    for source in sources:
        target = source.with_suffix(".json")
        rendered = render(source)
        current = target.read_text(encoding="utf-8") if target.exists() else None
        rel = target.relative_to(ROOT).as_posix()
        if current == rendered:
            print(f"unchanged {rel}")
            continue
        if args.check:
            stale.append(rel)
            continue
        target.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote     {rel}")

    if args.check and stale:
        print("STALE JSON export(s); run: python tools/contracts/export_json.py", file=sys.stderr)
        for rel in stale:
            print(f"  {rel}", file=sys.stderr)
        return 1
    if args.check:
        print(f"OK: {len(sources)} JSON export(s) match their YAML source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
