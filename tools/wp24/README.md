# tools/wp24 — WP24 EV02 operator tooling

Standalone scripts the owner runs on GPU hosts A and B, and from the control machine, to execute
EV02 "Real A/B registration" of `docs/WP24-EXPERIMENT-PROCEDURE.md` (gate `PRP-FR-010`..`PRP-FR-015`).
Start at [`EV02-CHECKLIST.md`](EV02-CHECKLIST.md) for the step-by-step operator walkthrough; this
file documents the scripts themselves.

**These tools produce evidence inputs for a WP24 run record — measurements, observations and
artifact file names — never a PASS/FAIL/BLOCKED verdict.** `docs/WP24-EXPERIMENT-PROCEDURE.md`
section 3 item 4 reserves that decision for the reviewer, based on the criteria in section 5.

## Constraints

- **Python 3.12, standard library only.** No third-party or ML imports. Every script runs on a
  host where only Python is installed (`urllib.request`, `json`, `subprocess`, `argparse`,
  `platform`, `shutil`, `time`, `datetime`, `hashlib` and friends).
- **No secrets in code.** Credentials come from an environment variable whose *name* is passed on
  the command line (`--token-env NAME`); the token value itself is never a CLI argument, never
  printed, and never written to JSON output. Any `Authorization` header this tooling logs is
  written as `Authorization: <redacted>`.
- **Redaction.** Every JSON output is walked before it is written and any Windows (`C:\Users\<name>\...`)
  or POSIX (`/home/<name>/...`, `/Users/<name>/...`) home-directory path is rewritten to `<home>`
  wherever it appears, including inside the recorded `command_line`.
- **Machine-readable JSON.** Every script writes one JSON file to `--out <dir>` (default
  `./wp24-out`). The file name always includes the candidate and/or host id it concerns, the JSON
  body always carries `generated_at_utc` (ISO-8601 UTC) and `command_line` (the exact invocation,
  redacted), and always carries `measurements` (list of `{name, value}`), `observations` (list of
  strings), `source_observations` (always `[]` — see below) and `artifacts` (list of file names
  this run wrote, normally just its own file name).
- **No verdicts.** Nothing in `tools/wp24/` computes `PASS` / `FAIL` / `BLOCKED`. `source_observations`
  is always emitted empty on purpose: it is where the operator later adds notes drawn from
  documentation (e.g. citing `docs/STACK-EVALUATION-PRP.md` section 4 or a `SRC-nn` row), which
  this tooling cannot manufacture from a live run.
- **Doc-cited endpoints.** Default endpoints for candidates A and B are the ones confirmed against
  official documentation (URLs below and in code comments next to each entry). An endpoint that
  could not be confirmed is not guessed at; it must be supplied via `--endpoints endpoints.json`
  and is marked `"verified": false` with a note "unverified, to be observed at run time" in the
  output.

## Scripts

### `host_inventory.py`

Run on the control host and on each GPU host. Records OS / kernel / Python version, GPU inventory
(`nvidia-smi -L` and `nvidia-smi --query-gpu=name,memory.total,driver_version,uuid --format=csv,noheader`),
CUDA version parsed from the bare `nvidia-smi` header (both the Linux label `CUDA Version:` and the
Windows label `CUDA UMD Version:`; the matched label is recorded as `cuda_version_header_label`),
disk free space for `--weights-path`, two optional clock checks, and container-runtime presence (`docker
--version` / `systemctl --version`, version check only, nothing is started). A missing `nvidia-smi`
is recorded as an observation ("nvidia-smi not found on this host"), never a crash — a control host
with no GPU driver is expected and allowed by `docs/WP24-EXPERIMENT-PROCEDURE.md` section 2.

```
python tools/wp24/host_inventory.py --host-id A --weights-path D:/models --out wp24-out
python tools/wp24/host_inventory.py --host-id control --ntp-check
python tools/wp24/host_inventory.py --host-id control --reference-time 2026-09-20T12:00:00Z
```

Clock checks: `--ntp-check` queries an NTP server read-only (`w32tm /stripchart` on Windows,
`chronyc tracking` or `ntpdate -q` elsewhere, whichever is installed; default server
`time.windows.com` on Windows, `pool.ntp.org` otherwise; the clock is never adjusted) and reports
`ntp_offset.offsets_seconds` as local minus server. `--reference-time` still works but its result is
named `reference_time_delta_seconds` because it includes the seconds between fetching the reference
and running the script (values of 5-11 s were seen on a host whose real offset was -0.6 s); treat it
as an upper bound only. When no NTP tool exists on the host the script records that and continues.

Feeds `environment.control_host` / `environment.gpu_hosts[]` of the run record template.

### `ev02_probe.py`

Run from the control machine against a runtime already launched on host A or B. For every
configured endpoint, performs the request twice — once with no credential, once with a bearer
token read from the environment variable named by `--token-env` (if set) — and records status
code, whether a `WWW-Authenticate` (or equivalent) challenge header is present, response size,
latency, and a redacted JSON body sample capped at 4 KB. Model IDs/revisions and anything that
looks like a GPU UUID, worker identifier or restart epoch are extracted heuristically into
`extracted_identifiers` for `ev02_restart_identity.py` to diff later. States explicitly in
`observations` when no probed endpoint exposed a physical GPU UUID mapping — itself an EV02
finding, not a tool error.

