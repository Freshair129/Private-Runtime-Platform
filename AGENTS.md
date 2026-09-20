# Core principles (NON-NEGOTIABLE)

### R1 — Think before action

Don't assume. Surface uncertainty before acting.

- State assumptions explicitly. If uncertain — **ask**.
- If multiple interpretations exist — present them, don't pick silently.
- If something is unclear — name what's confusing, then ask.
- Push back when a simpler approach exists.

> **Check:** *"Have I stated my assumptions before acting?"*

When assumptions exist, use:

[ASSUMPTIONS]

1. ...
2. ...
3. ...

If assumptions materially affect implementation,
request clarification before proceeding

---

### R2 — Simplicity first

Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No unrequested "flexibility" or "configurability".
- If 200 lines could be 50 — rewrite it.

> **Check:** *"Would a senior engineer say this is overcomplicated?"* If yes → simplify.

---

### R3 — Surgical changes

Touch only what you must.

- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you spot unrelated dead code — mention it, don't delete it.
- Remove only imports/variables/functions that **your own changes** made unused.

> **Check:** *Every changed line must trace directly to the user's request.*

---

### R4 — Goal-driven execution

Define success criteria before acting. Loop until verified.

Transform tasks into verifiable goals:

- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → ensure tests pass before **and** after.

For multi-step tasks, state a brief plan upfront:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

---

### R5 — Doc first — wait for approval

Never write or modify code without approved documentation.

Before any code change, inspect docs at two levels:

- **High-level (parent):** Ensure the change aligns with upstream intent — e.g. architecture decisions, product requirements, system design.
- **Same-level (peer):** Ensure the change doesn't conflict with adjacent features, modules, or contracts at the same abstraction layer.

Output the proposed documentation → **STOP** → ask for approval.
Do NOT write code in the same response as the doc proposal.

---

### R6 — RCA first

Never fix a bug without identifying its root cause.

- Do not provide blind fixes, guesses, or superficial patches.
- Explicitly state the root cause before proposing any solution.
- Only after the root cause is confirmed may you proceed to fix.
- Root cause must be supported by evidence.
- Root cause must be documented in `{workspace}\.brain\rca\`

See [RCA-Standard.md](./docs/standards/RCA-Standard.md) for the required template (Symptom → Evidence → Root Cause → Escape Analysis → Prevention).

---

### R7 — Definition of Done

A task is not complete until all 3 gates pass. Do not declare success before verification.

See [Definition-of-Done.md](./docs/standards/Definition-of-Done.md) for the full checklist (Acceptance → Success → Exit criteria).

---

### R8 — Change Risk Assessment

Every non-trivial change must be classified as **LOW / MEDIUM / HIGH**. State risk level before implementation.

See [Risk-Assessment.md](./docs/standards/Risk-Assessment.md) for classification criteria and required workflows per level.

---

### R9 — Scope Boundary

Implement only what was requested.

Do not:

- add optional features
- refactor unrelated code
- introduce future-proof abstractions
- perform opportunistic cleanup

Record out-of-scope findings separately.

---

## R10 — Complexity-Based Execution

Every task must be classified before execution.
Avoid under-engineering.
Avoid over-engineering.

Workflow:

Task
 ↓
Complexity Assessment
 ↓
C-1— Direct Implementation:Text → Code / C-2— Documentation-Driven Implementation:Text → Doc → Code / C-3— Architecture-Driven Implementation: Text → Doc → Diagram → Code
 ↓
Execute Workflow

When uncertainty exists, select the higher complexity level.

Escalation Rule

If uncertainty increases during execution:

C-1 → C-2
C-2 → C-3

Never downgrade complexity after approval without justification.

Selection Rule

Always choose the lowest complexity level that:

Maintains correctness
Maintains safety
Preserves maintainability

When uncertain:

Choose the higher level.

Verification Requirements
Level Verification
C-1 Validation
C-2 Tests + Documentation Review
C-3 Tests + Documentation Review + Architecture Review
Examples

Fix typo

C-1
Text → Code

Add login feature

C-2
Text → Doc → Code

Split monolith into services

C-3
Text → Doc → Diagram → Code

---

## Exception — Hotfix rule

Bypass "Doc first" **only** for trivial, non-structural changes:

- Minor syntax errors
- Typos
- Basic linting fixes

Output the corrected code directly. When in doubt — default to Doc first.

---

## Standard operating procedure (SOP)

### New feature / change request

1. Output proposed documentation / spec / metadata changes.
2. Analyze dependencies and assess impact on peer and parent layers.
3. End with: *"Please review and approve this documentation. I will generate the code once approved."*
4. alway show version diff after job done

### Bug fix request

1. Output `[ROOT CAUSE]` with analysis.
2. Explain the proposed solution.
3. **If complex** → wait for approval before proceeding.
   **If hotfix** → output the fix directly.

---

## Health check

*These guidelines are working when:*

- Diffs contain fewer unnecessary changes.
- Rewrites due to overcomplication decrease.
- Clarifying questions come **before** implementation, not after mistakes.

---
