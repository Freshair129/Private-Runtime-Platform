from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from prp.core.fleet.model import Node, QualificationReceipt, RuntimeDeployment


class RuntimeRegistry(Protocol):
    def get_node(self, node_id: str) -> Node | None: ...

    def list_deployments(self, pool_id: str) -> Sequence[RuntimeDeployment]: ...

    def current_receipt(self, node_id: str, profile_epoch: int) -> QualificationReceipt | None: ...


class RuntimeDescriber(Protocol):
    """Reads the worker `describe` port (contracts/openapi/prp-worker.yaml) for one node."""

    def describe(self, node: Node) -> RuntimeDeployment | None: ...
