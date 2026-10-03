# RCA-2026-10-03 — WP02 prerequisite was missing from the RG0 graph

**Status:** RESOLVED by the WP02/RG0 documentation correction on 2026-10-03.
**Scope:** Documentation dependency graph and qualification procedure; no application code or runtime was involved.
**Related:** [WP02 procedure](../../docs/WP02-HARDWARE-RUNTIME-INVENTORY.md) · [Roadmap](../../docs/ROADMAP-PRP.md) · [Execution DAG](../../docs/EXECUTION-DAG-PRP.md)

## Symptom

The execution plan stated that RG0 required WP02 hardware/runtime inventory, but its Mermaid graph did not contain a `WP02 → RG0` edge. The roadmap and registry also declared WP25 dependent on WP03 only. A scheduler following the graph could therefore start WP25 before the required inventory gate.

## Evidence

- `docs/EXECUTION-DAG-PRP.md` §2 and §6 said RG0 was pending WP02 inventory and that WP25/WP04 must wait for RG0.
- The same DAG's edge list contained `WP03 --> RG0` and `RG0 --> WP25`, but no `WP02 --> RG0` edge.
- `docs/ROADMAP-PRP.md` listed WP25 as depending on WP03 only.
- `docs/registry/roadmap.json` repeated the same incomplete WP25 dependency.
- The baseline had no canonical WP02 inventory collection procedure or artifact boundary; `workers/voice/tests/hardware/` had no physical tests.

## Root Cause

The WP02 prerequisite was written in gate prose but not represented in every dependency authority. The roadmap/registry dependency data and Mermaid DAG were reviewed as separate views, and WP02 had no explicit evidence-procedure document to force the missing edge and artifact boundary into review.

## Why the issue escaped detection

The existing documentation validator checked links, requirement/roadmap structure and OpenAPI references, but did not semantically compare gate prose, Mermaid edges and roadmap/registry prerequisites. The prior DAG cycle review verified acyclicity of the encoded graph, so it could not detect a prerequisite that was absent from that graph.

## Proposed prevention

- Keep WP02 inventory as a canonical procedure with explicit RG0 entry/exit rules.
- Reconcile the Mermaid DAG, Markdown roadmap and JSON registry together whenever a gate prerequisite changes.
- Require the independent Luna Max gate review to check both the prose and the encoded edges before dispatch.
- Keep WP02 dossiers separate from acceptance receipts so inventory cannot silently promote runtime acceptance.

## Resolution

The approved correction adds `WP02 --> RG0`, changes WP25's dependency to `WP03, RG0` in both roadmap views, adds the WP02 procedure and records this RCA. No application code, contract shape, acceptance status, credentials, server access or deployment was changed.
