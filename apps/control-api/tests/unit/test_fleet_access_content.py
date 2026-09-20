from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta

import pytest

from prp.core.access.model import AccessKeyGrant, AuthContext, Scope, has_scope, is_active
from prp.core.content.model import (
    Artifact,
    ArtifactGrant,
    can_read,
    grant_expiry_allowed,
    grant_is_live,
)
from prp.core.fleet.model import (
    Node,
    NodeState,
    QualificationReceipt,
    QualificationStatus,
    RuntimeDeployment,
    is_eligible,
)

NOW = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)


def node(state: NodeState = NodeState.ENABLED) -> Node:
    return Node(
        id="n1",
        pool_id="p1",
        pool_label="A",
        origin="https://worker-a.internal",
        physical_resource_id="hostA/GPU-0",
        runtime_uid="rt-a",
        state=state,
        version="v1",
    )


DEPLOYMENT = RuntimeDeployment(
    node_id="n1", profile_id="chat-default", profile_epoch=4, manager_uid=None
)


def receipt(
    status: QualificationStatus = QualificationStatus.PASS, epoch: int = 4
) -> QualificationReceipt:
    return QualificationReceipt(
        evidence_id="ev-1", node_id="n1", profile_epoch=epoch, status=status, recorded_at=NOW
    )


@pytest.mark.req("PRP-FR-018")
def test_eligibility_requires_enabled_node_and_pass_receipt_for_current_epoch() -> None:
    assert is_eligible(node(), DEPLOYMENT, receipt())
    assert not is_eligible(node(NodeState.DISABLED), DEPLOYMENT, receipt())
    assert not is_eligible(node(NodeState.DRAINING), DEPLOYMENT, receipt())
    assert not is_eligible(node(), DEPLOYMENT, None)
    assert not is_eligible(node(), DEPLOYMENT, receipt(QualificationStatus.FAIL))
    assert not is_eligible(node(), DEPLOYMENT, receipt(QualificationStatus.NOT_RUN))
    assert not is_eligible(node(), DEPLOYMENT, receipt(epoch=3))


@pytest.mark.req("PRP-FR-005")
def test_grant_and_auth_context_carry_no_key_material() -> None:
    names = {f.name for f in fields(AccessKeyGrant)} | {f.name for f in fields(AuthContext)}
    assert not {"secret", "key", "api_key", "token"} & names


def test_grant_activity_honours_expiry_and_revocation() -> None:
    grant = AccessKeyGrant(
        key_id="k1",
        key_prefix="prp_ab",
        principal_id="u1",
        organization_id="o1",
        scopes=frozenset({Scope.CHAT}),
        pool_ids=frozenset({"p1"}),
        expires_at=NOW + timedelta(days=1),
    )
    assert is_active(grant, now=NOW)
    assert not is_active(grant, now=NOW + timedelta(days=2))
    assert not is_active(replace(grant, revoked_at=NOW), now=NOW)
    context = AuthContext(organization_id="o1", principal_id="u1", key_id="k1", scopes=grant.scopes)
    assert has_scope(context, Scope.CHAT) and not has_scope(context, Scope.TTS)


def artifact(**overrides: object) -> Artifact:
    values: dict[str, object] = {
        "id": "art-1",
        "organization_id": "o1",
        "owner_principal_id": "u1",
        "mime_type": "audio/wav",
        "duration_seconds": 3.5,
        "expires_at": NOW + timedelta(hours=48),
    }
    values.update(overrides)
    return Artifact(**values)  # type: ignore[arg-type]


CONTEXT = AuthContext(
    organization_id="o1", principal_id="u2", key_id="k2", scopes=frozenset({Scope.ARTIFACTS})
)


@pytest.mark.req("PRP-FR-039")
def test_reads_require_owner_organization_and_live_artifact() -> None:
    assert can_read(artifact(), CONTEXT, now=NOW)
    other_org = AuthContext(
        organization_id="o2", principal_id="u9", key_id="k9", scopes=CONTEXT.scopes
    )
    assert not can_read(artifact(), other_org, now=NOW)
    assert not can_read(artifact(tombstoned_at=NOW), CONTEXT, now=NOW)
    assert not can_read(artifact(), CONTEXT, now=NOW + timedelta(hours=49))


@pytest.mark.req("PRP-FR-040")
def test_share_grant_ttl_is_bounded_by_24h_and_artifact_expiry() -> None:
    assert grant_expiry_allowed(artifact(), NOW + timedelta(hours=24), now=NOW)
    assert not grant_expiry_allowed(artifact(), NOW + timedelta(hours=25), now=NOW)
    short_lived = artifact(expires_at=NOW + timedelta(hours=2))
    assert not grant_expiry_allowed(short_lived, NOW + timedelta(hours=3), now=NOW)
    assert not grant_expiry_allowed(artifact(tombstoned_at=NOW), NOW + timedelta(hours=1), now=NOW)


def test_grant_dies_with_revocation_tombstone_or_expiry() -> None:
    grant = ArtifactGrant(id="g1", artifact_id="art-1", expires_at=NOW + timedelta(hours=1))
    assert grant_is_live(grant, artifact(), now=NOW)
    assert not grant_is_live(grant, artifact(), now=NOW + timedelta(hours=2))
    assert not grant_is_live(grant, artifact(tombstoned_at=NOW), now=NOW)
    revoked = ArtifactGrant(
        id="g1", artifact_id="art-1", expires_at=grant.expires_at, revoked_at=NOW
    )
    assert not grant_is_live(revoked, artifact(), now=NOW)
