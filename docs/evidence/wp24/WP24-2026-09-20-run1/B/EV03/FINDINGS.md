# EV03 — target binding, candidate B

Gate `PRP-NFR-023`. Operator observations; no verdict is computed here. Topology and the limits of a
single-GPU run are in `test-design.md`.

## Test 1 — binding holds for a live target

5 requests to `wp24-litellm-subspike-host-b` through the proxy:

| measurement | value |
|---|---|
| requests / successes | 5 / 5 |
| distinct deployments seen | 1 |
| `--expect-deployment` mismatches | 0 |
| upstream requests vLLM actually logged | **5 × `POST /v1/chat/completions` 200** |
| latency ms min / max | 31 / 625 |

Five client calls produced exactly five upstream calls. With `num_retries: 0` there is no retry
amplification, and every request landed on the deployment it was addressed to.

The probe also records that **no `x-litellm-model-id` / `x-litellm-model-api-base` /
`x-litellm-model-group` response header was present** on this build, so binding could not be
confirmed from the documented response headers. It was confirmed instead by correlating with the
upstream engine's own access log. PRP cannot rely on those headers to know which node served a
request on this version.

## Test 2 — the bound target is down, and a live peer exists

`wp24-litellm-subspike-host-a` points at port 8010, where nothing listens (connection refused,
verified from inside the proxy container). The live host B runtime was healthy throughout.

| measurement | value |
|---|---|
| requests / successes | 5 / **0** |
| client-visible status | 500 on all five |
| **requests that reached the live host B** | **0** |

This is the decisive NFR-023 evidence available on one GPU: a request bound to a down target failed
five times out of five, and not one of them leaked onto the healthy peer. No hidden failover, no
silent re-route.

## Test 3 — retry / fallback / hedging switches

The config in `litellm_config.template.yaml` sets `num_retries: 0`, `fallbacks: []`,
`content_policy_fallbacks: []`, `context_window_fallbacks: []`, `enable_weighted_failover: false`,
`routing_strategy: simple-shuffle`, `disable_cooldowns: true`.

Confirmed by execution rather than by reading the config:

- Test 1: 5 client calls → 5 upstream calls. No retry.
- Test 2: 5 failures → 0 requests on the peer. No fallback.
- The client-visible error states it directly: **`Available Model Group Fallbacks=None`**.
- The 25 log lines matching "fallback" are stack-trace frames from
  `litellm/router.py async_function_with_fallbacks`, the code path's name — not fallback attempts.
  Counting that word in logs would have been misleading.

No hedging switch exists in the documented surface, and no behaviour resembling a raced duplicate
request was observed: the upstream count matched the client count exactly in test 1.

## Test 4 — kill the bound runtime mid-generation

A 2000-token generation was started against the live host B and the container was killed 4 s in.

- Client received **HTTP 500 after 4.2 s** — the failure surfaced immediately, it did not hang.
- Message: `Hosted_vllmException - Server disconnected. Received Model Group=...`,
  `Available Model Group Fallbacks=None`.
- No second completion and no replay: one client call, one error.

Caveat recorded honestly: vLLM writes its access-log line when a request *completes*, so the killed
request never produced one. The upstream count for this test is empty **by construction** and is not
itself evidence of zero upstream requests. The no-replay evidence is the client side.

## Cross-cutting: `POST /invocations` without a credential

Confirmed by request, as agreed when this was deferred from EV04. Straight at the vLLM runtime,
no `Authorization` header at all:

| request | result |
|---|---|
| `POST /v1/chat/completions` | **401 Unauthorized** |
| `POST /invocations` | **200 with a real completion** (9 prompt tokens, 2 completion tokens) |

vLLM's `--api-key` is bypassable by changing the path. An unauthenticated caller with network reach
to the runtime can consume GPU capacity. This is no longer a docstring warning or a route-table
inference — it is a measured result, and it means a network policy in front of the runtime is
mandatory for candidate B, not advisory.

## What this run could not reach

Both are properties of having one GPU host (DEV-03), not results:

- No evidence about balancing or shuffling between two *healthy* deployments.
- No evidence about mid-flight relocation onto a second live host.
- Procedure step 4 (a second attempt keeping the original deadline and being readmitted) could not
  be observed, because no second attempt was ever made — which is itself the correct behaviour for
  the retry-disabled configuration under test.
