# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **monorepo for PRP (Private Runtime Platform)**, a proposed self-hosted LLM / ASR / TTS inference platform for two LAN GPU hosts. It holds design documentation, protocol contracts, documentation tooling and two Python skeletons: `apps/control-api` (control plane, package `prp`) and `workers/voice` (speech worker, package `prp_voice`). Both **fail closed by design**: no adapters or engines exist yet, so every authenticated request ends in 503, the voice worker reports NOT_READY, and the dispatcher/observer refuse to start. Adapters, engines and `deploy/` arrive in migration step M4 of `docs/SDD-PRP-REPO.md` §11 after the WP24 fit-gap, behind its own approval gate.

Everything is explicitly draft: every acceptance test is `NOT_RUN`, every work package is `NOT_STARTED`, framework selection is `OPEN_FOR_G0_SELECTION`. The validator enforces this, so never "upgrade" a status, invent a benchmark, or mark anything PASS.

Prose is Thai (`language: th-TH`); identifiers, API names, state names and diagram labels are English. Keep that split when editing.

`AGENTS.md` at the repo root holds the binding working rules (R1–R10: assumptions first, doc-first with approval before code, surgical diffs, RCA before fixes, complexity classification). Read it before doing anything non-trivial. `docs/standards/STD-Execution-Governance.md` §11 defines the header every non-trivial response must carry (Complexity C-0..C-3, Access Scope H0–H4, W-Scale, Risk). RCAs go in `.brain/rca/`; drafts awaiting approval go in `.brain/proposals/` and move into `docs/` once approved.

## Layout and the three kinds of files

| Path | Role | Rule |
|---|---|---|
| `docs/*.md`, `docs/standards/`, `docs/diagrams/`, `docs/registry/` | **Living** documentation, canonical for PRP | edit here, then run the validator |
| `docs/releases/PRP-Documentation-v0.3.0/` | **Frozen** delivered package with `MANIFEST.sha256`, Word/HTML/PDF and its own copy of the tools | never edit; only add new release folders |
| `contracts/openapi/*.yaml`, `contracts/schemas/`, `contracts/examples/` | protocol source of truth | YAML is authored; regenerate the `.json` twins with `tools/contracts/export_json.py` (CI rejects stale ones) |
| `tools/docs/`, `tools/contracts/` | validator, HTML builder, sequence renderer; contract export and example validation | repo tooling only; `tools/contracts` needs `pip install -r tools/contracts/requirements.txt` |
| `docs/registry/*.json`, `docs/*.html` | **Derived** | never hand-edit registry content; HTML is gitignored and built on demand |
| `apps/control-api/` | Python control plane: `platform/` kernel, `core/` six bounded contexts with ports, `api/` bound to the client contract, `entrypoints/` (api, dispatcher, observer) | own `uv.lock`; adding any ML or CUDA package fails `test_no_ml_import` and `lint-imports` |
| `workers/voice/` | Python speech worker: `contract/` models, `engines/` ports, `lifecycle/`, `server/` bound to the worker contract | own `uv.lock`; ML imports allowed only under `engines/` from M4 |

## Commands

```bash
# Structural validation (stdlib only, any cwd, exit 1 on any error). Run after ANY edit under docs/ or contracts/.
python tools/docs/validate_docs.py
```

It skips `docs/releases/`. Its JSON output is what `docs/registry/document-validation.json` holds; refresh that file from the output when counts change.

```bash
# After editing any contracts/openapi/*.yaml: regenerate the JSON exports (needs pip install -r tools/contracts/requirements.txt).
python tools/contracts/export_json.py
```

```bash
# Examples must satisfy the schemas named in contracts/examples/index.json.
python tools/contracts/validate_examples.py
```

Python gates (Coding-Standards §10) run inside `apps/control-api` or `workers/voice`; swap `src/prp` for `src/prp_voice` in the worker. On a Windows cp874 console set `PYTHONUTF8=1` before `lint-imports`.

```bash
uv sync --locked --group dev
```

```bash
uv run --locked ruff check . && uv run --locked ruff format --check . && uv run --locked mypy --strict src/prp && uv run --locked lint-imports && uv run --locked pytest tests/unit tests/contracts -q
```

```bash
# Run one test file or one test.
uv run --locked pytest tests/contracts/test_openapi_conformance.py -q -k inventory
```

```bash
# After adding or re-marking tests: regenerate docs/registry/code-trace.json from the pytest markers of every project (needs both projects synced). --check is what CI runs.
python tools/trace/collect_trace.py
```

```bash
# Rebuild docs/PRP-Documentation.html and docs/PRP-Diagram-Atlas.html (gitignored). Needs markdown-it-py and beautifulsoup4,
# which are not installed in this environment; use a scratch venv rather than the system Python.
python tools/docs/build_html_views.py
```

