# EV08 — adapter / exit, candidate B

Gate `PRP-NFR-024`. These are operator observations only; no verdict is computed here. The design is
in `test-design.md`.

- **Runtime.** Launched as in `../EV05/launch-command.txt` at 2026-09-22T15:38:33Z; cold, ready in
  about 225 s. Every request went straight to vLLM. LiteLLM was not run (sub-spike decision). All
  containers were stopped and removed at 15:55:46Z.
- **Keys.** Both keys were one-off, and neither is in any repository file.

## Step 1 — mapping and what the vendor exposes

### Mapping

The public name below is illustrative; naming is PRP's decision.

| client `model` (PRP, public) | `ModelProfile` (PRP) | `RuntimeDeployment` (PRP) | vendor identifiers (vLLM) |
|---|---|---|---|
| e.g. `prp-chat-th-small` | `id`; `revision` = `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741`; `profile_hash` over the model-file hashes in the export | `node_id`, `profile_epoch`, `manager_uid` | `--served-model-name typhoon2.5-qwen3-4b`, mount path `/models`, image `vllm/vllm-openai@sha256:c2914767…51ae1` |

- `prp-client.yaml` contains no vendor name: a grep for vllm / xinference / litellm / typhoon / qwen
  finds 0 matches.
- The client inventory is unchanged (`validate_docs.py`). The worker contract already keeps
  alias → profile mapping in the control plane.

### Leak scan

Responses taken straight from vLLM (`ev08_leak_scan_B_src_*.json`), compared with the client
contract. Every client schema below has `additionalProperties: false`.

| response | vendor-specific content | what the adapter must do |
|---|---|---|
| every response | header `server: uvicorn` | drop or replace |
| chat | `model` = served-model-name (`typhoon2.5-qwen3-4b`) | rewrite to the public alias |
| chat | `id` = `chatcmpl-<hex>` | replace with PRP's own id (the client needs PRP's request id anyway) |
| chat | `system_fingerprint` = `vllm-0.29.0-de711e39`, which names the vendor **and its version** | strip; not in `ChatResponse` |
| chat | extra top-level fields `kv_transfer_params`, `ec_transfer_params`, `metrics`, `prompt_logprobs`, `prompt_text`, `prompt_token_ids`, `service_tier` | strip; not in `ChatResponse` |
| chat | extra choice fields `logprobs`, `routed_experts`, `stop_reason`, `token_ids`; extra message fields `annotations`, `audio`, `function_call`, `reasoning`, `refusal` | strip; not in `ChatChoice` / `Message` |
| chat | `usage.prompt_tokens_details`, `usage.completion_tokens_details` | strip; not in `Usage` |
| stream chunk | `model`, `id`, `prompt_token_ids`, `prompt_text` | the same rewrite and strip, per chunk |
| `/v1/models` | `owned_by: vllm`, `root: /models`, `parent`, `max_model_len`, `permission[]` with `modelperm-*` ids | serve PRP's own model list; `Model` allows only `id`, `object`, `created`, `owned_by` |
| 400 | `{"error": {message, type: "BadRequestError", param, code}}` | map into `Error` / `ErrorBody` with PRP's `request_id` and `safe_to_retry` |
| 404 | `The model \`no-such-model\` does not exist.` echoes the client's own string | map; do not reveal served names |
| 401 | `{"error": "Unauthorized"}`, **a string, not an object**, unlike the other errors | map; the shape differs, so it needs its own branch |

Unlike LiteLLM in EV03, vLLM's own error bodies contain no host, port, IP or stack trace.

## Step 2 — export, and import from the export alone

- **Export** (`ev08_export_B_src_*.json`). It holds:
  - the image digest and the full command;
  - `VLLM_WSL2_ENABLE_PIN_MEMORY=1`, the one allow-listed env value;
  - `VLLM_API_KEY` by **name only**;
  - the port binding, the read-only weights mount and `--gpus all` / `--ipc=host`;
  - sha256 of `config.json`, `tokenizer.json`, `tokenizer_config.json`, `chat_template.jinja` and
    `model.safetensors.index.json`. This revision has no `generation_config.json`; it is recorded
    as absent.

  The self-check found no plaintext key in it.
