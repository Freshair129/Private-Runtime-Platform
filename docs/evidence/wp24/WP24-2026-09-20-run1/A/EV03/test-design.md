# EV03 test design for candidate A (Xinference)

Gate `PRP-NFR-023` (target binding). Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV03, steps 1–4.
Candidate B's EV03 (`../../B/EV03/`) is the comparison point; there, LiteLLM was the routing layer.
For candidate A the routing layer is **Xinference's own supervisor**, so no proxy is involved.

## What the shipped code says, to be confirmed by running

`core/supervisor.py` `get_model()` resolves a client's `model_uid` to a replica with
`build_replica_model_uid(model_uid, next(replica_info.scheduler))`, where `scheduler` is
`itertools.cycle(active_replica_ids)`.

So **binding is at the model-UID level, and the client cannot address one replica.** With one
replica the choice is trivially deterministic; with two it round-robins. The run has to establish
what that means for PRP: whether a request can silently land on a runtime PRP did not choose, and
whether the candidate retries elsewhere on failure.

## Topology (proposed DEV-08)

Two live targets are needed, and two copies of the 4B `shared_revision` do not fit in 16 GiB
(EV02 measured 10 956 MiB for one, and a second launch died on the host paging file). EV03 for
candidate A therefore uses the built-in **`qwen3` 0.6B** model, which Xinference downloads itself,
so that two runtimes can be live at once on the one GPU.

**This is a deviation from procedure §3 item 1 (same revision for every candidate) and is proposed
as DEV-08.** It is confined to EV03: the question here is *where a request goes*, which does not
depend on which weights are loaded. The `shared_revision` is kept for every other candidate-A
experiment.

## Steps

### Step 1 — does a request addressed to a target land on that target

Two model UIDs (`prp-a-t1`, `prp-a-t2`) from the same built-in model, each with one replica. Then
**20 requests to each UID**, with per-request evidence of who served it:

- the replica address recorded in `/v1/models` and `/v1/workers` per UID;
- the server log lines for each request, which carry the worker address;
- a prompt that makes the answer identifiable per target where possible.

The measurement is the count of requests that were served by the address bound to the UID they were
addressed to.

### Step 2 — a second replica, and what the client can see

One UID relaunched with `replica=2`. Then 20 requests to that UID, recording which replica served
each. Two questions:

- does the response or any header tell the client which replica ran it (candidate B returned no
  routing header at all);
- can a client pin a replica? The code says no, and the run confirms it by trying the documented
  surface.

### Step 3 — failure behaviour: the decisive NFR-023 test

With `replica=2` live, a long generation is started and the **process hosting one replica is
killed** mid-request. Recorded:

- what the client sees: an error, or a completion that silently came from the other replica;
- whether the supervisor re-ran the work elsewhere without being asked (blind failover), read from
  the server log and from a token-count comparison;
- how the surviving replica and the dead one are reported afterwards
  (`/v1/models`, `/v1/workers`).

Then the same with a **slow** target instead of a dead one: a request in flight while the replica is
busy, to see whether the supervisor moves queued work to the idle replica.

### Step 4 — retry / failover / hedging configuration

Everything in the shipped code that could re-send or re-route a request is located and recorded with
its default: the autostart retry fields already found (`retry_interval_seconds`, `max_retries`,
which govern *launching* a model, not a request), the round-robin scheduler, and anything found by
searching for retry, failover, reroute or hedge in the request path. For each, the run records
whether it can be switched off by configuration, and repeats step 3 with it off if it exists.

## What this cannot reach

- **One GPU host (DEV-03)**: both targets are on the same machine, so this is replica binding, not
  host binding. Candidate B's equivalent limit was the opposite: two hosts configured, one of them
  permanently down.
- **DEV-07**: Windows-native transformers backend.
- **DEV-08**: a smaller model than `shared_revision`, for this experiment only.
- ARCH §11's deadline question (step 4, second attempt keeps the original deadline) can only be
  observed if a second attempt happens at all.

## Run precondition

The GPU must be free. Two 0.6B replicas are small, and the model download is roughly 1.5 GB onto F:.
