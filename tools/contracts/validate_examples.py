#!/usr/bin/env python3
"""Validate contracts/examples/* against the schemas declared in contracts/examples/index.json.

Each index entry maps an example file to either
  {"openapi": "openapi/prp-client.json", "schema": "JobRequest"}   -> a component schema inside an OpenAPI export
  {"schema_file": "schemas/runtime-environment-manifest.schema.json"} -> a standalone JSON Schema
Paths are relative to contracts/. OpenAPI 3.1 schema objects are validated as JSON Schema 2020-12.
Requires PyYAML and jsonschema (tools/contracts/requirements.txt). Exit 1 on any violation.
"""
from pathlib import Path
import json
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
EXAMPLES = CONTRACTS / "examples"


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)


def schema_for(entry: dict) -> dict:
    if "openapi" in entry:
        api = load(CONTRACTS / entry["openapi"])
        return {"$ref": f"#/components/schemas/{entry['schema']}", "components": api["components"]}
    return load(CONTRACTS / entry["schema_file"])


def main() -> int:
    index = load(EXAMPLES / "index.json")
    failures = 0
    for name, entry in index.items():
        example_path = EXAMPLES / name
        if not example_path.exists():
            print(f"FAIL {name}: example file missing")
            failures += 1
            continue
        schema = schema_for(entry)
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(load(example_path)), key=lambda e: list(e.path))
        target = entry.get("schema") or entry.get("schema_file")
        if errors:
            failures += 1
            print(f"FAIL {name} -> {target}")
            for error in errors:
                where = "/".join(str(p) for p in error.path) or "<root>"
                print(f"     {where}: {error.message}")
        else:
            print(f"ok   {name} -> {target}")
    unindexed = sorted(p.name for p in EXAMPLES.iterdir() if p.is_file() and p.name != "index.json" and p.name not in index)
    for name in unindexed:
        print(f"FAIL {name}: not listed in examples/index.json")
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
