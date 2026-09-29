---
document_id: PROP-2026-09-30-WP01
title: "WP01 scope and ownership closure"
version: 0.1.0
status: approved
created_at: 2026-09-30
complexity: C-3
risk: HIGH
decision_status: APPROVED
implementation_status: NOT_STARTED
owner_decision: "APPROVED_BY_REPOSITORY_OWNER_ON_2026-09-30; ROLE_LEVEL_PRODUCT_AND_ARCHITECTURE_ACCOUNTABILITY_ACCEPTED"
---

# WP01 scope and ownership closure

## 1. Purpose and boundary

Record the owner-backed scope and ownership decision that closes WP01 and unblocks formal WP03 entry. The approved decision adopts the current PRD/SRS baseline; requirement statements, IDs, product boundaries, and acceptance criteria remain unchanged. Approval/authority status prose and frontmatter are updated. It does not formally freeze WP03, qualify hardware, approve a DEV/PROD deployment, or mark acceptance tests as passed.

## 2. Evidence and current status

- [ROADMAP-PRP.md](../../docs/ROADMAP-PRP.md) §3 identifies WP01 as "Scope & ownership freeze", owned by Product + Architecture, with deliverables for PRD/SRS boundaries, requirement IDs, and job dimensions. The owner approved the WP01 decision on 2026-09-30; implementation remains `NOT_STARTED`.
- [PRD-PRP.md](../../docs/PRD-PRP.md) §5 defines the P1-A/P1-B/P1-C and P2 scope matrix; §7 states product boundaries; §10 assigns acceptance responsibility. Its v0.3.0 baseline is now `approved`.
- [SRS-PRP.md](../../docs/SRS-PRP.md) §§1–3 define scope authority, operating context, and ownership boundaries. It records 56 FR, 24 NFR, and 12 SEC requirements, with stable IDs and traceability in §15. Its v0.3.0 baseline is now `approved`.
- [SRS-PRP.md](../../docs/SRS-PRP.md) §8 defines the API/job kinds; P1 asynchronous jobs are ASR and TTS only. §9 keeps job outcome, execution, capacity lease, artifact, voice-turn, and LINE-delivery dimensions separate. §14 lists the G0–G3 and integration release gates.
- [PROP-2026-09-29-wp03-contract-authority-freeze.md](PROP-2026-09-29-wp03-contract-authority-freeze.md) and [RCA-2026-09-29-wp03-entry-status.md](../rca/RCA-2026-09-29-wp03-entry-status.md) record that WP24's decision receipt satisfies its WP03 prerequisite; WP01 was the remaining gate before this approval.
- This approved proposal is the WP01 owner decision receipt. The repository owner approved the existing product/requirement baseline and role-level accountability on 2026-09-30; no individual execution assignees are inferred.

## 3. Approved WP01 baseline

Adopt the existing PRD/SRS content as the WP01 baseline, with these boundaries:

1. **Product scope:** self-hosted, application-neutral PRP core. P1-A covers independent bootstrap, keys/quotas, text/chat, routing, and control foundations; P1-B adds ASR/TTS, async speech jobs/artifacts, and the independent playground; P1-C covers qualification and pilot. P2 image/video remains an envelope for a separate later decision.
2. **Explicit exclusions:** no P1 realtime/full-duplex calls, wake word, speaker identification, voice cloning, music, arbitrary async DAG, generative image/video, untrusted customer sharing on one engine, or automatic cloud inference fallback. Zuri/LINE is a separately accepted integration, not a core dependency.
3. **Operating context:** two independent LAN hosts are the planning context, not an approved production hardware profile. Their nominal VRAM figures do not assert qualified capacity; WP02 and later qualification retain those decisions.
4. **Requirement baseline:** retain PRP-FR-001..056, PRP-NFR-001..024, and PRP-SEC-001..012 as the current stable requirement set. Preserve requirement IDs and traceability; no requirement is retired, added, or changed by WP01 closure.
5. **Job dimensions:** P1 sync interfaces include chat, ASR, and TTS; native async jobs are ASR and TTS only. Preserve separate outcome, execution, capacity-lease, artifact, client voice-turn, and LINE-delivery states. Quota dimensions remain requests, tokens, audio seconds, active jobs, queued jobs, and storage bytes.
6. **Acceptance boundary:** the 92 runtime acceptance cases remain `NOT_RUN`; decision approval is not implementation, qualification, or release evidence.