```bash
# Re-render one Graphviz diagram (Graphviz `dot` is not on PATH here).
dot -Tsvg docs/diagrams/source/D01.dot -o docs/diagrams/svg/D01.svg
dot -Tpng docs/diagrams/source/D01.dot -o docs/diagrams/png/D01.png
```

```bash
# Re-render one sequence diagram into a NEW directory, then copy svg/png/mmd back by hand.
python tools/docs/render_sequence.py docs/diagrams/source/D07.sequence.json --out ../.tmp/seq
```

```bash
# Verify the frozen release (run inside it).
cd docs/releases/PRP-Documentation-v0.3.0 && sha256sum -c MANIFEST.sha256 --quiet
```

CI: `.github/workflows/docs.yml` runs the validator, the manifest check and the HTML build on changes under `docs/`, `contracts/`, `tools/`. `.github/workflows/contracts.yml` runs the export check, example validation and the validator on contract changes.

## How the documentation fits together

The central idea is **one canonical source with derived views, and a validator that pins them together**. Knowing which file is authoritative prevents drift errors.

**Requirement chain (92 P1 requirements: 56 FR + 24 NFR + 12 SEC, plus 8 P2 envelopes).**
`docs/SRS-PRP.md` is the requirement authority. Each requirement has an explicit `<a id="PRP-FR-001"></a>` anchor, a heading and a statement. `docs/registry/requirements.json` is `derived: true`, and the validator requires each registry `statement` to appear **verbatim** in the SRS. Each requirement also needs a one-to-one `<a id="PRP-AT-nnn">` anchor in `docs/TEST-PRP.md` (exactly 92), a row in `docs/TRACEABILITY-PRP.md`, a primary diagram ID present in `docs/diagrams/catalog.json`, and a row in `docs/registry/reuse-fit-gap-template.json` that stays `UNASSESSED` / `NOT_RUN`. That row's derived columns (`title`, `acceptance_test`, `proof`, `phase`, `epic`, `evaluation_experiments` from STACK-EVALUATION §6 gates, `source_review` citing SOURCES-PRP `SRC-nn` IDs) are validated against the registry too, and its result columns must remain `null` until WP24 copies the template into a real run record. Adding or renaming a requirement therefore touches all of those plus the hard-coded counts in `tools/docs/validate_docs.py` and the cardinality label in `docs/diagrams/source/D26.dot` (`AT001-AT092`, `WP01-WP25`).

**Roadmap chain (25 work packages).** `docs/registry/roadmap.json` is checked against `docs/ROADMAP-PRP.md`: every `deliverable` string must appear verbatim, dependencies must be acyclic, WP03 must depend on WP24 and WP04 on WP25, and every status must be `NOT_STARTED`.

**Diagram chain (34 views, D01–D34).** `docs/diagrams/catalog.json` is the index. Each entry points to a Graphviz `.dot`, or for sequence diagrams a `.sequence.json` **plus** an equivalent `.mmd`. `render_sequence.py` consumes the JSON and regenerates the `.mmd`, so edit the JSON and re-render rather than editing Mermaid alone. Every diagram needs both `svg/` (well-formed XML, inlined into the Atlas) and `png/`. No font files may be distributed.

**API contracts.** Three OpenAPI documents live in `contracts/openapi/`: `prp-client.yaml` (public; 12 paths and 14 operations unchanged since v0.2.0), `prp-worker.yaml` and `prp-management.yaml` (both `x-prp-status: DRAFT`, freeze at WP03). YAML is canonical; every `.json` is generated. Every object schema must be a named component, never inline, because Python contract models are generated from these files and component names become class names (ADR-PRP-013); hand-written contract models are forbidden outside the tested escape hatch that ADR describes. The validator checks each export for local `#/` refs, unique operationIds and declared security, and checks the client inventory. `contracts/examples/index.json` maps each example to the schema it must satisfy. Schemas shared across boundaries (Error, Message) are copied per document on purpose, never cross-referenced, because each boundary has a different trust level.

**Document frontmatter.** Every doc under `docs/` opens with YAML frontmatter (`document_id`, `version`, `status`, `implementation_status`, `runtime_verification`) and exactly one `# Title` H1. The HTML builder strips the frontmatter, uses that H1 for navigation, and orders documents by the `ORDER` list in `tools/docs/build_html_views.py`.

**Provenance.** Citations `[SRC-nn]` / `[SRC-Unn]` / `[SRC-Bnn]` resolve to the register in `docs/SOURCES-PRP.md`. Claims about third-party tools must trace to a source row; the Xinference recoverable-key behaviour is recorded as a gap against FR-005, not as compliance.

## How the Python code fits together

