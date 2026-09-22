# EV05 — atomic multi-process load, candidate B

Gates `PRP-FR-017` / `PRP-FR-018`. Operator observations only; no verdict is computed here. The design is
in `test-design.md`. The runtime launch is in `launch-command.txt`: EV02's launch plus
`VLLM_WSL2_ENABLE_PIN_MEMORY=1` and `--max-num-seqs 4` (DEV-05). Image
`vllm/vllm-openai@sha256:c2914767…51ae1`. Every request went straight to vLLM; LiteLLM was not in the
path. The container was stopped and removed at 2026-09-22T08:14:50Z.

## Step 1 — bypass

| from | target | result |
|---|---|---|
| the host | `127.0.0.1:8000` | OPEN |
| the host | LAN `192.168.1.100:8000`, tailnet `100.76.19.65:8000` | refused |
| an unrelated container (`prp-mvp-litellm`) | host LAN / tailnet | refused |
| an unrelated container (`prp-mvp-litellm`) | `host.docker.internal:8000` | **OPEN** |
| a second LAN machine (step 1b) | host LAN / tailnet | *deferred by the owner, 2026-09-22* |

The re-check against the EV05 container (`step1-recheck-ev05-container.txt`) matches the first
matrix. Publishing on loopback keeps the runtime off the network, but **every process on the GPU host
reaches it**, and one of those paths needs no credential:

- `/invocations` serves inference without the key (EV03).
- `/metrics` answers 200 without the key (re-confirmed here).

The only barrier on this host is "not on this machine". A PRP deployment needs a host-level policy
(firewall rule or a dedicated network namespace) to stop other local processes calling the worker
directly.

## Step 2 — load beyond the limit from several processes

| run | processes × concurrent | HTTP | tokens per request | first token after release (s) | `max_running` | `max_waiting` |
|---|---|---|---|---|---|---|
| A, at the limit | 1 × 4 | 4 × 200 | 256 each | 0.11–0.16 | 4 | 0 |
| B, 3 × the limit | 3 × 4 (3 distinct PIDs) | 12 × 200 | 256 each | 0.16–0.18 / 5.92–5.94 / 11.69–11.72 | 4 | 8 |

- **Excess requests queue; nothing is rejected, and nothing runs beyond the limit.** In run B the 12
  requests started in three waves of four, each wave beginning when the one before finished (done at
  about 5.9 s, 11.7 s and 17.5 s). `running` never exceeded 4 in any of 121 scrapes across both runs.
- **The metrics never over-count.** In no scrape did `running + waiting` exceed the client-side
  upper bound, and `running` never did either (0 of 39 and 0 of 82 scrapes).
- **They can under-count for a moment at the edge of a burst.** In one scrape, 0.144 s after
  release, all 12 requests were already sent but the gauges read 0 running and 0 waiting. At that
  moment the requests were still between the socket and the scheduler (HTTP parsing and
  tokenization). This is the direction FR-018 tolerates: a request not yet counted can never make
  PRP double-hold capacity. It does mean an admission decision taken on the metric alone can admit
  work that is already in flight (ARCH §5: metrics are a signal, not a guarantee).
- The engine's own 10-second log lines agree: `Running: 4 reqs, Waiting: 8 reqs` during run B.
- The queue has no visible bound. Nothing in the launch or the metrics shows a maximum queue
  length. This run did not try to find one.

## Step 3 — can the limit be read back?

| source | `max_num_seqs` found |
|---|---|
| `/metrics` | no. `vllm:cache_config_info` exposes `gpu_memory_utilization`, `block_size` and `kv_cache_max_concurrency="1.71484375"`, but not the sequence limit |
| `/v1/models` | no |
| `/version` | no |
| startup log (`docker logs`) | **yes**: `non-default args: {… 'max_num_seqs': 4}` |

PRP cannot learn the runtime's concurrency limit from any API. It has to take it from the deployment
config it launched with, or scrape the startup log. The KV cache capacity is a second, separate
ceiling: at 8192 tokens per request this cache holds 1.71 requests (`vllm-startup-excerpt.txt`). The
short requests here stayed under it, so the effective limit for long requests can be lower than
`max_num_seqs`.

## Limits of this run

- **FR-017** (durable admission transaction) needs PRP's PostgreSQL admission with fault injection,
  which arrives at M4. AT-017 stays `NOT_RUN`; this run answers only the candidate side.
- **One GPU host (DEV-03)**, so there is no evidence about capacity being counted twice across two
  replicas.
- **Shared host (DEV-04)**: timings are indicative, not capacity figures.
- The queue bound and behaviour under memory pressure were not probed.
