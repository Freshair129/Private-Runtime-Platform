---
document_id: ADR-PRP
title: "Architecture Decisions | Proposed PRP Baseline"
product: PRP - Private Runtime Platform
version: 0.4.0-draft
status: draft-for-review
created_at: 2026-09-20
language: th-TH
source_authority: authored-proposal
implementation_status: NOT_IMPLEMENTED_IN_THIS_DELIVERY
runtime_verification: NOT_RUN
repository_integration: NOT_PERFORMED
---

# Architecture Decisions | Proposed PRP Baseline

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [Architecture](ARCH-PRP.md) · [Roadmap](ROADMAP-PRP.md)

## ADR-PRP-001 — Independent platform ownership
Status: PROPOSED implementation decision; name and independent direction were selected in conversation. Context: historical SRS tied identity/admission to Zuri. Decision: PRP owns identities/quotas/resource leases/inference jobs; apps own conversation/tools/channel delivery. No import, database foreign key, bootstrap or release dependency on Zuri.
Alternatives: Zuri module (simpler reuse, unacceptable mandatory product dependency); generic third-party proxy alone (does not cover shared custom speech resources). Consequence: PRP needs its own control state and migration mapping; reuse code only behind neutral adapters. Verification: FR-001/002/053/054 and D01/D03/D26.

## ADR-PRP-002 — One physical admission authority, Router is not engine
Status: PROPOSED. Decision: Router filters/ranks; Admission atomically reserves quota/queue/physical budgets; dispatcher sends only reserved attempts. Engine retains local batching. Resident model budget separate from invocation lease. No hedging or KV migration in P1.
Alternatives: direct round-robin, independent app schedulers, free-VRAM-only selection. Rejected because they cannot account for shared resources/failure ambiguity. Consequence: central state availability matters; fail closed during DB/observer failure. Verification: FR-013/016..022/044.

## ADR-PRP-003 — Atomic speech services, client owns voice turn
Status: PROPOSED. Decision: PRP exposes ASR and preset TTS as independent sync/native-async operations. Client app/reference UI owns ASR->chat->TTS and text fallback. No business voice-turn job kind or generic DAG in P1.
Alternatives: Zuri agent in pool; central ASR/LLM/TTS orchestrator. Deferred to avoid business ownership/agent lock-in. Consequence: reference client demonstrates workflow and preserves answer before TTS; job IDs connect stages without shared business DB. Verification: FR-028/031..038/049/055.

## ADR-PRP-004 — Modular control plane and replaceable implementations
Status: OPEN_FOR_G0_SELECTION (revised in v0.3.0). Direction: Python-first is fixed for this documentation revision via ADR-PRP-009; framework/product selection is not fixed. Compare A Xinference-managed runtimes with B independent vLLM/speech services; C Ray Serve only when its trigger is documented. LiteLLM may implement gateway/keys/routing, not an obligatory additional scheduler.

Selection input: WP24 fit-gap, conformance spikes, current feature-tier/license evidence, key storage/reveal semantics, worker binding, retry/cancel/restart evidence, operator cost, export/exit. No candidate passes on README claims alone. Use supported extension/config interfaces before custom services; BUILD-GAP needs a named requirement and approved owner.

One client-key authority and one physical admission contract; vendor runtime/key state is not duplicated in a competing PRP store. Client key verifier-only constraint FR-005 remains: documented Xinference recoverable/reveal-able keys are a gap for direct client-key delegation [SRC-10].

Consequence: extra G0 evaluation work, but lower risk of implementing already-solved infrastructure. Existing FRs remain normative; framework selection cannot waive resource fencing or privacy. Verification: FR-005/017/018/042/043/050/053 and NFR-019..024. Decision receipt must name selected build/profile and unresolved blockers before production.

## ADR-PRP-005 — Unknown execution is a first-class state
Status: PROPOSED. Decision: user outcome, execution and capacity dimensions separate. Timeout/cancel/lease expiry never prove compute stopped. Unknown attempt quarantines resource until evidence/supervisor recovery; late result cannot reopen terminal outcome/deleted content.
Consequence: temporary lower availability rather than hidden oversubscription. No automatic retry after ambiguous send. Verification: FR-020/021/022/038/041 and D12/D13/D22.

