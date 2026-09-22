# EV02 — real A/B registration, candidate A (Xinference)

Gate `PRP-FR-010`..`PRP-FR-015`. Operator observations only; no verdict is computed here. The design
is in `test-design.md`; candidate B's run is in `../../B/EV02/`.

## What was deployed

| item | value |
|---|---|
| install | `pip install xinference==3.4.0` into a venv at `F:\prp-xinference-a` (owner decision: drive C:, which holds Docker's storage, had under 17 GB free) |
| engine | `transformers` 5.17.0 with `torch 2.14.0+cu130`, accelerate 1.15.0 |
| bind | `127.0.0.1:9997`, loopback only, as candidate B was |
| model | the same `shared_revision`, registered as a custom LLM from `F:/prp-models/typhoon2.5-qwen3-4b@ce0a741`, `model_family: qwen3`, `context_length 8192`, the model's own `chat_template.jinja` |
| home | `XINFERENCE_HOME=F:/prp-xinference-a/home` |

**DEV-07 (proposed).** Candidate B ran vLLM inside a Linux container; candidate A runs natively on
Windows with the transformers backend, because vLLM has no Windows build and the only WSL distro on
this host is Docker's own. **No timing comparison between the candidates is valid.** The identity,
registration and placement findings below do not depend on the engine.

Three deployment facts worth recording, each measured:

- Installing `xinference==3.4.0` **replaced the CUDA build of torch with the CPU wheel** from PyPI
  (`2.11.0+cu128` → `2.14.0+cpu`), after which Xinference reported `gpu_count 0` and refused to
  launch with `n_gpu`. Reinstalling `torch==2.14.0+cu130` fixed it. An operator who installs in that
  order gets a CPU-only cluster with no warning.
- The launch path tries to **symlink** the weights into its cache and failed with `A required
  privilege is not held by the client`, the Windows symlink privilege. A directory **junction**
  created at the same path works without any privilege change, and the launch then succeeded.
- `curl` in this shell mangled a UTF-8 Thai body into an `Internal Server Error`. The same request
  from Python with an explicit UTF-8 body worked. Not an Xinference fault; recorded so the artifact
  is not misread.

## Step 1 — launch

Cold launch of the model took **100 s** (`2026-09-22T20:07:03Z` → `20:08:43Z`) and the server itself
needed about 44 s to accept requests. VRAM after load: **10 956 MiB of 16 311 MiB**. A chat
completion answered in 1.4 s warm (`inference-smoke.txt`).

Two lines from the server log are worth carrying forward (`xinference-server-excerpt.log`):

- **It checks VRAM before launching**: `Pre-launch VRAM low for model prp-a-llm-rep0 on GPUs [0]:
  free_ratio=0.79`. The candidate has a pre-launch admission signal of its own, which matters for
  EV05.
- `Failed to load model config from path …cache\v2\…` — a warning while reading the config through
  the junction. The model served correctly afterwards, using the registration's own
  `context_length` and chat template, so it is recorded as a warning, not a failure.

## Step 2 — what the candidate reports about its own runtime

`ev02_probe_A_A_20260922T200855Z.json` (before restart) and `…201150Z.json` (after).

| question | candidate A | candidate B for comparison |
|---|---|---|
| model id / profile | `/v1/models` returns `id`, `model_name`, `model_format`, `model_size_in_billions`, `quantization`, `context_length`, `model_family`, `model_ability` | id and `max_model_len` only |
| **physical placement** | **`accelerators: ["0"]`** and an `address` per replica, from `/v1/models` and `/v1/workers` | nothing; the GPU had to be found with `nvidia-smi` |
| GPU UUID | **not exposed.** `accelerators` gives the device *index*, so PRP still has to join index → UUID itself. `ev02_gpu_binding_A_*.json` matched pid 47100 to `GPU-38430611-…` | same gap |
| worker / supervisor identity | `/v1/workers` lists the worker by `work-ip` with each model replica under it (`prp-a-llm-rep0`); `/v1/supervisor` returns `supervisor_ip` | no such concept |
| **restart identity** | **yes, usable**: terminating and relaunching the model changed the replica `address` (`127.0.0.1:62147` → `127.0.0.1:63318`) while 57 other identifiers stayed the same (`ev02_restart_identity_A_A_*.json`) | no stable identity; only `process_start_time_seconds` in `/metrics` moved |
| start time / epoch | `created` is `0` in `/v1/models`; there is no epoch field. The changing `address` is the only restart signal | `created` was the current time on every call, so it was useless |

## Step 3 — the negative tests

**Test 1, same alias with a different profile** (`negative-test1-same-alias-different-profile.txt`).
Re-registering the same `model_name` with `context_length 4096` was **refused**: `400 … Model
prp-typhoon25-qwen3-4b already registered`. Registering a *second* name over the same weights
succeeded, and the two stay separate entries. The candidate never silently merges two profiles
under one alias, which is what FR-010…015 needs.

**Test 2, one runtime counted twice** (`negative-test2-two-uids-one-weights.txt`). On one host the
procedure's "two origins, one runtime" was adapted to launching a second `model_uid` from the same
registration. It **failed before it started**: `The paging file is too small for this operation to
complete (os error 1455)` — a Windows host limit with 31.8 GiB RAM and 5.7 GiB free, not a GPU OOM.
VRAM was unchanged and the first model kept answering. **The capacity-counting question is therefore
unanswered on this host.**

## Step 4 — authentication

**Xinference 3.4.0 authenticates by default**, which its older documentation does not describe. With
the server started plainly, `XINFERENCE_AUTH_ADVANCED` defaults to true and a first-run admin setup
is required.

| endpoint | default (auth on) | with `XINFERENCE_AUTH_ADVANCED=0` |
|---|---|---|
| `/v1/models` | **401** with a `WWW-Authenticate` challenge | 200 |
| `/v1/model_registrations/LLM` | **401** with challenge | 200 |
| `/v1/workers` | **401** with challenge | 200 |
| `/v1/supervisor` | **401** with challenge | 200 |
| `/v1/cluster/auth` | 200, by design (bootstrap) | 200 |
| `/v1/admin/setup/status` | 200, by design (bootstrap) | 404 |

The measurements in steps 1–3 were taken with `XINFERENCE_AUTH_ADVANCED=0`, because enabling the
default path requires creating an administrator account, which the operator did not do in this run.
Both states are recorded above.

Compared with candidate B, where `/metrics` and `POST /invocations` served without any credential
(EV02, EV03), Xinference's default posture is stricter: every inspection endpoint challenges, and
only the two bootstrap endpoints are open. The `0` switch that removes all authentication is itself
worth noting: an operator can disable it with one environment variable.

## Limits of this run

- **One GPU host (DEV-03)**: "A and B as independent replicas" was not shown, the same limit as
  candidate B.
- **DEV-07**: Windows-native transformers, so no timing comparison with candidate B.
- The capacity-counting negative test did not run (host paging file).
- Distributed Xinference (supervisor with remote workers) was not deployed; only the local worker.
- The default-auth path was observed but not exercised with a real account.
