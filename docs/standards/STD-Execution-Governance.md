---
title: "STD: Execution Governance Standard"
doc_id: "STD-EXECUTION-GOVERNANCE"
status: "stable"
version: "3.0.0"
updated: "2026-09-20"
source_of_truth: true
related_adrs: ["ADR-015", "ADR-018", "ADR-019"]
---

# STD: Execution Governance Standard

**Title:** Execution Governance Standard  
**Summary:** Minimum viable process selection for safe work execution, mapped to Access Scope H0-H4 (enforceable capability tiers) and W-Scale fan-out control.  
**Version:** 3.0.0  
**Updated:** 2026-09-20  
**Role:** Governance / Process Framework  
**Legacy Alias:** R10, Complexity-Based Execution Path

---

## 1. Core Principle

Choose the minimum process that preserves correctness, safety, and maintainability.

- Avoid under-engineering.
- Avoid over-engineering.
- Every non-trivial task must declare **Complexity Level** and **Access Scope** (H) before execution.
- Access Scope defaults from the Complexity Level; declare it explicitly only to override upward.
- When uncertainty exists, choose the higher level.
- Authority uncertainty must fail closed: resolve the canonical source before using a conflicting copy for approval, implementation, or audit.

## 2. Complexity Levels

| Level | Name | Workflow | Use When | Recommended Context |
| --- | --- | --- | --- | --- |
| **C-0** | Trivial | Text -> Code | Typo, copy, config, comment, or tiny isolated change | H0 |
| **C-1** | Direct | Text -> Code | Small task, clear bug fix, single-file low-risk change | H0-H1 |
| **C-2** | Doc-Driven | Text -> Doc -> Code | Feature work, multi-file work, medium-risk logic | H1-H2 |
| **C-3** | Architecture-Driven | Text -> Doc -> Diagram -> Code | Architecture, governance, security, cross-system, platform-level work | H3 (H4 by declaration) |

## 3. H-Scale: Access Scope

`H` is the executor's tool and permission ceiling. It is not graph distance, retrieval radius, token budget, risk, or context profile.

| H Tier | Capability set | Scope reading | Extra requirement |
| --- | --- | --- | --- |
| **H0** | read one bounded file | Subtask / PR | — |
| **H1** | + search (glob/grep) | Task / Component | — |
| **H2** | + write and multi-file edit | Story / Feature | — |
| **H3** | + shell execution | Epic / Module | — |
| **H4** | + network and full configured capabilities | Architecture / cross-system / platform | approval before implementation |

Default mapping:

```yaml
complexity_access_mapping:
  C-0: H0
  C-1: H1
  C-2: H2
  C-3: H3   # H4 only by declaration + approval
```

Rules:

- H defaults from Complexity; declare it only to override upward.
- H4 requires approval before implementation.
- For C-2 scope, the grantor is the lead or architect.
- For C-3 scope, the grantor is the owner.
- Do not downgrade complexity or access after approval without recorded justification.
- H5/H6 are abolished. Platform-level work is C-3 at H4.

## 4. W-Scale: Fan-out Control

`H` controls capability. `W` controls fan-out or branching width.

| W Scale | Meaning | Rule |
| --- | --- | --- |
| **W2** | Optimal | `3-5` sibling or peer connections; normal operation |
| **W3** | Warning | `6-8` connections; lead review required |
| **W4** | Super-hub danger | `9+` connections; block deployment until refactored |

Use W-Scale when evaluating:

- graph node degree
- roadmap branching width
- feature or task decomposition breadth
- context packets at risk of token explosion

Dense coupling can shorten graph paths. Therefore, a wide retrieval radius can indicate a missing hub or an oversized task, while high fan-out is the direct coupling warning owned by W-Scale.

## 5. Human-First Artifact Requirements

Normal SWE documents are the primary authoring format. Genesis atoms may be derived after review, but agents and developers are not required to author work directly as atom blocks.

