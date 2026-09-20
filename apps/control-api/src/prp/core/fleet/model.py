from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class NodeState(StrEnum):
    DISABLED = "DISABLED"
    DRAINING = "DRAINING"
    ENABLED = "ENABLED"


class ProfileKind(StrEnum):
    CHAT = "chat"
    ASR = "asr"
    TTS = "tts"


class QualificationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    pool_id: str
    pool_label: str
    origin: str
    physical_resource_id: str
    runtime_uid: str
    state: NodeState
    version: str


@dataclass(frozen=True, slots=True)
class ModelProfile:
    id: str
    kind: ProfileKind
    revision: str
    profile_hash: str
    approved: bool


@dataclass(frozen=True, slots=True)
class RuntimeDeployment:
    node_id: str
    profile_id: str
    profile_epoch: int
    manager_uid: str | None


@dataclass(frozen=True, slots=True)
class QualificationReceipt:
    evidence_id: str
    node_id: str
    profile_epoch: int
    status: QualificationStatus
    recorded_at: datetime


def is_eligible(
    node: Node,
    deployment: RuntimeDeployment,
    receipt: QualificationReceipt | None,
) -> bool:
    """Registration is not eligibility; health is not qualification."""
    if node.state is not NodeState.ENABLED or deployment.node_id != node.id:
        return False
    return (
        receipt is not None
        and receipt.node_id == node.id
        and receipt.status is QualificationStatus.PASS
        and receipt.profile_epoch == deployment.profile_epoch
    )
