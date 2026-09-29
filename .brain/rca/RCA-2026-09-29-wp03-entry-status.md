# RCA: WP03 entry status and WP24 evidence reconciliation

**Date:** 2026-09-29  
**Status:** Resolved; WP01 formal-entry gate remains open  
**Scope:** Documentation and gate-status interpretation only

## Symptom

The execution DAG describes WP24 run 2 as having an open reviewer disposition that keeps WP24 partial for WP03. The roadmap also marks WP24 `NOT_STARTED`, while the canonical WP24 run 1 decision receipt says its approved decision satisfies the WP24 gate for WP03.

## Evidence

- `docs/evidence/wp24/WP24-2026-09-20-run1.json`: decision receipt approved 2026-09-24; selects candidate A; `approval_note` explicitly says the WP24 gate for WP03 is satisfied.
- `docs/evidence/wp24/WP24-2026-09-24-run2/A/FINDINGS.md` and `docs/CHANGELOG-PRP.md`: run 2 records measurements only and does not change run 1 verdicts, status, or disposition. It narrows DEV-07 to DEV-09; cache-derived figures are not like-for-like.
- `docs/ROADMAP-PRP.md` §3: WP01 and WP24 remain `NOT_STARTED`; WP03 depends on WP01 and WP24.
- `docs/EXECUTION-DAG-PRP.md` §2 now records run 1 as satisfying the WP24 decision prerequisite; run 2/DEV-09 is a separate measurement limitation.

## Root Cause

The derived DAG status collapsed two separate facts into one gate state: the approved run 1 candidate-selection receipt and run 2's unresolved question about whether a performance-comparison trigger was met. It treated the run 2 review note as revoking or withholding run 1's WP03 entry approval. The roadmap's work-package status was not reconciled against the canonical receipt.

## Why the issue escaped detection

The review pass summarized run 2 findings and roadmap status without checking the `decision_receipt.approval_note` in run 1 against the run 2 statement that it does not alter run 1. No validator currently joins evidence receipts to roadmap/DAG status.

## Proposed prevention

- Derive WP24 selection/gate status from the approved run 1 receipt; track run 2/DEV-09 as a separate measurement limitation and reviewer trigger.
- Never infer acceptance-test PASS from a decision receipt; all 92 runtime acceptance cases remain `NOT_RUN`.
- Reconcile WP01 separately. WP24 approval alone does not satisfy WP03's WP01 dependency.
- Add a documentation review check that compares roadmap and DAG gate claims against canonical decision receipts before approval.

## Resolution

Candidate A's run 1 approval remains in force and satisfies the WP24 decision prerequisite for WP03. The roadmap and DAG now separate that decision from implementation status and DEV-09 measurement limitations. WP01 remains `NOT_STARTED` and formal WP03 readiness remains pending its separate scope/ownership receipt. Prevention follow-up: include receipt-to-roadmap/DAG reconciliation in future gate reviews; no automated join validator was added in this scoped correction.