- **Import.** The source container was removed and a new one launched **from the export alone**,
  with the key supplied at launch (`ev08_launch_B_import_*.json`). It was ready 223 s later (cold:
  new container, no cache).
- **Compare** (`ev08_compare_B_src-vs-import_*.json`): **equal on all four fields**:
  - startup `non-default args`;
  - `/v1/models`, ignoring `created` and the random `permission` ids;
  - `vllm:cache_config_info`;
  - the fixed greedy answer (`กรุงเทพฯ`).
- **Deviation DEV-06.** The import ran as a new container on the same host, not on a clean second
  host.

## Step 3 — key rotation

### Plan

- **Client keys** belong to PRP's own verifier (one client-key authority), so leaving vLLM never
  touches a client key.
- **The vLLM key** is an internal worker credential (`credential_ref`). Bare vLLM has no revoke API
  (EV04) and reads keys only at startup. A rotation is therefore three steps, each a relaunch:
  1. launch with old + new;
  2. switch the adapter to new;
  3. launch with new only.
- **Downtime.** Without a second replica (DEV-03), each relaunch is downtime.
- **LiteLLM layer.** Its rotation (hash-addressed keys, regenerate) is summarised from EV04 and was
  not re-run.

### Check

| stage | no key | old (A) | new (B) | key value in `docker inspect` | in `docker logs` |
|---|---|---|---|---|---|
| source, A through `VLLM_API_KEY` | 401 | 200 | 401 | **A: yes, plaintext** | no |
| import, A through `VLLM_API_KEY` | 401 | 200 | 401 | **A: yes, plaintext** | no |
| overlap, A + B through a read-only `--config` YAML | 401 | 200 | 200 | no | no |
| new only, B through `VLLM_API_KEY` | 401 | **401** | 200 | **B: yes, plaintext** | no |

- **The overlap-then-drop sequence works:** the old key stops working at the second relaunch.
- **Every key change needs a new container, about 220 s cold here** (226 s and 217 s). The key
  source is fixed when the container is created, whether it is an env var or a mounted file.
  Editing a mounted key file and running `docker restart` would reuse the warm container (about
  93 s in EV06). That path is not tested here.
- **`VLLM_API_KEY` is readable in plaintext** by anyone who can run `docker inspect` on the host.
  The `--config` file route keeps the key out of `docker inspect`. vLLM reads only one key from
  `VLLM_API_KEY` (`entrypoints/serve/middleware/register.py`), so any overlap needs `--api-key` or
  `--config` anyway.

## Step 4 — where job data could end up outside PRP's deletion fence

A request carrying a unique marker was sent, then every added or changed path in the container was
searched: 1292 search roots out of 11875 `docker diff` entries.

| store | kind | holds job data? |
|---|---|---|
| container writable layer: compile caches (`/root/.cache/vllm`, `.triton`, `flashinfer`, `torchinductor`, …) | persistent for the container's life | **no**: the marker was not found in any added or changed file |
| `docker logs` (json-file driver; a log file on the Docker host) | persistent on the host until the container is removed | **no**: the marker was not in the log. vLLM logs request counts, not content, at its default level |
| `/root/.config/vllm/usage_stats.json` | persistent for the container's life | no prompts: hardware, config and a `uuid` (`step4-usage-stats.txt`) |
| **usage stats sent to `https://stats.vllm.ai`** | vendor server, outside the host | no prompts, but **host and config telemetry leaves the platform by default**: at startup and every 600 s. The opt-outs (`VLLM_NO_USAGE_STATS=1` / `DO_NOT_TRACK=1`) were not set. Actual egress was not captured |
| in-memory prefix cache | volatile | prompt tokens, held in GPU memory only; gone on restart (EV06); cannot be deleted on request |
| Responses API store | absent | off by default (EV06) |

## Limits of this run

- **DEV-06:** there was no clean second host.
- **Fake-adapter replacement through client conformance** needs PRP's adapter layer (M4). The
  mapping and strip list above are its inputs.
- **Replay through a replacement candidate** needs candidate A (DEV-02).
- The warm-restart rotation path and actual telemetry egress were not measured.
