# Operator cost — candidate B (independent vLLM + speech services)

`docs/WP24-EXPERIMENT-PROCEDURE.md` section 5, "Operator cost", recorded after the mandatory gates
(EV02–EV06, EV08) were run. Only measured or counted facts are here; nothing is expressed as a
percentage or as time saved, which that section forbids. No verdict is computed.

The speech half of candidate B has not been deployed (WP10), so everything below covers the LLM
runtime plus the key/proxy layer that EV03 / EV04 ran.

## Deploy steps and time

**Prerequisites, done once per host and not measured in this run** (they were already in place on
DESKTOP-VETATMQ before WP24):

1. NVIDIA driver and a GPU-capable container runtime (here Docker Desktop on WSL2).
2. `docker pull vllm/vllm-openai@sha256:c2914767…51ae1` — **30.5 GB** image. Not timed; it was
   already cached.
3. Fetch the model revision `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741` — **7.49 GiB** of bf16
   safetensors — and verify the file hashes. Not timed.

**Per deployment, all performed and timed in EV05 / EV06 / EV08:**

| # | step | evidence |
|---|---|---|
| 1 | generate the runtime key and place it where the launch can read it | EV08 step 3 |
| 2 | one `docker run` with the pinned digest, the weights mount, `--gpus all`, `--ipc=host`, the loopback port binding and the seven vLLM flags | `EV05/launch-command.txt` |
| 3 | wait for `/health` 200 | EV05, EV06, EV08 |
| 4 | confirm identity and readiness: startup `non-default args`, `/v1/models`, one completion | EV08 `fingerprint` |
| 5 | apply the host-level network policy that keeps other local processes off the runtime | required by EV05 step 1; **not yet implemented on this host** |

**Counted:** 3 prerequisite steps, 5 per-deployment steps.

| measurement | value | source |
|---|---|---|
| container create → `/health` 200, cold (new container, no compile cache) | **217, 223, 225, 226, 260 s** across five launches; about **3.7–4.3 min** | EV05, EV06, EV08 |
| restart of an existing container (warm, compile cache kept) | **93 s** (98 s in the first run) | EV06 |
| ready after `docker start` of a container that had exited | **73 s** (79 s in the first run) | EV06 |
| deploy time from a clean host, including image pull and weights download | **not measured** | — |

## Services to operate

| service | why | note |
|---|---|---|
| vLLM runtime, one container per GPU host | serves the model | no supervisor of its own: after `kill -9` of its engine the API server exits and the container stops (EV06) |
| a supervisor | restarts the runtime | Docker's restart policy, or PRP's own. This run used no restart policy, so recovery was manual |
| key/proxy layer (LiteLLM), **only if** candidate B's key layer is used | issues and revokes client keys, which bare vLLM cannot (EV04) | not run in EV05–EV08 |
| PostgreSQL 16, required by that proxy | virtual-key store | — |
| host network policy (firewall rule or dedicated namespace) | every local process can otherwise reach the runtime, and `/invocations` and `/metrics` answer without a key (EV05 step 1, EV03) | to be built |

## Datastores to operate

| store | what it holds | persistence |
|---|---|---|
| PostgreSQL (with the proxy layer) | virtual keys and spend rows | persistent, PRP-controlled |
| container writable layer (`/root/.cache/vllm`, `.triton`, `flashinfer`, `torchinductor`) | compile caches; **no job data** — an EV08 marker request left no trace in 1292 searched roots | container lifetime; lost on recreate, which is why a recreate costs 3.7–4.3 min instead of 93 s |
| `docker logs` json-file on the host | vLLM's own log; request counts, **no prompt content** (EV06, EV08) | until the container is removed |
| `/root/.config/vllm/usage_stats.json` plus the report vLLM posts to `https://stats.vllm.ai` at startup and every 600 s | host and config telemetry, no prompts | **leaves the platform unless `VLLM_NO_USAGE_STATS=1` or `DO_NOT_TRACK=1` is set at launch** (EV08 step 4) |
| GPU memory prefix cache | prompt tokens | volatile; cannot be deleted on request; gone on restart (EV06) |

