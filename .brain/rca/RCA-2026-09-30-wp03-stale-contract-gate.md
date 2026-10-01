# RCA: Stale WP01 gate text in management contract description

**Date:** 2026-09-30

**Status:** Resolved by the WP03 formal contract freeze update

## Symptom

The management OpenAPI description said that formal WP03 freeze remained gated by WP01 evidence after the repository owner had approved the WP01 scope/ownership receipt.

## Evidence

- `contracts/openapi/prp-management.yaml` described formal freeze as gated by WP01 evidence.
- `.brain/proposals/PROP-2026-09-30-wp01-scope-ownership-closure.md` records WP01 decision approval on 2026-09-30 and implementation `NOT_STARTED`.
- `docs/ROADMAP-PRP.md` records WP01 decision approval separately from implementation status.

## Root Cause

The D6 contract description preserved a historical gate sentence. The later WP01 approval updated roadmap and decision records but did not reconcile the embedded OpenAPI description. That sentence conflated WP01 implementation status with WP03's separate formal freeze decision.

## Why the issue escaped detection

The documentation validator checks links, structure, and OpenAPI references, while the contract generator faithfully exports descriptions without checking their lifecycle claims against decision receipts.

## Proposed prevention

- Reconcile status claims embedded in canonical contract descriptions against the current owner decision receipt during every freeze review.
- Keep WP01 decision approval, implementation status, WP03 freeze status, and RG0 implementation entry as separate fields in roadmap/DAG reviews.

## Resolution

The contract description now reflects the approved WP03 freeze and states that implementation and runtime qualification remain unperformed. The generated JSON was regenerated from canonical YAML.
