# RCA-2026-09-29 — Canonical contract and derived artifact drift

**Date:** 2026-09-29
**Status:** RESOLVED_LOCALLY; independent review PASS; pending merge
**Scope:** WP03/G0 contract synchronization after pulling `main` at `57787c7`
**Risk:** HIGH; the mismatch crosses public contract, generated models, and worker conformance

## Symptom

The repository was not at a contract-consistent baseline after the latest `main` pull. The canonical OpenAPI YAML files required `runtime_epoch`, but the checked-in JSON twins and generated Python models were stale. The voice worker contract-conformance test failed.

## Evidence

- `export_json.py --check` failed because `contracts/openapi/prp-management.json` and `contracts/openapi/prp-worker.json` were stale.
- `gen_models.py --check` failed for the control API worker/management modules and the voice generated module.
- Example validation, documentation validation, and trace collection could pass while generated artifacts remained stale.
- The initial voice suite reported `21 passed, 1 failed` at the generated contract mismatch.

## Root Cause

The canonical contract change was pulled without regenerating and committing its derived JSON and generated Python artifacts as one controlled change. The repository therefore contained two contract authorities at runtime: updated YAML and stale generated artifacts.

## Why the issue escaped detection

- Canonical source and derived outputs were not treated as one commit/PR acceptance unit.
- The shared-baseline barrier did not require both generator checks before the change was consumed.
- Documentation, trace, examples, and control-only tests do not enforce YAML → JSON → generated-model parity.

## Proposed prevention

1. Author contract changes only in canonical YAML and regenerate JSON twins/models immediately.
2. Review canonical and derived diffs together and reject partial contract changes.
3. Make generator checks, examples, route conformance, control/voice tests, trace, and docs one B0 barrier.
4. Give generated outputs one named integrator and record the input SHA and commands in the receipt.

## Resolution in the isolated B0 worktree

The JSON twins and generated Python modules were regenerated from canonical YAML. The route-binding and valid-fixture follow-on mismatches were corrected under their separate RCAs. The full local B0 gate now passes; the change is not yet committed or merged, and no acceptance status changed.

## Handoff message

`[ROOT CAUSE] หลัง pull main ที่ 57787c7 canonical OpenAPI YAML เปลี่ยน แต่ JSON twins และ generated Python models ยัง stale ทำให้ export_json --check/gen_models --check fail และ voice conformance fail ที่ runtime_epoch. สาเหตุคือไม่ได้บังคับให้ source + derived artifacts เป็น commit/PR เดียวกันและไม่มี B0 parity barrier ก่อนแชร์ baseline. B0 แก้ใน isolated worktree แล้วและ local gates ผ่าน; รอ independent review ก่อน commit/push. ห้ามถือว่า WP03/G0, deploy หรือ acceptance ผ่านจาก baseline เดิม.`