- **Layers** (`apps/control-api/src/prp`): `entrypoints` → `api` | `adapters` → `core` → `platform`. `import-linter` enforces it from `pyproject.toml`; `core` and `platform` may not import FastAPI, Pydantic, ORMs or HTTP clients, and nothing may import torch, vLLM, whisper or similar. Wire ports to adapters only in `entrypoints/wiring.py`.
- **Contexts** under `core/` mirror the ARCH §2 ownership table one to one: `access`, `fleet`, `scheduling` (router selects, admission reserves), `execution`, `content`, `observability`. Each exposes frozen dataclasses in `model.py`, `Protocol` ports in `ports.py`, and pure rule functions; cross-context calls go through the owning context's ports.
- **Contract binding**: `api/routes.py` declares every client operation with the contract's `operationId`; `tests/contracts/test_openapi_conformance.py` diffs `app.openapi()` against `contracts/openapi/prp-client.yaml`. The worker does the same against `prp-worker.yaml`. Change the YAML first, then the routes.
- **Test tiers**: `tests/unit` (pure), `tests/contracts` (inventory, envelopes, no-ML import, lock contents), `tests/integration` (real services, M4+), `workers/voice/tests/hardware` (self-hosted only). Mark tests with `@pytest.mark.req("PRP-FR-nnn")`; use `@pytest.mark.at("PRP-AT-nnn")` only when the test is the acceptance procedure itself, and never more than one `at` per test.
- **Status gate**: `tools/trace/collect_trace.py` turns the markers into `docs/registry/code-trace.json` (derived, committed, checked in CI). An acceptance case in `docs/TEST-PRP.md` may leave `NOT_RUN` only when that file lists a collected test for it **and** `docs/evidence/` holds a complete receipt with the same status; a PASS from unit or contract tests alone is rejected unless the requirement's proof is purely contract/packaging/portability. Markers never change a status. See `docs/evidence/README.md`.
- **Settings** are frozen dataclasses reading `PRP_*` / `PRP_VOICE_*` environment variable names; never put values or secrets in source.

## Design decisions that constrain edits

Settled in `docs/ADR-PRP.md` and `docs/ARCH-PRP.md`; proposals that contradict them need a new ADR appended to `ADR-PRP.md` (with an `<a id="ADR-PRP-nnn">` anchor), not a quiet edit.

- PRP is independent: no import, foreign key or bootstrap dependency on Zuri, FUNG or Lalin Studio. Clients own the voice turn (ASR → chat → TTS); PRP exposes atomic ASR/TTS only.
- Python-first for first-party control/API/policy/adapters (ADR-009); Rust/Tauri is not a requirement. API processes never load models or CUDA. Model runtimes live in separate processes and environments.
- Reuse before build (ADR-010): every module box maps to REUSE / CONFIGURE / ADAPT / BUILD-GAP / DEFER with evidence. Candidates A (Xinference-managed) and B (independent vLLM + speech services) are alternatives, not a stack; C (Ray Serve) is conditional.
- Exactly one client-key authority (verifier-only keys) and one physical admission authority. Router selects, Admission reserves, dispatch only sends reserved attempts. Timeout / cancel / lease expiry never prove compute stopped.
- Two GPU hosts are two independent full-model replicas, not HA.
- Repository and code layout (ADR-012, `docs/SDD-PRP-REPO.md`): ports-and-adapters with six bounded contexts under `apps/control-api/src/prp/core/` mirroring the ARCH §2 ownership table; vendor SDK / ORM imports only under `adapters/`; three processes (api, dispatcher, observer) from one codebase; one `pyproject.toml` + `uv.lock` per Python project, no uv workspace; W-Scale 3–5 siblings per node, 6–8 needs recorded review.

## Things that do not govern this repository

- `docs/standards/Definition-of-Done.md`, `Risk-Assessment.md` and `Verification-Standards.md` still reference Rust/Tauri, `cargo`, Vitest and Glassmorphism from an earlier project. `Coding-Standards.md` states those do not govern PRP. Apply the gate structure but map tooling to the Python toolchain in Coding-Standards §10 (uv, Ruff, mypy strict, pytest) once code exists.
- The tools inside `docs/releases/PRP-Documentation-v0.3.0/tools/` use the old package paths; run the root `tools/docs/` copies.
- `tools/docs/build_html_views.py` still prints "v0.3.0" in the page header; fix it at the next version bump.

## Conventions

- Commits follow Conventional Commits with a scope: `domain(scope):`, `feat(scope):`, `fix(scope):`, `docs(scope):`, `refactor(scope):`, `chore(scope):`. Put the task ID (e.g. `PRP-P1S101`) in the body. Branches are `feat/PRP-XXX-description` or `fix/PRP-XXX-description`. One task per PR with the DoD checklist in the description and a `docs/CHANGELOG-PRP.md` entry.
- `core.autocrlf=true` is set and there is no `.gitattributes`, so LF/CRLF warnings on `git diff` are expected noise. Preserve a file's existing line endings when scripting edits.
- Version bumps are register-driven: `docs/CHANGELOG-PRP.md` (an `Unreleased` section collects changes), `docs/QA-REPORT-PRP.md`, frontmatter `version` fields, `info.version` in both OpenAPI files, then a release snapshot under `docs/releases/`.