```
python tools/wp24/ev02_probe.py --candidate B --base-url http://10.0.0.2:8000 --host-id B \
    --token-env WP24_RUNTIME_TOKEN --out wp24-out
python tools/wp24/ev02_probe.py --candidate A --base-url http://10.0.0.1:9997 --host-id A \
    --endpoints endpoints.json --out wp24-out
```

Default endpoints and their documentation:

| Candidate | Endpoint | Doc |
|---|---|---|
| B (vLLM) | `GET /v1/models` | <https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/> |
| B (vLLM) | `GET /metrics` | <https://docs.vllm.ai/en/latest/usage/metrics.html> — Prometheus text, not covered by `--api-key` per <https://docs.vllm.ai/en/latest/usage/security/> (only `/v1`, `/v2`, `/inference`, `/cohere` are) |
| A (Xinference) | `GET /v1/models` (running models) | <https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html> |
| A (Xinference) | `GET /v1/model_registrations/LLM` | <https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html> |
| A (Xinference) | `GET /v1/workers` | <https://inference.readthedocs.io/en/stable/_modules/xinference/client/restful/restful_client.html> — confirmed from the shipped client source; not enumerated on the narrative docs page above |
| A (Xinference) | `GET /v1/supervisor` | same source as `/v1/workers`, same caveat |
| A (Xinference) | `GET /v1/cluster/auth` | same source as `/v1/workers`, same caveat |
| A (Xinference) | `GET /v1/admin/setup/status` | <https://inference.readthedocs.io/en/latest/user_guide/auth_system.html> — documented as unauthenticated by design (bootstrap status check) |

Feeds `experiments.EV02.per_candidate.<X>.{measurements,observations,artifacts}` — see
[`EV02-CHECKLIST.md`](EV02-CHECKLIST.md) for the full field mapping.

### `ev02_gpu_binding.py`

Run *on* a GPU host while the candidate's runtime is up. Joins `nvidia-smi --query-gpu=uuid,index
--format=csv,noheader` with `nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory
--format=csv,noheader` (the `gpu_uuid` field is added to the compute-apps query — without it there
is no shared key to join the two tables on) and reports the PIDs whose process name matches
`--process-pattern` (default `vllm|xinference|python`) together with the GPU UUID/index they are
bound to. Everything else is counted (`unrelated_process_count`), never named, for privacy.

```
python tools/wp24/ev02_gpu_binding.py --host-id A --out wp24-out
python tools/wp24/ev02_gpu_binding.py --host-id B --process-pattern "vllm" --out wp24-out
```

Also used, with a candidate-specific `--process-pattern`, to confirm "no lingering `nvidia-smi`
process" during the reset-between-candidates step (`docs/WP24-EXPERIMENT-PROCEDURE.md` section 3
item 1) — see the checklist.

### `ev02_restart_identity.py`

Pure file processing, no network or device access. Diffs the `extracted_identifiers` maps of two
`ev02_probe.py` JSON outputs captured before and after a runtime restart, and reports what was
added, removed, changed, or stayed the same.

```
python tools/wp24/ev02_restart_identity.py \
    --before wp24-out/ev02_probe_B_B_<ts1>.json \
    --after wp24-out/ev02_probe_B_B_<ts2>.json \
    --out wp24-out
```

### `ev05_admission_load.py`

EV05 steps 2–3 (gate `PRP-FR-017` / `PRP-FR-018`), per the design in
`docs/evidence/wp24/WP24-2026-09-20-run1/B/EV05/test-design.md`. It calls the vLLM server directly,
never through LiteLLM.

- `--processes` OS processes, each with `--per-process` concurrent streaming requests of
  identical length (`max_tokens` + `ignore_eos`), released together.
- `/metrics` is polled every `--poll-interval` seconds for `vllm:num_requests_running` /
  `vllm:num_requests_waiting`.
- Each scrape is compared with the client-side bounds on requests that could have been inside the
  server during that scrape. The script reports scrapes above those bounds (over-count) or above
  `--limit`.
- Step 3: records where `max_num_seqs` is readable, checking `/metrics`, `/v1/models`, `/version`
  and, with `--container`, `docker logs`.

```
python tools/wp24/ev05_admission_load.py --base-url http://127.0.0.1:8000 \
    --token-env VLLM_API_KEY --model typhoon2.5-qwen3-4b --limit 4 \
    --processes 3 --per-process 4 --label run-B --container prp-wp24-vllm-b --out wp24-out
```

## Environment variables

| Name | Used by | Meaning |
|---|---|---|
| any name passed to `--token-env` (e.g. `WP24_RUNTIME_TOKEN`) | `ev02_probe.py`, `ev05_admission_load.py` | Bearer token for the credentialed request. Never pass the token value itself on the command line; only the variable *name*. |

No other script reads an environment variable for a secret.

## Quality gates

```
python -m py_compile tools/wp24/*.py
python -m unittest discover -s tools/wp24/tests
```

From `apps/control-api` (its `uv.lock` has ruff pinned):

```
uv run --locked ruff check ../../tools/wp24
uv run --locked ruff format --check ../../tools/wp24
```
