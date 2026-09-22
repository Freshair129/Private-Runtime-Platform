# EV03 test design on a single GPU host

Gate `PRP-NFR-023` (target binding). The procedure assumes two live GPU hosts; this run window has
one (DEV-03). The design below gets the decisive NFR-023 evidence anyway, and records what it
cannot reach.

## Topology used

| LiteLLM alias | `model_info.id` | backend | state |
|---|---|---|---|
| `wp24-litellm-subspike-host-a` | `wp24-host-a` | `http://host.docker.internal:8010/v1` | **permanently down** — nothing listens on 8010 (ConnectionRefusedError verified from inside the proxy container) |
| `wp24-litellm-subspike-host-b` | `wp24-host-b` | `http://host.docker.internal:8000/v1` | **live** — the vLLM runtime |

A permanently-down host A is a stronger version of procedure step 2's "kill A" condition, not a
weaker one: the failure is present for every request instead of only mid-flight.

## What this proves

The NFR-023 question is whether the candidate silently re-routes a request bound to one target onto
another. With host A down and host B live and healthy, a request addressed to
`wp24-litellm-subspike-host-a` must fail. If it returns a completion, that completion can only have
come from host B, which is exactly the hidden failover NFR-023 forbids. One GPU is sufficient to
distinguish those two outcomes.

## What this cannot reach

- Two *live* replicas, so no evidence about balancing or shuffling between two healthy deployments.
- Mid-flight relocation of an in-progress generation onto a second live host.
- Procedure step 4 (second attempt keeping the original deadline and being readmitted) can only be
  observed for the retry-to-the-same-target case, not for a cross-host attempt.

Both are recorded as blockers on EV03 rather than as results.