## ADR-PRP-006 — Clip voice and calibrated two-node deployment
Status: PROPOSED. Decision: two full-model chat replicas, speech CPU trial or measured GPU resident headroom, no silent LLM unload. Voice P1 is record-and-send with approved preset; live calling/cloning/music deferred. If hardware cannot meet targets, revise model/context/placement and expose reduced capacity rather than falsify readiness.
Verification: FR-018/029..035/044 and W1-W4. Release gate: exact models/rights/profile approved before G2/G3.

## ADR-PRP-007 — Explicit content retention and bearer-link boundary
Status: PROPOSED. Decision: authenticated artifact access default; native delivery grant is optional, explicitly permissioned, revocable and time-bound. Async durable payload encrypted with finite TTL; sync text no persistent memory by default. Erasure ledger applies before restore read.
Consequence: some LINE use cases must use authenticated app playback instead of native audio attachment; third-party downloaded copies cannot be erased by PRP. Verification: FR-028/039..041 and SEC-008/009.

## ADR-PRP-008 — P2 additive media, not implicit Phase 1 expansion
Status: PROPOSED. Decision: P2 image/video use same identity/admission/job/artifact primitives but new grants, metering units and qualified profiles. No arbitrary workflow/plugin installs, no unapproved chat preemption. Realtime speech, cloud fallback and hostile multi-tenancy require separate decisions.
Verification: FR-056/P2-001..008 and P1 regression. P2 envelope has no approved throughput/resolution/duration promises.

## ADR-PRP-009 — Python-first, no mandatory desktop backend
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION by the user request to revise; runtime NOT_RUN. PRP-owned control/API/policy/adapters use Python. FastAPI/Pydantic are first evaluation choices for the thin API, not a mandate to wrap every vendor API with redundant endpoints [SRC-13]. React/TypeScript clients remain independent. Rust/Tauri screenshot standards do not govern PRP backend.

Native dependency kernels are allowed. A first-party Rust/C++ module needs evidence of a measured bottleneck or unavoidable integration boundary plus an ADR; a general claim that Python is slow is insufficient. Verification: NFR-019/021/022 and coding standards. Consequence: separate model processes/environments are mandatory; no single giant Python environment.

## ADR-PRP-010 — Reuse evidence before custom infrastructure
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION; candidate selection OPEN. Requirements describe outcomes; logical module ownership does not require first-party code. Evaluate existing runtime manager, gateway, scheduler and process-supervisor capabilities before building equivalents.

A/B are alternative evaluated compositions, not cumulative dependencies. Candidate C Ray Serve is conditional. Fit-gap rows retain source evidence separate from runtime evidence and track REUSE/CONFIGURE/ADAPT/BUILD-GAP/DEFER. A critical gap blocks G0 exit or produces a reviewed narrower design; never redefine security to declare a candidate passed. Verification: NFR-020/023/024; WP24.

## ADR-PRP-011 — Thin API and isolated model lifecycles
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION; exact environment pins pending WP25. API processes must not load models or initialize GPU drivers through import side effects. Dedicated runtime/worker services own weights, batching and termination. Package/image locks are isolated for control, LLM and speech when dependency requirements differ.

Automatic cross-engine retries/relocation must respect current admission and execution fences. Standard serving frameworks may implement lifecycle, but actual resource mapping must be observable; no unexplained second scheduler. Client timeout is not native compute cancellation. Verification: NFR-021..024, existing FR-020/021/044, D32/D33/D34.

<a id="ADR-PRP-012"></a>

## ADR-PRP-012 — Monorepo layout: living documentation, contracts and Python-first code in one repository

**Status:** ACCEPTED — approved by the repository owner on 2026-09-20 with all six §12 recommendations of SDD-PRP-REPO taken as proposed; migration M1 in progress, no application code generated
**Date:** 2026-09-20
**Deciders:** Repository owner (C-3 grantor per STD-Execution-Governance §3)
**Related:** ADR-PRP-009 / 010 / 011 · ARCH-PRP §2, §13, §14 · D30, D32 · Coding-Standards §2, §3, §7, §10 · STD-Execution-Governance §4–§9 · PRP-NFR-019..024 · WP03 / WP04 / WP24 / WP25
**Companion design:** [SDD-PRP-REPO](SDD-PRP-REPO.md) (full tree, module boundaries, migration plan)

