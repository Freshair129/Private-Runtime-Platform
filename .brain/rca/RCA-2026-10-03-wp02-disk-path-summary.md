# RCA: WP02 disk-path summary mismatch

**Date:** 2026-10-03

**Status:** Resolved; documentation corrected

**Scope:** WP02 evidence wording only

## Symptom

The Host B inventory narrative said the requested `F:\models` directory did not exist and that disk capacity had been measured on its nearest existing ancestor.

## Evidence

- The 2026-10-02 structured receipt and the 2026-10-03 refresh both record `checked_path` and `requested_path` as `F:\models` and set `path_existed` to `true`.
- `tools/wp24/host_inventory.py` sets `path_existed` by comparing the resolved probe to the requested target; it walks to an ancestor only while the target does not exist.
- A current read-only `Get-Item F:\models` observation also found the directory.

## Root Cause

The prose summary contradicted the structured receipt. It incorrectly described the `path_existed` result and was not reconciled with the collector's field semantics.

## Why the issue escaped detection

The documentation validator checks document structure and links but does not compare narrative claims with JSON field meanings or collector logic.

## Proposed prevention

For future host-inventory summaries, compare disk-path statements with both the generated receipt and the collector implementation before recording them. Keep the raw receipt as the source of truth.

## Resolution

The WP02 Host B record now states that `F:\models` existed at both structured collection times, links the refreshed receipts, and preserves the capacity measurement as a dated observation. No collector or host setting was changed.
