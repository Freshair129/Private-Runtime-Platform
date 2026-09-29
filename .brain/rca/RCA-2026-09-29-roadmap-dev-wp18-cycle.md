# RCA-2026-09-29 — DEV gate depended on post-DEV WP18 evidence

**Status:** RESOLVED by the approved roadmap correction on 2026-09-29.
**Scope:** Documentation dependency graph; no application code or runtime was involved.
**Related:** [Roadmap](../../docs/ROADMAP-PRP.md) · [Execution DAG](../../docs/EXECUTION-DAG-PRP.md)

## Symptom

The approved roadmap could not be executed in topological order: the DEV gate required WP18 deployment/rollback runbooks, but WP18 depended on WP17, which the same roadmap scheduled after DEV.

## Evidence

- Before correction, the DEV milestone entry listed deploy/rollback runbooks from WP18 as an entry dependency.
- Roadmap WP17 is mixed/fault/security qualification; WP18 explicitly depends on WP17.
- The roadmap critical path placed DEV before mixed-load and restore/rollback qualification, so WP18 could not be completed before the DEV gate that required it.

## Root Cause

The plan treated two different outputs as one dependency: a short procedure to deploy and revert a development build, and WP18's full restore, recovery, and release rollback evidence. Their different positions in the delivery sequence were not represented as separate artifacts.

## Why the issue escaped detection

The milestone table and work-package dependency list were reviewed separately. No topological-cycle check was applied across milestone prerequisites and WP dependencies before the roadmap was marked approved.

## Proposed prevention

- Keep the bounded deploy/revert instruction in the DEV gate packet using WP04/WP25 deployment artifacts.
- Keep WP18 after WP17 for full restore, recovery, and rollback evidence.
- During each DAG review, validate dependencies across gates and work packages as one graph; preserve WP IDs and require an independent review before dispatch.

## Resolution

On 2026-09-29, the repository owner approved the execution DAG. `ROADMAP-PRP.md` now removes WP18 as a DEV prerequisite, and `EXECUTION-DAG-PRP.md` records the acyclic order DEV → WP17 → WP18 → WP19 → G3 → PROD. No SRS requirement or acceptance status changed.