### Context

The repository today contains one frozen documentation package (`PRP-Documentation-v0.3.0/`, checksummed and QA-reviewed) plus `AGENTS.md` and `CLAUDE.md`. There is no code. The next work packages (WP24 fit-gap, WP25 Python baseline, WP04 control plane) need a place for code to live, and the governance already fixes several forces:

- **DDD SSOT / Docs-to-Code gate.** Documents are canonical, code is derived; C-2/C-3 code must reference an approved PRD / SRD / SDD / LLD / API contract / Runbook / Test Plan. Git-Standards require spec or RCA documents committed alongside code, one task per PR.
- **Coding-Standards.** `src/` layout; framework-specific objects only in adapters; separate lock and image boundaries for control, LLM and speech; no torch / CUDA / weights import in the control path; CI gates (Ruff, mypy strict, pytest, no-ML-import test).
- **Existing package direction.** ARCH-PRP §14 and diagram D30 already name `apps/control-api/src/prp/`, `workers/voice/`, `apps/console`, `apps/playground` and a contracts location. D30 labels it `packages/contracts`, ARCH §14 says `contracts/`; this ADR reconciles the two.
- **Framework selection is OPEN** (ADR-PRP-004). The layout must hold the A (Xinference-managed) / B (independent vLLM + speech) seams without choosing either.
- **W-Scale.** Sibling fan-out of 3–5 is optimal, 6–8 requires lead review, 9+ blocks.
- **Package immutability.** v0.3.0 was delivered as a package with `MANIFEST.sha256`; editing it in place invalidates the manifest and the QA report. Day-to-day documentation iteration must not require re-packaging.

Non-goals: selecting a framework, changing any requirement text, generating application code, qualifying any runtime.

### Decision

Adopt **Option B**: a single monorepo whose root holds a living documentation tree (`docs/`), the protocol source of truth (`contracts/`), Python projects under `apps/` and `workers/` each with its own lock, deployment templates (`deploy/`), repository tooling (`tools/`) and governance working memory (`.brain/`). Frozen documentation packages are archived unchanged under `docs/releases/`. The full tree and rules are in SDD-PRP-REPO.

Bundled secondary decisions:

1. **Per-project locks, no uv workspace.** A uv workspace shares one lockfile, which contradicts Coding-Standards §7 and NFR-022 (isolated control / LLM / speech environments). Each Python project owns `pyproject.toml`, `uv.lock` and `.python-version`. The repository root has no Python project.
2. **Ports-and-adapters with bounded contexts.** `src/prp/core/` holds six contexts that map 1:1 to the ARCH-PRP §2 ownership table; `src/prp/adapters/` is the only place vendor SDK, ORM and HTTP-client imports are allowed; the A/B seam is `adapters/runtimes/` and `adapters/gateway/`.
3. **Contracts: YAML canonical, JSON generated.** Today JSON and YAML are hand-kept twins. Going forward the YAML is authored and the JSON is produced by a tool and checked for equality in CI. The three contract boundaries named in API-PRP (client subset §3–§6, worker §7, management §8) become three files.
4. **ADR-PRP-012 onward append to `docs/ADR-PRP.md`** as new sections, keeping the existing single-file convention (surgical change; no migration of 001–011).
5. **Derived registries become generated.** `registry/requirements.json` and `roadmap.json` are already marked `derived: true`; a tool generates them from the SRS / Roadmap Markdown, and the existing validator is extended to cross-check code traceability markers.

### Options Considered

#### Option A: Two repositories (documentation package repo + code repo)

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low to start, High to keep in sync |
| Cost | Two CI pipelines; cross-repo links; manual version pinning of docs in code |
| Scalability | Adding apps / workers is easy; keeping requirement → test traceability is not |
| Team familiarity | Common pattern, but the Docs-to-Code tooling cannot see both sides |

**Pros:** frozen packages stay pristine; code repo is small.
**Cons:** breaks the Git-Standards rule that spec / RCA ship in the same PR as code; the validator cannot check `PRP-AT-nnn` markers in tests; the DDD "symbolic link doc ↔ code" rule becomes an external convention nobody enforces.

