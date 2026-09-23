# Operator cost — candidate A (Xinference)

Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md`, "Operator cost" after the mandatory gates, and
STACK §7. **Only measured or counted facts are recorded, and no percentage saving is claimed.**
Candidate B's equivalent is `../B/OPERATOR-COST.md`.

Everything here was measured on DESKTOP-VETATMQ during EV02–EV08 between 2026-09-22 and 2026-09-24.
**DEV-07** applies throughout: this is a Windows-native deployment with the transformers backend,
while candidate B ran vLLM in a Linux container, so **no timing here is comparable with candidate
B's**.

## 1. Deploy steps and time

**Prerequisites, once per host, not timed** (all already present on this host):

1. Python 3.12 with the `venv` module.
2. NVIDIA driver and a CUDA-capable GPU (the RTX 5060 Ti, 16 311 MiB).
3. The model weights on local disk (`shared_revision`, **7.51 GiB**).

**Per deployment, performed and timed:**

| # | step | measured |
|---|---|---|
| 1 | create the virtual environment | see §5 |
| 2 | `pip install xinference==3.4.0` | see §5 |
| 3 | **reinstall CUDA torch** (`torch==2.14.0+cu130` from the cu130 index) | see §5 |
| 4 | create the weights **junction** at `<XINFERENCE_HOME>/cache/v2/<name>-<format>-<size>-<quant>` | instant |
| 5 | start `xinference-local --host 127.0.0.1 --port 9997` | **24–44 s** to the first `200` (5 starts across EV02–EV08: 24, 28, 31.2, 32, 44) |
| 6 | register the custom model (`POST /v1/model_registrations/LLM`, `persist: false`) | under 1 s |
| 7 | launch the model (`POST /v1/models`) | **49.3–131 s** warm (49.3, 51, 55, 61, 62); **100 s** on the one cold launch measured (EV02) |

**Step 3 is not optional and is not documented anywhere**: installing `xinference==3.4.0` replaced
the CUDA build of torch with `2.14.0+cpu` from PyPI, after which the cluster reported `gpu_count 0`
and refused to launch on the GPU (EV02). An operator following the obvious order gets a CPU-only
cluster with no warning.

**On-disk footprint after deployment:**

| item | measured |
|---|---|
| virtual environment (`Lib` + `Scripts`) | **3.97 GiB** |
| model weights (shared, not per deployment) | 7.51 GiB |
| pip cache retained | 4.73 GiB |
| `XINFERENCE_HOME` state (databases, logs, per-model virtualenv) | 2.8 GiB across the run |

## 2. Services to operate

| service | why |
|---|---|
| the `xinference-local` process tree: an API process **plus a worker process plus one sub-pool process per model replica** | this is one command to start, but **not one process to manage**: killing the API listener leaves the worker alive (EV06) |
| **an orphan reaper**, PRP's own | force-killing the supervisor leaves the worker holding the GPU (10 610 MiB) and recreating the model actor; the candidate's built-in startup cleanup only matches PPID 1 plus a vLLM-like command line and never fires here (EV06, EV07 partial) |
| **a host firewall or network policy** in front of the metrics endpoints | every listener is loopback-bound, but `/metrics` on the API port and the whole worker exporter answer **without any credential** while the API returns 401, and they disclose `model_uid`, `worker_address`, `gpu_index` and `xinference_home` (EV05) |
| **no external database and no proxy layer** | unlike candidate B, which needed PostgreSQL for LiteLLM virtual keys; candidate A's auth is a local sqlite file |

Listeners opened by one deployment: **four** — the REST API, the worker actor, one actor per model
replica, and the worker metrics exporter (whose port is announced only in the log, EV05).

## 3. Datastores to operate

All local files under `XINFERENCE_HOME`; nothing leaves the host (EV08 step 4):

| file | holds | note |
|---|---|---|
| `auth/auth.db` | users and API keys | keys are stored **hashed and AES-encrypted**, and the encrypted copy is reversible (EV04) |
| `auth/encryption_key`, `auth/jwt_secret_key` | key material | **in the same directory as the database they protect** |
| `launch_history.db` | model launch history | |
| `monitor_config.db` | monitor configuration | |
| `token_routers.db` | token-router configuration | |
| `download_tasks.db` | model download tasks | |
| `cache/v2/<model>` | weights, via junction here | |
| `virtualenv/v4/<model>/<engine>/<python>` | a **per-model virtual environment** the runtime builds | a hard kill can leave it in a state where later launches **hang silently for ~10 minutes with no error**; recovery is to discard the home directory (EV07 partial) |

No prompt or response content reached any of them: a marker request was traced across **57 562
scanned files** and **0 contained the marker** (EV08).

## 4. Custom code PRP has to write, per requirement

Every row is a gap this run measured, not an estimate of effort.

| requirement | what PRP must build | why, measured |
|---|---|---|
| FR-003…009 | the **whole client-key authority**, verifier-only | `GET /v1/admin/keys/{id}/reveal` returns the plaintext key, and the AES key sits beside the database (EV04) |
| FR-010…015 | its **own epoch**, and a join from device index to GPU UUID | the candidate exposes `accelerators: ["0"]` and a replica address but no UUID and no epoch; `created` is always 0 (EV02) |
| FR-010…015, NFR-023 | **reconciliation after an unrequested relocation** | the supervisor relaunches a dead replica by itself (35–40 s on 0.6B, 131.8 s on 4B) and the replica address changes every time (EV03, EV06) |
| FR-017/018 | set `request_limits` at launch and **scrape the metrics exporter** for the limit and the in-flight count | the default is unlimited, and `/v1/models` does not report `request_limits` at all (EV05) |
| FR-020…022 | cancel through the **explicit abort endpoint** with a PRP-generated `request_id`, and map a stream that ends without `[DONE]` to `UNKNOWN` | closing the socket does nothing for non-streaming work (61.5 s of wasted compute measured), and a killed engine returns HTTP 200 with a truncated stream and no error object (EV06) |
| NFR-023 | **pin placement with `gpu_idx`** | otherwise the supervisor chooses the GPU by `IDLE_FIRST_LAUNCH_STRATEGY` (EV07 partial) |
| NFR-024 | an adapter that **replaces candidate error bodies wholesale** and strips `server: uvicorn` | errors carry the internal actor address, the pid and **every model uid on the cluster** (EV08) |
| operations | an **orphan reaper** and a bound on `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` | see §2 |

PRP must also record, on its own side, the launch parameters that the API does not describe:
`POST /v1/models` has **no documented request body** in `/openapi.json`, so `gpu_idx`,
`request_limits` and `replica` exist only in the source (EV07 partial).

## 5. Install, upgrade and rollback

Measured in a throwaway virtual environment (`F:\prp-xinference-upgrade-test`) so the evidence
deployment was never at risk. The GPU was not exercised there: the question is what an operator has
to do, how long it takes, and whether state survives a version change.

### Install, measured

| step | measured |
|---|---|
| create the virtual environment | **5.6 s** |
| `pip install xinference==3.3.0` (packages largely already in the pip cache; no download from a clean host) | **200.1 s** |
| first server start | **32.4 s** to the first `200` |

The evidence deployment's own install of 3.4.0 plus the CUDA torch correction is the same shape;
neither was timed from a genuinely clean host, since the pip cache and the weights were already
local (DEV-06). Candidate B recorded the same caveat for its image pull and weights download.

### Upgrade in place: attempted four times, failed every time

`pip install -U xinference==3.4.0` against a working 3.3.0 environment failed with:

```
ERROR: Could not install packages due to an OSError: [WinError 32] The process cannot access the
file because it is being used by another process:
'f:\prp-xinference-upgrade-test\scripts\xinference-local.exe'
```

This was not a race with a running server. The runtime was stopped first and **zero processes from
that environment remained**; the file was still locked, a manual rename returned `Device or resource
busy`, and it was still locked after waiting 60 s and again after 120 s. The holder was not
identified — no Sysinternals tooling is installed on this host.

**The failed attempts left the environment broken**: `importlib.metadata` could no longer find
`xinference` at all, and pip reported `Ignoring invalid distribution ~inference`, while the old
3.3.0 executables still started a working server. So a failed upgrade does not fail cleanly; it
leaves a deployment whose installed version cannot be read.

### Rollback: the reliable path is rebuild, not pip

| attempt | result |
|---|---|
| `pip install xinference==3.3.0` over the broken environment | same `WinError 32`, non-zero exit |
| but the server still started afterwards | **28.2 s** to the first `200`, reporting 3.3.0 |
| **rebuild the environment and re-import the configuration** | create 5.6 s + install 200.1 s, then EV08's bundle re-import: instance answers in **31.2 s**, model launches in **49.3 s**, and the rebuilt instance matched the original on the model record, a fixed greedy answer and token usage |

The measured conclusion: **on this Windows host, candidate A cannot be upgraded or rolled back in
place.** The operator path that works is to build a new environment and re-import the five-file
configuration bundle, which EV08 proved reproduces the deployment exactly. That is also why the
export bundle matters operationally, not just for the exit question.

This test ran in a throwaway environment (`F:\prp-xinference-upgrade-test`), so the evidence
deployment was never at risk; it was verified intact afterwards (xinference 3.4.0, torch
2.14.0+cu130). Removing the throwaway left **0.37 GiB** behind, because the same locked
`xinference-local.exe` cannot be deleted either.


## 6. Licences

| component | licence | source |
|---|---|---|
| Xinference 3.4.0 | Apache-2.0 | package metadata and the source headers (`Copyright 2022-2026 Xinference Holdings Pte. Ltd`, "Licensed under the Apache License, Version 2.0") |
| xoscar 0.10.0 | Apache-2.0 | package metadata |
| transformers 5.17.0 | Apache-2.0 | package metadata |
| accelerate 1.15.0 | Apache-2.0 | package metadata |
| bcrypt 5.0.0 | Apache-2.0 | package metadata |
| torch 2.14.0+cu130 | BSD-3-Clause, with NVIDIA CUDA components under the **NVIDIA CUDA EULA** | the cu130 wheel bundles NVIDIA runtime libraries |
| the model | **BYOM**: the owner brings the model and holds its rights, and a licence receipt per SEC-007 is required before activation | `scope_decisions.model_licensing` in the run record |

No paid licence is required for the runtime itself.

## 7. Skills the operator needs

Each item is something this run actually required:

- **Python virtual environments and pip index pinning.** Recovering the CUDA torch build needs
  `--index-url https://download.pytorch.org/whl/cu130` and an understanding of why the PyPI wheel
  displaced it.
- **Windows specifics**: directory **junctions** (the launch path tries to create a symlink and
  fails without the privilege), and log files shared by several processes that break rotation at the
  date rollover (`PermissionError WinError 32`).
- **Process-tree management for an actor system**: knowing that the API process, the worker and the
  per-replica sub-pools are separate, and reaping them in the right order.
- **Reading the vendor's source.** Three things needed in production are not in the API or the
  documentation: the abort route, the launch parameters, and the auth switch.
- **Prometheus-style metrics scraping**, since the only per-replica attribution and the only
  readable concurrency limit live in the exporter.
- **Basic sqlite handling and file-level access control** for the auth directory.
