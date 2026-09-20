"""pytest plugin loaded by tools/trace/collect_trace.py via ``-p pytest_trace_plugin``.

After collection it writes every item's node id together with its ``req`` / ``at`` marker arguments
as JSON to the path named by the PRP_TRACE_OUT environment variable. It never runs tests and never
alters results; with ``--collect-only`` pytest exits right after this hook.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def pytest_collection_finish(session: Any) -> None:
    target = os.environ.get("PRP_TRACE_OUT")
    if not target:
        return
    items = []
    for item in session.items:
        req = sorted({str(arg) for marker in item.iter_markers(name="req") for arg in marker.args})
        at = sorted({str(arg) for marker in item.iter_markers(name="at") for arg in marker.args})
        items.append({"nodeid": item.nodeid, "req": req, "at": at})
    Path(target).write_text(json.dumps(items, indent=1), encoding="utf-8")