#### Option B: Monorepo with a living docs tree and archived releases (recommended)

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium (one-time migration of the package into `docs/` + `docs/releases/`) |
| Cost | One CI with path-filtered jobs; one validator covering docs + contracts + trace |
| Scalability | New apps / workers / contract files slot into existing roots; W-Scale stays W2–W3 |
| Team familiarity | Matches ARCH §14 / D30 direction already reviewed |

**Pros:** spec and code in one PR; validator and trace tool see everything; release packages remain immutable snapshots with their own manifest; single clone for Claude Code / agents.
**Cons:** the 150 package files exist twice (living copy + frozen snapshot) after migration; repository root sits at W3 (six visible directories); validator paths must be updated once.

#### Option C: Monorepo where docs stay as versioned packages beside code

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low migration, High friction |
| Cost | Every documentation edit becomes a package version bump with new manifest, HTML, DOCX |
| Scalability | Poor; the `vX.Y.Z` folder name is embedded in links and tooling |
| Team familiarity | Familiar from the current delivery, but designed for hand-off, not iteration |

**Pros:** nothing moves.
**Cons:** kills daily iteration; two copies of "current" truth appear as soon as anyone edits without bumping; contracts and tools are trapped inside a versioned folder that code must reference by version string.

### Trade-off Analysis

- **Immutability vs iteration.** B separates the two concerns by location (`docs/` iterates, `docs/releases/` is frozen) instead of by discipline (C) or by repository (A). The duplication cost of B is bytes; the cost of A and C is process failure modes.
- **Traceability.** Only B lets one tool walk SRS anchors → registry → acceptance IDs → pytest markers → evidence receipts. This is the concrete mechanism behind the DDD claim "code reflects spec 100%".
- **Framework openness.** The `core/` vs `adapters/` split (decision 2) is what keeps ADR-004 open in code form: A and B differ only in `adapters/runtimes/*`, `adapters/gateway/*` and `deploy/`, never in `core/` or `contracts/`.
- **W-Scale.** Root: `docs`, `contracts`, `apps`, `workers`, `deploy`, `tools` = 6 (W3, lower bound). `deploy/` could fold into `apps/*/deploy` and `workers/*/deploy` to reach W2, but that fragments the two-host topology that spans both. Recommendation: keep `deploy/` and record the W3 review here. `core/` = 6 contexts (W3) is accepted because it mirrors the ARCH §2 table exactly; merging contexts would hide an ownership boundary the SRS names.
- **Lock isolation vs convenience.** A uv workspace would be nicer for developers but is exactly the "single giant Python environment" ADR-011 forbids.

### Consequences

- **Easier:** one `git clone`; one PR carries spec + code + RCA; agents (Claude Code, Codex) get one `AGENTS.md` / `CLAUDE.md` scope; release packaging becomes "snapshot `docs/` + rebuild views + write manifest".
- **Harder:** `tools/docs/validate_docs.py` needs its root and hard-coded paths updated; contributors must learn which copy is live (`docs/`) and which is frozen (`docs/releases/`); the release folder is never edited, only added to.
- **Revisit when:** a second worker kind (P2 image / video) arrives → `workers/<kind>/`; console and playground share a generated TypeScript client → introduce `packages/`; `core/` needs a seventh context or `apps/` a fourth app → re-run W-Scale review; a control-plane context needs its own process for measured reasons → separate service with its own ADR (ARCH §2 explicitly does not mandate microservices).

### Verification

- Structural: `python tools/docs/validate_docs.py` returns `errors: []` after migration; `sha256sum -c MANIFEST.sha256` still passes inside `docs/releases/PRP-Documentation-v0.3.0/`.
- Governance: every migration PR carries the §11 header, one task per PR, DoD checklist.
- Traceability: PRP-NFR-019..024 remain the acceptance targets for the Python layout; none is claimed PASS by this ADR.

### Action Items

Each item is its own PR and its own approval gate. Nothing below starts before this ADR is approved.