## Custom code PRP has to write (custom gap), per requirement

Each row is something the candidate cannot do, observed in a run; none is an estimate of effort.

| requirement | what PRP must write | observed in |
|---|---|---|
| FR-003…FR-009 | the whole client-key authority: issuing, scoping, expiry, quota, revocation. Bare vLLM has a flat key list, no scopes and no revoke API | EV04 |
| SEC / NFR-023 boundary | a host-level network policy in front of the runtime | EV05 step 1, EV03 |
| NFR-023 | binding confirmation from the engine's own access log: LiteLLM v1.90.2 sends none of the documented routing headers | EV03 |
| FR-017 | the durable admission transaction (PostgreSQL plus fencing). Nothing on the candidate side does this | EV05 |
| FR-018 | hold `max_num_seqs` in PRP's own config, since no API returns it, and treat the running/waiting gauges as a signal that can under-count at burst edges; also respect the KV-cache ceiling (1.71 requests at 8192 tokens) | EV05 |
| FR-020…FR-022 | UNKNOWN / QUARANTINED reconciliation. Once HTTP 200 is sent, only an in-stream error object means "failed"; a cut stream means nothing, and there is no request-status API | EV06 |
| NFR-024 | an adapter that strips or rewrites every vendor field: `model`, `chatcmpl-` ids, `system_fingerprint` (vendor **and version**), a dozen extra response fields, `owned_by`/`root` in the model list and the `server: uvicorn` header | EV08 step 1 |
| NFR-024 | a normalised error mapping: vLLM's 401 body is a bare string while 400 and 404 are objects | EV08 step 1 |
| NFR-024 / SEC | key delivery through a read-only config file instead of `VLLM_API_KEY`, which `docker inspect` shows in plaintext, and rotation orchestration (overlap, then drop, each step a relaunch) | EV08 step 3 |
| NFR-024 / privacy | `VLLM_NO_USAGE_STATS=1` in every launch | EV08 step 4 |

## Upgrade and rollback

**Not attempted** (owner decision, 2026-09-22). A real version upgrade means pulling a second
vLLM image of about 30.5 GB, which was judged not worth the bandwidth in this run. `upgrade_steps_tried`
and `rollback_steps_tried` stay null in the run record.

What the other runs already show about that path, which is not a substitute for trying it:

- a deployment is one `docker run` from a digest-pinned image plus a redacted export file, and an
  import from that export alone reproduced the source exactly (EV08 step 2), so a rollback to a
  previous **configuration** is one relaunch;
- any relaunch costs a cold start of 3.7–4.3 min, because a new container has no compile cache;
- nothing in the runtime survives it: no job state, no queue (EV06).

## Licenses required

| item | license | how it was checked |
|---|---|---|
| vLLM 0.29.0 in the pinned image | Apache-2.0 | the LICENSE file inside the image's `vllm-*.dist-info/licenses/` |
| model `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741` | Apache-2.0 | Hugging Face license tag at that revision (run record `shared_revision`). The SEC-007 licence receipt is still to be filed before activation |
| LiteLLM v1.90.2 (key layer) | **not verified in this run** — its image does not carry package metadata at the expected path | — |
| PostgreSQL 16 | **not verified in this run** | — |

## Operator skills required

Named from what the runs actually demanded, not from a job description:

- containers with GPU passthrough, including the WSL2 quirk that made vLLM fail to start until
  `VLLM_WSL2_ENABLE_PIN_MEMORY=1` was set (`.brain/rca/RCA-2026-09-21-vllm-wsl2-uva.md`);
- reading engine logs to find the truth the API does not return: the concurrency limit, the
  `EngineDeadError` behind a cut stream, the abort-on-shutdown mode;
- Prometheus metrics, and knowing which of them may under-count;
- key handling without putting a key into `docker inspect`, a log or a command line;
- YAML/CLI configuration of the runtime, and hash verification of model files.

## What this section cannot say

- Deploy time from a genuinely clean host, since the image and weights were already local.
- Upgrade and rollback, not attempted.
- Anything about candidate A, which has not run (DEV-02), so there is no A-versus-B comparison.
- Speech services (WP10).
