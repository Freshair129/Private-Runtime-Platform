---
document_id: SOURCES-PRP
title: "Sources | Provenance & Verification Limits"
product: PRP - Private Runtime Platform
version: 0.3.0
status: draft-for-review
created_at: 2026-09-20
language: th-TH
source_authority: authored-proposal
implementation_status: NOT_IMPLEMENTED_IN_THIS_DELIVERY
runtime_verification: NOT_RUN
repository_integration: NOT_PERFORMED
---

# Sources | Provenance & Verification Limits

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

## Evidence policy
Checked date: 2026-09-20. Design requirements/targets are authored proposals, not upstream guarantees. External references support protocol/implementation constraints only. No runtime benchmark, repository mutation, hardware test or live channel test was performed for this package. References to prior repo review are pinned historical input, not an assertion that latest main was re-audited here.

## Source register
| ID | Source / scope | Provenance |
|---|---|---|
| SRC-U01 | Current conversation: PRP name, PRP Router, independent platform, two LAN devices, keys, Chat & Voice first, image/video later | User direction; runtime details not verified |
| SRC-B01 | SRS-Self-Hosted-Inference-Pool-Chat-Voice-v0.1.0.md | Attached historical SRS read in full; ownership revised, not carried over silently |
| SRC-01 | vLLM online/OpenAI-compatible serving | official docs checked; API subset must be tested against pinned release |
| SRC-02 | vLLM security / API key limitations | official docs checked; endpoint authentication alone insufficient |
| SRC-03 | LiteLLM virtual keys and routing | official docs checked; optional implementation candidate |
| SRC-04 | LINE receive messages/webhook | official docs checked; external adapter boundary |
| SRC-05 | LINE Messaging API reference | official Markdown reference checked; reply/audio/content constraints |
| SRC-06 | LINE retry failed API requests | official docs checked; retry-key scope/acceptance semantics |
| SRC-07 | Lalin-AI apps/api/app/{pipelines/asr.py,pipelines/tts.py,main.py,jobs/manager.py} at 512e5c445fb614ada34fee916ed5ea999878aab7 | Prior conversation's source review; reuse candidate, not certified current production backend |
| SRC-08 | VIZINTZOR/F5-TTS-THAI model card | checked; Thai/English and limitations; model/voice licensing still approval gate |

## Primary references
[SRC-01] https://docs.vllm.ai/en/latest/serving/online_serving/ and https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/

[SRC-02] https://docs.vllm.ai/en/latest/usage/security/

[SRC-03] https://docs.litellm.ai/docs/proxy/virtual_keys and https://docs.litellm.ai/docs/routing

[SRC-04] https://developers.line.biz/en/docs/messaging-api/receiving-messages/

[SRC-05] https://developers.line.biz/en/reference/messaging-api/index.html.md

[SRC-06] https://developers.line.biz/en/docs/messaging-api/retrying-api-request/

[SRC-07] https://github.com/Freshair129/Lalin-AI/tree/512e5c445fb614ada34fee916ed5ea999878aab7/apps/api/app

[SRC-08] https://huggingface.co/VIZINTZOR/F5-TTS-THAI

## Limits
No standard-conformance certificate (ISO/IEEE/C4/UML/BPMN/security) is claimed. Diagrams use notation inspired by common engineering views; each has a stated type and legend. No legal advice/brand clearance or blanket commercial license approval is supplied. Actual configuration must use selected immutable runtime/model versions, not dynamic latest links.

## v0.3.0 review additions
Revision direction is from the user's request to revise PRP to Python-first/reuse-before-build. This delivery read the attached v0.2.0 archive; the earlier screenshot-based Coding-Standards.md remains historical input and is not the PRP backend standard.

The following official documentation pages were accessed for this revision on 2026-09-20. References are documentation snapshots, not selected deployment versions. Earlier SRC-04..08 references are retained baseline provenance and were not used to claim a new repository/model audit.

| ID | Source | What it supports / limit |
|---|---|---|
| SRC-09 | Xinference using/cluster/model lifecycle | launch/list/terminate and supervisor/workers; actual bound routing still untested |
| SRC-10 | Xinference authentication system | encrypted/reveal-able API keys and first-admin setup; mismatch with PRP verifier-only client key contract |
| SRC-11 | Ray Serve LLM | serving/replica orchestration candidate, not automatic requirement |
| SRC-12 | Ray Core resources | logical resources are not universal physical limits; fractional GPU is not a VRAM cap |
| SRC-13 | FastAPI features | typed request validation/OpenAPI integration candidate |
| SRC-14 | FastAPI deployment concepts | multiple process memory and independent workers |
| SRC-15 | vLLM multiprocessing | engine/native process behavior and version-sensitive start-method constraints |
| SRC-16 | uv locking/syncing | locked versus frozen semantics, isolated reproducible dependency practice |
| SRC-17 | Ruff official docs | linting/format tooling candidate |

[SRC-09] https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html

[SRC-10] https://inference.readthedocs.io/en/latest/user_guide/auth_system.html

[SRC-11] https://docs.ray.io/en/latest/serve/llm/

[SRC-12] https://docs.ray.io/en/latest/ray-core/scheduling/resources.html

[SRC-13] https://fastapi.tiangolo.com/features/

[SRC-14] https://fastapi.tiangolo.com/deployment/concepts/

[SRC-15] https://docs.vllm.ai/en/latest/design/multiprocessing/

[SRC-16] https://docs.astral.sh/uv/concepts/projects/sync/

[SRC-17] https://docs.astral.sh/ruff/

SRC-02/SRC-03 security/key/routing pages were also revisited. No claims about a particular installed release, runtime benchmark or enterprise-license entitlement are made.