1. [x] **M1 — Documentation tree (C-2 / H2)** — done 2026-09-20, see CHANGELOG-PRP.md "Unreleased". Create root layout; `git mv` the v0.3.0 package to `docs/releases/`; copy the living documents, standards, diagrams, registry into `docs/`; promote `contracts/` and `tools/` to root; update validator paths, `AGENTS.md` standards link, `CLAUDE.md`; decide the fate of `github-setting/`; add `.github/workflows/docs.yml`.
2. [x] **M2 — Contracts (C-2 / H2)** — done 2026-09-20 (worker and management drafts, export tool, schema, CI), see CHANGELOG-PRP.md "Unreleased". Split OpenAPI into `prp-client.yaml` / `prp-worker.yaml` / `prp-management.yaml` (the latter two as drafts for WP03); add JSON export tool and equality check; JSON Schema for job payloads and runtime manifests.
3. [x] **M3 — Python skeletons (C-3 / H4 for dependency resolution, = WP25)** — done 2026-09-20 with owner decisions (Python 3.12, FastAPI/Pydantic candidate, adapters deferred), see CHANGELOG-PRP.md "Unreleased". `apps/control-api` and `workers/voice` with pyproject, lock, `platform/`, `core/*` ports and domain types, `api/` bound to the client contract, entrypoint stubs, the no-ML-import and conformance tests, CI jobs. No adapters yet.
4. [ ] **M4 — Adapters and deploy (after WP24 → WP03 → WP04).** Implement adapters according to fit-gap dispositions; `deploy/` host templates with pinned image digests (TEMPLATE / NOT_QUALIFIED).
5. [x] **Trace tooling** — done 2026-09-20 (`tools/trace/collect_trace.py`, validator status gate, `docs/evidence/`), see CHANGELOG-PRP.md "Unreleased". `tools/trace/collect_trace.py` and the validator extension: an acceptance case may leave `NOT_RUN` only with a collected test *and* an evidence receipt.

<a id="ADR-PRP-013"></a>

## ADR-PRP-013 — Contract models: generated from the OpenAPI YAML, never hand-written

**Status:** ACCEPTED — approved by the repository owner on 2026-09-20 as proposed, including the three recommendations in "Open questions" (keep descriptions, frozen models, generate the DRAFT management contract now); action item 1 starts immediately, items 2-5 at M4 kickoff
**Date:** 2026-09-20
**Deciders:** Repository owner
**Related:** ADR-PRP-012 decision 3 (YAML canonical, JSON generated) · SDD-PRP-REPO §5, §6.3, §9 · API-PRP §1, §10 · Coding-Standards §3 · ARCH-PRP §14 · PRP-NFR-024 · CHANGELOG "M3" deferred item

### Context

M3 bound every client operation to `contracts/openapi/prp-client.yaml` by route inventory only; request and response bodies are not yet typed. M2 fixed the contract authority rule: the YAML is canonical and every `.json` beside it is generated and checked in CI. The voice worker already carries 110 lines of hand-written Pydantic models (`prp_voice.contract.models`) that duplicate `prp-worker.yaml` by hand, which is exactly the drift the M2 rule was written to prevent.

Forces the models must satisfy, all already documented:

- **Reject, do not drop.** Unsupported fields are rejected rather than silently dropped (API-PRP §1); field/extra handling must match the contract and there must be no silent coercion that changes quota or identity (Coding-Standards §3).
- **Typed public boundary.** Public functions, adapters and message envelopes carry type hints; `mypy --strict` gates every project (Coding-Standards §3, §10).
- **UTC-aware timestamps** in anything persisted (Coding-Standards §3).
- **Per-boundary models, never cross-referenced.** Each contract copies shared shapes such as `Error` on purpose because the client, worker and management boundaries have different trust (ADR-PRP-012 decision 3, contracts/README).
- **Portable binding.** The public contract must not embed vendor model IDs or manager schemas (PRP-NFR-024); models come from PRP's own YAML, not from a vendor SDK.
- **Scale.** Three contracts with 21 + 22 + 16 component schemas today; the management contract keeps growing until the WP03 freeze.

Non-goals: choosing the API framework (FastAPI remains the candidate per ADR-PRP-009), changing any wire format, or promoting any acceptance status.

### Decision

Adopt **Option B, generated models**: every contract's Python models are generated from its YAML by a pinned `datamodel-code-generator`, committed as derived files, regenerated and diffed in CI exactly like the JSON exports. Hand-written contract models are forbidden except through the narrow escape hatch in rule 6. Core domain types (`core/*/model.py` dataclasses) are unaffected; `api/` maps between contract models and core types as before.

Rules:

