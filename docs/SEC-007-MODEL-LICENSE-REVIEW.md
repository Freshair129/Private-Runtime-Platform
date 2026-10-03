---
document_id: SEC-007-MODEL-LICENSE-REVIEW-2026-10-03
title: "SEC-007 license review for the selected Typhoon model"
version: 0.5.0
status: approved
created_at: 2026-10-03
complexity: C-2
risk: HIGH
decision_status: APPROVED
activation_status: BLOCKED
owner_decision: "APPROVED_BY_REPOSITORY_OWNER_ON_2026-10-03; ASSESSMENT_ONLY"
---

# SEC-007 license review for the selected Typhoon model

## 1. Purpose and boundary

Record source-backed provenance for the owner-selected BYOM candidate `typhoon-ai/typhoon2.5-qwen3-4b` at revision `ce0a7416fe82d4404b2b4a253ce3ac095ab1252c`. This owner-approved assessment is **not** the SEC-007 license receipt and not legal certification. It does not change the selected model, authorize download or activation, or attest rights on the owner's behalf.

## 2. Requirement and parent/peer dependencies

- [SRS-PRP.md](SRS-PRP.md#PRP-SEC-007) requires separate provenance for code, weights, vocoder, reference voice, and intended use; a missing license receipt blocks activation.
- [SECURITY-DATA-PRP.md §8](SECURITY-DATA-PRP.md) requires review of code, weights, tokenizer/vocoder, voice assets, and intended use separately. A model-card claim is input evidence, not legal certification.
- [WP24 run 1](evidence/wp24/WP24-2026-09-20-run1.json) records the model choice and says its SEC-007 receipt is still required before activation.
- This candidate is text-only in WP24; voice assets and vocoder are outside this candidate's scope. That does not close the separate WP10 speech/voice rights gate.

## 3. Evidence captured on 2026-10-03

| Item | Observed evidence | Review status |
|---|---|---|
| Selected model | The Hugging Face revision API resolves the selected repository and exact SHA. Its metadata declares `apache-2.0`; the snapshot file list has no `LICENSE` file. [Pinned revision](https://huggingface.co/typhoon-ai/typhoon2.5-qwen3-4b/tree/ce0a7416fe82d4404b2b4a253ce3ac095ab1252c) · [revision metadata API](https://huggingface.co/api/models/typhoon-ai/typhoon2.5-qwen3-4b/revision/ce0a7416fe82d4404b2b4a253ce3ac095ab1252c) | Repository declaration observed; rights not certified |
| Model card license source | The pinned README declares `apache-2.0` and links to the Qwen base model's `main/LICENSE`, a mutable reference rather than a revision pinned by the Typhoon snapshot. [Pinned README](https://huggingface.co/typhoon-ai/typhoon2.5-qwen3-4b/blob/ce0a7416fe82d4404b2b4a253ce3ac095ab1252c/README.md) | Upstream linkage needs owner/legal review |
| Referenced upstream license | At capture time, Qwen repository `main` resolved to `cdbee75f17c01a7cc42f958dc650907174af0554`; its LICENSE content had SHA-256 `832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e` and identifies Apache License 2.0. [Captured immutable LICENSE](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE) · [current upstream LICENSE page](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE) | Captured source is traceable; applicability to this Typhoon revision is not established by the link alone |
| Typhoon terms | The current [Terms and Conditions](https://opentyphoon.ai/tac) state that they apply to models made available through open-source distribution or third-party platforms and regardless of access method. This is recorded as a source statement, not an interpretation of its legal effect. | Owner/legal review required for the proposed self-hosted use |
| Intended use | Not recorded in the WP24 model choice. Internal development, production, commercial use, and redistribution have not been distinguished. | Owner input required |
| Owner rights statement | WP24 records the BYOM assumption that the owner holds model rights; it is not a completed SEC-007 review or an intended-use approval. | Owner attestation required in the final receipt |
| Tokenizer | Tokenizer files are present in the pinned model snapshot, but the snapshot has no separate tokenizer license file. The model repository's declared license remains input evidence, not owner rights approval. | Owner/legal review remains open |
| Vocoder and reference voice | Not applicable to this text-only LLM candidate; WP24 keeps speech out of scope. | Separate speech gate remains open |

### Candidate A runtime source-level review

WP24 candidate A's [EV02 launch record](evidence/wp24/WP24-2026-09-20-run1/A/EV02/launch-command.txt) and [findings](evidence/wp24/WP24-2026-09-20-run1/A/EV02/FINDINGS.md) identify the experiment stack below. The upstream license files at those exact version tags were checked on 2026-10-03.

| Component and WP24 version | Upstream source-level license evidence | Limit |
|---|---|---|
| Xinference 3.4.0 | Apache License 2.0 in the [v3.4.0 LICENSE](https://raw.githubusercontent.com/xorbitsai/inference/v3.4.0/LICENSE) | Package source license only |
| Transformers 5.17.0 | Apache License 2.0 in the [v5.17.0 LICENSE](https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/LICENSE) | Package source license only |
| PyTorch 2.14.0+cu130 | The [v2.14.0 project metadata](https://raw.githubusercontent.com/pytorch/pytorch/v2.14.0/pyproject.toml) declares `Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT` for installed PyTorch packages. | Does not inventory the exact CUDA wheel payload or its dependency licenses |
| Accelerate 1.15.0 | Apache License 2.0 in the [v1.15.0 LICENSE](https://raw.githubusercontent.com/huggingface/accelerate/v1.15.0/LICENSE) | Package source license only |

This is experiment evidence, not an approved deployment profile. The original 2026-09-22 WP24 candidate A evidence has no dependency lock or SBOM; the current inventory below is a later re-snapshot, not a replacement for those run-time records. Transitive and build-specific components remain unreviewed. A final runtime/code manifest must use the exact deployment artifacts and their generated inventory.

### Current candidate A environment snapshot

On 2026-10-03, I read package metadata from the surviving local candidate A virtual environment without importing runtime packages. The [snapshot](evidence/wp24/WP24-2026-09-20-run1/A/EV02/current-python-distribution-inventory-2026-10-03.json) records 99 installed distributions; Xinference, Transformers, PyTorch, and Accelerate still match the four versions recorded in EV02. It includes package-declared license metadata and hashes for 342 license-related files across 93 distributions.

This is a current-state re-snapshot, not proof of the full 2026-09-22 experiment environment or a deployment lock/SBOM. The inventory preserves declarations and file hashes but does not analyze every license text, host library, or CUDA component. It does not close the runtime/code review.

The snapshot has no embedded license files for six distributions (`aioprometheus`, `nvidia-ml-py`, `quantile-python`, `sentencepiece`, `tokenizers`, and `xoscar`), although each declares license metadata. Three distributions' metadata mentions MPL-2.0 (`certifi`, `orjson`, and `tqdm`). These are review leads, not legal findings; the reviewer must resolve their exact distribution terms and any bundled notices.

The pinned PyPI release records for the six distributions without embedded license files declare the following. These registry declarations are publisher-supplied metadata; they do not replace review of the exact license text and notices for the selected artifacts.

| Distribution/version | PyPI-declared license | Exact release metadata |
|---|---|---|
| `aioprometheus` 23.12.0 | MIT | [PyPI release record](https://pypi.org/pypi/aioprometheus/23.12.0/json) |
| `nvidia-ml-py` 13.610.43 | BSD | [PyPI release record](https://pypi.org/pypi/nvidia-ml-py/13.610.43/json) |
| `quantile-python` 1.1 | Apache License 2.0 | [PyPI release record](https://pypi.org/pypi/quantile-python/1.1/json) |
| `sentencepiece` 0.2.2 | Apache-2.0 | [PyPI release record](https://pypi.org/pypi/sentencepiece/0.2.2/json) |
| `tokenizers` 0.23.2 | Apache Software License classifier | [PyPI release record](https://pypi.org/pypi/tokenizers/0.23.2/json) |
| `xoscar` 0.10.0 | Apache License 2.0 | [PyPI release record](https://pypi.org/pypi/xoscar/0.10.0/json) |

The current [Typhoon Privacy Notice](https://opentyphoon.ai/privacy) is also linked from the pinned README. Privacy/data handling review is separate from the model license receipt and must follow the approved deployment and egress design.

## 4. Required final receipt contents

The final SEC-007 manifest for this candidate should identify, at minimum:

1. Repository, immutable model revision, tokenizer files/revision, and checksums of the staged artifacts.
2. Declared license metadata, the exact license text/source revision reviewed, and any linked terms that the owner/legal reviewer determines are relevant.
3. Runtime/code component names and pinned versions with their separate license sources.
4. Explicit intended use, including whether it is development-only, internal production, commercial use, or redistribution.
5. Owner rights attestation and a named reviewer decision/date. The review must not be described as legal certification.

## 5. Open owner decisions and activation gate

Before the final receipt can be issued, the owner/reviewer must:

1. State the intended use and whether model or derivative weights will be redistributed.
2. Review the mutable upstream license link and current Typhoon terms for the selected self-hosted use; record the decision or obtain legal review.
3. Attest the rights basis for the weights and tokenizer; review exact license text/notices for the six packages and the three MPL-2.0 metadata entries; complete the runtime/code license rows for the chosen deployment profile.
4. Name the reviewer and approve the completed manifest.

Until those fields and decisions are recorded, SEC-007 remains open and model activation remains **BLOCKED**. The model card's Apache tag alone does not satisfy the receipt gate.

## 6. Risk, success, and exit criteria

- **Risk:** HIGH — license and intended-use evidence gate activation.
- **Success:** immutable model provenance and source observations are recorded without claiming owner rights, legal clearance, or deployment approval.
- **Exit for this assessment:** owner review resolves the open decisions; a separate final receipt is created and reviewed. This assessment alone does not close SEC-007.
- **Out of scope:** model download or execution, changing the selected model, runtime implementation, speech/voice rights, production authorization, and legal advice.

## 7. Version diff

| Artifact | Before | After approval |
|---|---|---|
| SEC-007 candidate evidence | Owner-approved v0.1.0 model-provenance assessment | v0.5.0 adds pinned registry declarations for six distributions; still not the receipt |
| Canonical requirement/policy docs | SEC-007 receipt required; activation gated | Unchanged |
| Model selection and activation | Owner-selected model; receipt outstanding | Unchanged; activation stays `BLOCKED` |
| Application code/runtime | No change | No change; experiment observations do not pin a deployment |

## 8. Owner approval

The repository owner approved promotion of the v0.1.0 assessment proposal on 2026-10-03. Later v0.2.0–v0.4.0 edits add dated source observations and review leads; they do not record owner or legal decisions. The approval does not attest to the owner's rights, decide intended use, close SEC-007, or authorize model activation. The open actions in §5 remain required before a final receipt can be issued.