## 4. Approved ownership model

Adopt role-based accountability already present in the sources:

| Responsibility | Proposed accountable role | Source |
|---|---|---|
| Confirm product scope and proposed SLO | Product owner | PRD §10 |
| Confirm technical boundary, requirement/job dimensions, and traceability | Architecture / technical owner | Roadmap WP01; SRS §§1–3, 8–9, 15 |
| Confirm isolation, egress, rights, and security acceptance | Security owner | PRD §10 |
| Confirm deployment and restore acceptance | Operator | PRD §10 |
| Record test evidence and status | QA | PRD §10 |
| Accept external app/channel integration | Integration owner | PRD §10 |

The repository does not identify individual people for these roles. The repository owner approved role-level accountability as sufficient for WP01; named execution assignees will be recorded when implementation work packages are opened. No individual names are inferred.

## 5. Changes applied after approval

1. Recorded the repository owner's approval of the Product + Architecture role-level decision on 2026-09-30; named execution assignees remain for implementation planning.
2. Changed PRD and SRS front-matter status from `draft-for-review` to `approved` and updated approval-status prose; kept requirement statements, IDs, product boundaries, acceptance criteria, and version numbers unchanged.
3. Updated the WP01 roadmap trace to cite this approved decision receipt; the scope/ownership decision is approved while implementation remains `NOT_STARTED`.
4. Reconciled the execution DAG, API status note, ADR, and README to show WP01 approval while preserving implementation, runtime, and release gates.
5. Left WP03 contract metadata at `0.4.0-draft` / `DRAFT` / freeze gate `WP03`; a separate formal WP03 freeze decision remains pending.

## 6. Parent, peer, risk, and scope

- **Parent sources:** PRD product goals and scope; SRS requirement and acceptance authority.
- **Peer sources:** roadmap/DAG dependencies, API job boundary, architecture and traceability views.
- **Risk:** HIGH, because approving these boundaries establishes the product and requirement baseline used by downstream implementation and release decisions.
- **Out of scope:** changing requirements, naming individual staff, changing WP02 hardware status, formal WP03 contract freeze, application implementation, runtime testing, DEV deployment, production release, or changing any acceptance status.

## 7. Acceptance and exit evidence

- The repository owner approved the P1/P2 boundary, exclusions, proposed SLO treatment, requirement set, job kinds/dimensions, and role-level Product/Architecture ownership on 2026-09-30.
- No exception to the proposed baseline was recorded; named implementation assignees remain a later work-package assignment.
- This approved proposal is linked from WP01 in the roadmap; the execution DAG records the decision as satisfied.
- PRD/SRS status is `approved`; requirement IDs and acceptance criteria are unchanged, and all 92 acceptance statuses remain `NOT_RUN`.
- Documentation validation reports no broken links or structure errors. WP03 remains a separate formal freeze decision.

## 8. Version diff after approval

| Artifact | Before | After approval |
|---|---|---|
| WP01 closure proposal | — | `0.1.0`, `approved`; decision receipt recorded |
| PRD / SRS | `0.3.0`, `draft-for-review` | `0.3.0`, `approved`; approval-status prose updated, requirement statements/IDs/boundaries/acceptance criteria unchanged |
| Roadmap | `0.4.0-draft`, `approved`; WP01 `NOT_STARTED` | `0.4.0-draft`, `approved`; WP01 decision approved, implementation `NOT_STARTED` |
| Management / worker contracts | `0.4.0-draft`, `DRAFT`, gate `WP03` | Unchanged until a separate formal WP03 freeze decision |
| Runtime acceptance | 92 `NOT_RUN` | Unchanged |

## 9. Owner review

The repository owner approved the WP01 baseline and role-level ownership on 2026-09-30. This receipt closes WP01's decision gate; it does not freeze WP03 or change implementation/runtime acceptance status.