1. **Tool and pin.** `datamodel-code-generator` is pinned in `tools/contracts/requirements.txt` (spike used 0.82.0 against Pydantic 2.13.5, the version locked in `apps/control-api`). It is dev tooling only; generated files import nothing but Pydantic and the standard library.
2. **Generator wrapper.** `tools/contracts/gen_models.py` holds a fixed table of (contract YAML → project → output module → base class) and the exact generator flags, runs the generator, then `ruff check --fix` (import order) and `ruff format` on the output, and supports `--check` (regenerate to memory, fail on any diff). `.github/workflows/contracts.yml` runs `--check`.
3. **Flags fixed by this ADR.** `--output-model-type pydantic_v2.BaseModel --target-python-version 3.12 --use-annotated --field-constraints --strict-nullable --strict-types int float bool --use-union-operator --use-standard-collections --enum-field-as-literal all --use-double-quotes --disable-timestamp --collapse-root-models --base-class <project>.contract.base.ContractModel`. Descriptions stay in the output; generated modules get a per-file `E501` ignore in `pyproject.toml`.
4. **Hand-written base class per project.** `ContractModel(BaseModel)` with `model_config = ConfigDict(extra="forbid", frozen=True)`. Numeric and boolean strictness comes from `--strict-types` (StrictInt / StrictFloat / StrictBool) rather than a global `strict=True`, because global strict mode also rejects string inputs for `UUID` and `date-time` fields in Python-mode validation, which is the path FastAPI uses after parsing a JSON body. This is a known Pydantic behaviour, not yet exercised through FastAPI in the spike; M4 adds a test for it (action 4).
5. **Placement.** Control plane: `src/prp/api/contract/client_v1.py` (server side of the client contract) and `src/prp/adapters/runtimes/worker_v1.py` (client side of the worker contract, owned by the runtimes adapter); `src/prp/api/contract/management_v1.py` when the console work starts. Voice worker: `src/prp_voice/contract/generated.py` replaces the hand-written models, with `models.py` reduced to a re-export so M3 imports and tests keep working. Generated code is never imported across projects (ARCH-PRP §14).
6. **Escape hatch.** A shape the generator cannot express may be hand-written in `<contract>/_manual.py` only together with a test that compares the model's `model_json_schema()` to the OpenAPI component after normalization (drop `title`, `description`, `$defs` names; compare `type`, `properties` keys, `required`, `enum`, `const`, bounds). No such shape exists in the three contracts today.
7. **Contract hygiene first.** Before generation, every inline object schema in the three YAMLs is promoted to a named component so that no generator-invented name (`Error1`, `Result`, `Choice`, `Function1`, `ToolChoice`, `Delta`, `Detail`, `Cancellation`, `Scope`, `TestId`, `Limits`) reaches source code. Proposed names: `ErrorBody`, `TtsJobResult`, `ChatChoice`, `FunctionCall`, `ToolFunction`, `NamedToolChoice`, `ChatDelta`, `EvidenceDetail`, `CancellationSupport`, `PolicyScope`, `AcceptanceTestId`, `CapabilityLimits`. This changes component counts (client 21 → about 26) but not a single wire byte; the operation inventory 12 paths / 14 operations stays as the validator requires, and the change is recorded in CHANGELOG as a naming-only revision.
8. **FastAPI binding.** Routes take the generated models as body and response types. The M3 inventory test stays; a new conformance test compares each operation's request-body and success-response schema in `app.openapi()` with the contract after the same normalization as rule 6.

### Options Considered

#### Option A: Hand-written Pydantic models plus a schema-conformance test

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium code, High test complexity (normalizing two JSON-Schema dialects) |
| Cost | About 59 models now, every contract edit made twice; conformance test is the only drift guard and it is brittle |
| Scalability | Linear human effort per schema; management contract still growing |
| Team familiarity | Highest readability; idiomatic Pydantic; no extra tool |

**Pros:** full control over names, docstrings and validators; nothing to install.
**Cons:** duplicates the canonical YAML by hand, which the M2 rule forbids for JSON and should forbid here for the same reason; the drift guard depends on a normalization layer that the spike shows is non-trivial (`anyOf` vs `type: [x, null]`, `$defs`, titles).

