# EV02 step 3 — negative tests, candidate B (vLLM 0.29.0)

Operator notes captured with the raw artifacts in this directory. These are observations, not verdicts.

## Setup

One vLLM container, alias `typhoon2.5-qwen3-4b`, relaunched with `--max-model-len 4096`
(the baseline run used 8192), with two host origins published to the same container port:
`127.0.0.1:8000` and `127.0.0.1:8001`. Command in `../negative-test-launch-command.txt`.

## Case 1 — same alias, different profile

`/v1/models` reports `max_model_len: 4096` under the same `id` (baseline: 8192), and
`/metrics` `vllm:cache_config_info` carries the resolved profile
(`kv_cache_size_tokens="10576"`, `kv_cache_max_concurrency="2.58203125"`,
`num_gpu_blocks="661"`, `gpu_memory_utilization="0.7"`, `block_size="16"`).
The profile is therefore observable per runtime instance.

vLLM has no cross-process model registry: each server process serves its own alias list, so
two instances of the same alias are never merged or compared by the candidate. Whether two
profiles under one alias are distinguishable is entirely PRP's problem to solve, not the
candidate's.

## Case 2 — two origins, one runtime

Both origins are the same container and the same process. The model listing does NOT say so:

| field | origin :8000 | origin :8001 | same runtime? |
|---|---|---|---|
| `data[0].id` | typhoon2.5-qwen3-4b | typhoon2.5-qwen3-4b | indistinguishable either way |
| `data[0].created` | 1789946489 | 1789946491 | **differs** |
| `permission[0].id` | modelperm-b7fb58673e5b11ff | modelperm-9a91bb3f39a5c5ce | **differs** |
| `/metrics` `process_start_time_seconds` | 1.78994622059e+09 | 1.78994622059e+09 | **identical** |

## Correction to the earlier restart-identity reading

`created` and `permission[].id` are **not** runtime identity and **not** a restart epoch.
Three consecutive calls to one origin (`same-origin-repeated-calls.txt`) return three
different `modelperm-*` values, and `created` tracks the wall clock at request time, not
process start. The three "changed identifiers" seen in
`../ev02_restart_identity_B_B_20260920T223039Z.json` were the passage of time between the two
snapshots, not evidence of the restart.

Consequence for FR-010..015: the authenticated model listing carries **no** stable runtime
identity. The only stable identity and profile source observed is `/metrics`
(`process_start_time_seconds` plus `vllm:cache_config_info`) — which is the endpoint that
`--api-key` does **not** protect (see the EV02 step 4 observation and [SRC-02]).
