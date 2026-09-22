# EV02 test design for candidate A (Xinference) on a single GPU host

Gate `PRP-FR-010`..`PRP-FR-015`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV02, steps 1–4, and
the operator walkthrough in `tools/wp24/EV02-CHECKLIST.md`. Candidate B's EV02 is the comparison
point (`../../B/EV02/`).

## Deployment decisions, and why

| decision | choice | reason |
|---|---|---|
| install method | Python venv at `F:\prp-xinference-a`, `pip install xinference==3.4.0` | **owner decision 2026-09-22.** Drive C: has about 17 GB free and holds Docker's storage; the Xinference image is about 6.8 GB compressed. A venv on F: (167 GB free) avoids that, and supervisor + worker from a package is Xinference's own documented deployment [SRC-09] |
| pip cache | `PIP_CACHE_DIR` on F: | the default cache is on C: |
| version | `xinference==3.4.0`, matching the `xinference-client==3.4.0` already recorded in the run record | pinned, not `latest` |
| engine | whatever Xinference selects on this host, expected to be transformers | **vLLM has no Windows build**, and the only WSL distro here is Docker's own, so candidate A runs natively on Windows. Recorded as **DEV-07** below |
| model | the same `shared_revision`: `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741` from `F:/prp-models/…`, registered as a custom model | procedure §3 item 1: same revision for every candidate |
| bind | `127.0.0.1:9997` | the same loopback-only exposure candidate B had |

**Proposed DEV-07.** Candidate B ran as vLLM inside a Linux container; candidate A runs natively on
Windows with the transformers backend. Any timing or throughput number is therefore **not**
comparable between the two candidates. EV02 asks about identity, registration and placement
reporting, which do not depend on the engine, so the comparison stays meaningful for this gate; any
later EV that measures time must state this deviation.

## Reset between candidates (procedure §3 item 1)

Candidate B is already stopped: no `prp-wp24-vllm-b` container exists and the prp-mvp vLLM is not
running. Before launching A the run records:

- `docker ps -a` showing no candidate-B runtime;
- `tools/wp24/ev02_gpu_binding.py --host-id A --process-pattern "vllm|xinference|python"`, whose
  `matched_processes` must be empty;
- that the model weights cache on `F:/prp-models` is **kept**, which §3 item 1 allows if recorded.

## Steps

### Step 1 — launch

`xinference-local --host 127.0.0.1 --port 9997` starts a supervisor and a local worker. The exact
command, stdout and stderr are kept as artifacts. Then the model is registered from the local path
and launched, and the launch command and the returned model UID are recorded.

### Step 2 — what the candidate reports

`tools/wp24/ev02_probe.py --candidate A` already knows the documented endpoints: `/v1/models`,
`/v1/model_registrations/LLM`, `/v1/workers`, `/v1/supervisor`, `/v1/cluster/auth`,
`/v1/admin/setup/status`. It records each payload twice, without and with a credential.

The run then answers, for each item, whether the candidate itself supplies it:

- model id and revision;
- the process that holds the GPU, joined against real `nvidia-smi` UUIDs by
  `ev02_gpu_binding.py`;
- a start time, and any identifier that changes on restart, compared before and after with
  `ev02_restart_identity.py` — candidate B had **no** stable runtime identity and only
  `process_start_time_seconds` in `/metrics` moved on restart.

### Step 3 — the two negative tests

1. **Same alias, different profile.** Register a second custom model under the same model name with
   a different profile (a different `max_tokens` / context setting), launch both, and see whether
   Xinference keeps them apart or merges them into one.
2. **Two origins, one runtime.** Address the same running worker through two origins
   (`127.0.0.1:9997` and the host's own address) and see whether the cluster counts one capacity or
   two.

### Step 4 — authentication

`ev02_probe.py` flags any endpoint that answers 2xx with no credential, or 401/403 with no
`WWW-Authenticate`. Xinference's auth system [SRC-10] is off unless configured, so the run records
the default state first, then, if auth is enabled, repeats the endpoint sweep.

## What this cannot reach

- **One GPU host (DEV-03)**, so "A and B as independent replicas" cannot be shown; the same
  limitation as candidate B's EV02.
- **Engine parity (proposed DEV-07)**: no timing comparison with candidate B.
- Distributed Xinference (a supervisor with remote workers) is not deployed; only the local worker.

## Tooling

No new tooling. `tools/wp24/host_inventory.py`, `ev02_probe.py`, `ev02_gpu_binding.py` and
`ev02_restart_identity.py` already carry candidate A's documented endpoints and were written for
exactly this run.

## Run precondition

The GPU must be free; the model is 7.49 GiB of bf16 weights and the transformers backend loads all
of it. Installing the venv downloads several GB (torch with CUDA) onto F:.