| Access Scope | Required Human Artifact | Optional Supporting Artifact | Derived Atom Examples |
| --- | --- | --- | --- |
| **H0** | Change note or task comment | Test evidence | `PARAMS`, `HOOK` |
| **H1** | Task spec or LLD section | API snippet, component contract | `ALGO`, `API`, `PARAMS`, `SAFTY` |
| **H2** | SRD, Feature Spec, or Runbook | Data contract, Test Plan | `FEAT`, `RUNBOOK`, `ENTITY`, `GUARD` |
| **H3** | SDD for the module or integration | API/Event Contract, Integration Plan | `MOD`, `FLOW`, `API`, `PROTOCOL`, `AUDIT` |
| **H4** | SDD, ADR, Access Model, Architecture Standard, PRD, Vision, Roadmap, Operating Model, or cross-system recovery brief | Threat Model, Migration Plan, Governance Model, coupling report, impact matrix | `FRAMEWORK`, `STACK`, `GUARD`, `MCP`, `CONCEPT`, `AUDIT` |

## 6. Docs-to-Code Gate

For C-2 and C-3 work, code generation, task generation, and agent assignment must reference an approved human-readable artifact.

Allowed source artifacts:

- PRD
- SRD
- SDD
- LLD
- API Contract
- Event Contract
- MCP Contract
- Runbook
- Test Plan

Required traceability:

```text
source document
-> requirement or section
-> task
-> agent assignment
-> artifact
-> review
-> test evidence
```

## 7. Diagram-to-Doc Gate

Diagrams are valid architecture inputs, but must be converted into reviewed documentation before implementation.

Supported inputs include:

- C4 context, container, and component diagrams
- sequence diagrams
- flow diagrams
- ERD or data-model diagrams
- site maps
- dependency graphs
- agent workflow diagrams

Required flow:

```text
diagram -> draft doc -> human review -> approved doc -> docs to code
```

## 8. Canonical Source Rule

Human-readable SWE documents are canonical for their governed subject. Derived atoms support retrieval, graph linking, compaction, and visualization.

If a derived atom conflicts with its canonical source document, the canonical source wins until the owner approves a new revision.

A mirror is not a second authority. A mirror distributes an exact governed payload and must identify its canonical source.

## 9. Naming Rule

Use `Test Plan` for testing strategy. Use `SDD` or `LLD` for design. Do not use `TDD` to mean Technical Design Document because it conflicts with Test-Driven Development.

Recommended terms:

```text
PRD = Product Requirements Document
SRD = Software Requirements Document
SDD = Software/System Design Document
LLD = Low-Level Design
TRD = Technical Requirements Document
Test Plan = Testing and verification strategy
```

## 10. Verification Requirements

| Complexity | Required Verification |
| --- | --- |
| **C-0** | Basic validation |
| **C-1** | Basic test and manual check |
| **C-2** | Tests, spec review, and lead approval |
| **C-3** | Tests, documentation review, diagram review, impact analysis, and owner approval |

W-Scale checks are additionally required when work changes graph structure, decomposition breadth, routing topology, or roadmap branching behavior.

Authority and mirror checks are additionally required when a governed standard is copied across repositories.

## 11. Required Output Format

Every non-trivial task response should include:

```markdown
**Complexity:** C-X
**Access Scope:** H-Y
**W-Scale:** W2 / W3 / W4 or N/A
**Risk:** LOW / MEDIUM / HIGH
**Required Artifacts:** ...
**Plan:** ...
**Verification:** ...
```

Access Scope may be omitted only when it equals the declared Complexity default and the omission cannot create ambiguity.

## 12. Versioning

- `MAJOR` changes incompatible obligations or authority boundaries.
- `MINOR` adds enforceable rules, fields, gates, or verification duties.
- `PATCH` clarifies wording without changing obligations.

## 13. Changelog

| Version | Date | Summary |
| --- | --- | --- |
| **3.0.0** | 2026-09-20 | Migrated to Private-Runtime-Platform. Removed external repo references and mirror distribution contract. |
| **2.3.0** | 2026-07-10 | Redefined H as Access Scope H0-H4; abolished H5/H6; separated retrieval radius and W fan-out; required approval for H4. |
| **2.2.0** | 2026-06-12 | Expanded execution governance, artifact requirements, and W-Scale controls. |
| **2.1.0** | 2026-06-12 | Added human-first artifacts, Docs-to-Code, Diagram-to-Doc, and canonical-source rules. |
| **2.0.0** | 2026-06-07 | Added C-0 and complexity-to-access mapping. |
| **1.0.0** | Previous | Initial complexity governance model. |