#### Option B: Generated models from the YAML, committed and CI-checked (recommended)

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low code (one wrapper tool, one base class per project), Medium one-off contract cleanup |
| Cost | One pinned dev tool in `tools/contracts`; regenerate on every YAML change; zero hand maintenance of models |
| Scalability | Constant effort per schema; management growth is free |
| Team familiarity | Same pattern as `export_json.py`; generated code is plain Pydantic, readable if verbose |

**Pros:** drift is impossible by construction; `extra="forbid"`, `Literal` enums, discriminated unions and `AwareDatetime` come out of the box; passes `mypy --strict` unchanged.
**Cons:** verbose output (about 4x the hand-written line count, mostly descriptions); generator names inline schemas itself, so the YAML must name them (rule 7); default generation coerces `"64"` to an int, so strictness must be configured (rule 3, 4); one more pinned tool to upgrade deliberately.

#### Option C: Build models at import time from the OpenAPI document

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low to write, High to reason about |
| Cost | Runtime dependency on the YAML loader; opaque types |
| Scalability | Fine mechanically |
| Team familiarity | Poor: no static types, `mypy --strict` cannot see fields |

**Rejected:** violates the typed-boundary rule (Coding-Standards §3) and makes the API's OpenAPI output depend on runtime parsing.

### Spike evidence (dev tooling only, 2026-09-20)

Run in an isolated scratch virtualenv, never inside the repository; it qualifies nothing at runtime and changes no acceptance status.

| Check | Default flags | Flags of rule 3 |
|---|---|---|
| `mypy --strict` on generated client / worker / management | pass / pass / pass | pass / pass (with base class) |
| `ruff check` (E, F, I, B, UP, SIM, N) | client clean; worker 12 × E501; management 5 × E501 | worker 10 × E501 + 1 × I001; client 1 × I001 (both fixable by the post-step) |
| `additionalProperties: false` → `extra="forbid"` | yes, all 28 client classes | yes |
| `JobRequest` discriminated union (`kind`) | `RootModel` with `Field(discriminator="kind")`; examples validate; `kind: video` rejected | same |
| `type: [string, 'null']` → `str \| None`, `format: date-time` → `AwareDatetime` | yes; naive `2026-09-20T12:00:00` rejected | same |
| Unknown field `shell` on a job request | rejected (`extra_forbidden`) | rejected |
| `max_tokens: "64"` (string) | **accepted** (lax coercion) | rejected (`int_type`); `ge=1` still enforced |
| `cancellation_requested: "false"` | not tested | rejected |
| Frozen instances | no | yes (`frozen=True` from base class) |
| Generator-invented class names | client 8, worker 10, management 3 | unchanged (must be fixed in YAML, rule 7) |
| Output size | client 296 / worker 459 / management 275 lines | client 307 / worker 449 lines; hand-written worker models are 110 lines but omit descriptions and six models |

Reproduction: `datamodel-codegen --input contracts/openapi/prp-<c>.yaml --input-file-type openapi` plus the flags in rule 3; validation smoke with `model_validate` on `contracts/examples/job-*.example.json`.

#### Comparison example — `Readiness` from `prp-worker.yaml`

Hand-written today (`prp_voice/contract/models.py`):

```python
class Readiness(StrictModel):
    state: ReadinessValue
    profile_epoch: int = Field(ge=0)
    observed_at: datetime
    limits: Limits | None = None
```

Generated with the flags of rule 3:

```python
class Readiness(ContractModel):
    state: Annotated[
        Literal["READY", "NOT_READY", "UNKNOWN"],
        Field(description="NOT_READY covers loading/draining ..."),
    ]
    profile_epoch: Annotated[StrictInt, Field(description="Actual epoch of the runtime", ge=0)]
    observed_at: AwareDatetime
    limits: Limits | None = None
```

Differences that matter: the generated version rejects a naive `observed_at` and a string `profile_epoch`, carries the contract's own description, and cannot drift from the YAML; the hand-written version is shorter and happens to be correct today only because it was copied from the YAML by hand.

### Trade-off Analysis

- **Drift vs readability.** B trades verbose files for a structural guarantee. The repository already accepted this trade for JSON exports, registry files and `code-trace.json`; models are the same kind of derived artifact.
- **Strictness.** Both options need the same care about coercion; B makes it a generator flag plus a five-line base class, A makes it a convention every author must remember.
- **Naming.** B forces the YAML to name every object, which improves the contract for every other consumer (TypeScript clients, docs) rather than being a cost specific to Python.
- **Escape hatch.** Keeping rule 6 means Option A's machinery still exists, but only for exceptions with a test attached, so the default path stays drift-free.

