#!/usr/bin/env python3
"""Diff two ev02_probe.py snapshots taken before and after a runtime restart for WP24 EV02
(docs/WP24-EXPERIMENT-PROCEDURE.md, gate PRP-FR-010..015; related to EV06 restart identity).

Pure file processing: reads the ``extracted_identifiers`` map two ev02_probe.py JSON outputs
carry and reports what was added, removed, changed or stayed the same. No network access, no
device access. Standard library only; computes no verdict.

Usage:
  python tools/wp24/ev02_restart_identity.py --before wp24-out/ev02_probe_B_B_<ts1>.json \\
      --after wp24-out/ev02_probe_B_B_<ts2>.json --out wp24-out
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import wp24_common as common


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--before", required=True, help="ev02_probe.py JSON output captured before the restart"
    )
    parser.add_argument(
        "--after", required=True, help="ev02_probe.py JSON output captured after the restart"
    )
    parser.add_argument(
        "--out", default="./wp24-out", help="output directory (default: ./wp24-out)"
    )
    return parser.parse_args(argv)


def load_probe(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    observations: list[str] = []

    before_data = load_probe(Path(args.before))
    after_data = load_probe(Path(args.after))
    before_ids = before_data.get("extracted_identifiers") or {}
    after_ids = after_data.get("extracted_identifiers") or {}

    diff = common.diff_identifiers(before_ids, after_ids)

    before_candidate = before_data.get("candidate")
    after_candidate = after_data.get("candidate")
    candidate = before_candidate or after_candidate or "unknown"
    before_host = before_data.get("host_id")
    after_host = after_data.get("host_id")
    host_id = before_host or after_host or "unknown"
    if before_candidate != after_candidate:
        observations.append(
            f"before candidate={before_candidate!r} != after candidate={after_candidate!r}; "
            "diff may not be meaningful"
        )
    if before_host != after_host:
        observations.append(
            f"before host_id={before_host!r} != after host_id={after_host!r}; "
            "diff may not be meaningful"
        )

    if diff["added"] or diff["removed"] or diff["changed"]:
        observations.append(
            "identifiers differ between the before/after snapshots; review "
            "WP24-EXPERIMENT-PROCEDURE.md EV02 step 2 / EV06 for whether this is a restart "
            "epoch the candidate exposes or something else"
        )
    else:
        observations.append(
            "no extracted identifier differs between the before/after snapshots; if a "
            "restart actually happened between the two captures, this may mean the candidate "
            "exposes no distinguishing restart identity through these endpoints (an EV02 "
            "finding for the reviewer)"
        )

    measurements = [
        {"name": "identifiers_before_count", "value": len(before_ids)},
        {"name": "identifiers_after_count", "value": len(after_ids)},
        {"name": "identifiers_added_count", "value": len(diff["added"])},
        {"name": "identifiers_removed_count", "value": len(diff["removed"])},
        {"name": "identifiers_changed_count", "value": len(diff["changed"])},
        {"name": "identifiers_unchanged_count", "value": len(diff["unchanged"])},
    ]

    timestamp = common.utc_now_iso().replace(":", "").replace("-", "")
    filename = f"ev02_restart_identity_{candidate}_{host_id}_{timestamp}.json"
    payload = {
        "kind": "WP24_EV02_RESTART_IDENTITY_DIFF",
        "generated_at_utc": common.utc_now_iso(),
        "command_line": common.command_line(),
        "candidate": candidate,
        "host_id": host_id,
        "before_file": Path(args.before).name,
        "after_file": Path(args.after).name,
        "diff": diff,
        "measurements": measurements,
        "observations": observations,
        "source_observations": [],
        "artifacts": [filename],
    }
    path = common.write_json(Path(args.out), filename, common.redact_json(payload))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