### Consequences

- **Easier:** contract changes are one YAML edit plus regeneration; reviewers diff the YAML, not 59 models; the voice worker loses its hand-copied models.
- **Harder:** one more pinned dev tool and a `--check` step; generated files must never be edited by hand (header marker plus CI diff); descriptions make files long.
- **Revisit when:** the generator cannot express a contract construct (use rule 6, then reconsider); a TypeScript client needs models (generate them from the same YAML, do not share Python); the management contract freezes at WP03 (regenerate, no design change).

### Verification

- Generated modules pass `ruff check`, `ruff format --check`, `mypy --strict` and `lint-imports` in each project; `gen_models.py --check` and `export_json.py --check` pass in `contracts.yml`.
- Contract tests: examples validate; unknown fields, string numbers and naive datetimes are rejected; FastAPI body and response schemas conform after normalization (rule 8).
- Validator: client inventory 12 / 14 unchanged after the component-naming pass; all acceptance cases remain NOT_RUN.

### Action Items (all at M4 kickoff, one PR each)

1. [x] **Contract naming pass (C-2 / H2)** — done 2026-09-20: client 21→29, worker 22→32, management 16→19 components; wire equivalence proven by dereferenced comparison; see CHANGELOG-PRP.md "Unreleased". Promote inline schemas to named components in all three YAMLs (rule 7); regenerate JSON; CHANGELOG entry; validator green.
2. [x] **Generator wrapper (C-2 / H2)** — done 2026-09-20. Placement refined against rule 5: the control plane keeps all generated modules in one package `prp.contracts` (a layer below `api | adapters`, above `core`) because rule 4 wants one base class per project and the layer rule forbids `api` and `adapters` from importing each other; import-linter enforces that `prp.contracts` imports Pydantic only. See CHANGELOG-PRP.md "Unreleased". `tools/contracts/gen_models.py`, pin in `tools/contracts/requirements.txt`, `--check` step in `contracts.yml`, per-file `E501` ignore for generated modules.
3. [x] **Generate and wire (C-2 / H2)** — done 2026-09-20: generated modules in `prp.contracts` and `prp_voice.contract.generated`; `prp_voice.contract.models` is now a re-export with drift-tested Literal aliases; M3 tests green. `ContractModel` base per project; generated client and worker modules in `apps/control-api`, generated worker module in `workers/voice` replacing the hand-written models; M3 tests unchanged and green.
4. [x] **FastAPI binding and conformance (C-2 / H2)** — done 2026-09-20 for every JSON operation (14 client, 5 worker): bodies, parameters and success responses bound to generated models; normalized schema-conformance tests and strictness tests added. Exception recorded in the test: the two multipart operations (`transcribeAudio`, `uploadArtifact`) are bound together with the upload path at M4. Contract adjustment: URL fields use `pattern: ^https://` instead of `format: uri` because Pydantic AnyUrl cannot carry a pattern. Body/response types on the 14 client routes and 5 worker routes; schema conformance test; explicit test that JSON string inputs for `UUID` and `date-time` fields are accepted while string numbers and booleans are rejected.
5. [x] **Docs (C-1 / H2)** — done 2026-09-20: SDD-PRP-REPO §5 (contract models as derived code, YAML authoring rules), §6.1/§6.3 (`prp.contracts` layer, W-Scale `src/prp` 5 → 6 recorded), §7 (`generated.py` / `base.py` / `models.py`), §9 (generation and conformance in the traceability chain, rule 6), §10 (conformance tier and `contracts.yml` steps); CLAUDE.md commands and contracts/README were updated with items 2–4. SDD-PRP-REPO §5 and §9, CLAUDE.md commands, contracts/README.

### Open questions for the owner

1. Keep field descriptions in generated code (long lines, `E501` ignored) or strip them (`--use-field-description` off) to keep files short. Recommendation: keep; the contract text next to the type is what reviewers read.
2. `frozen=True` on contract models (recommended: yes; contract payloads are values, and mutation of a validated request is never intended).
3. Generate the management contract now while it is DRAFT (recommended: yes, to exercise the pipeline) or wait for the WP03 freeze.
