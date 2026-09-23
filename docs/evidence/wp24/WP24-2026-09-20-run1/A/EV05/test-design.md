# EV05 test design for candidate A (Xinference)

Gate `PRP-FR-017` / `PRP-FR-018`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV05, steps 1–3.
Candidate B's EV05 (`../../B/EV05/`) is the comparison point: there the runtime was vLLM in a
container with `max_num_seqs 4`, which queued excess work rather than rejecting it.

The procedure already states the limit this experiment cannot cross: FR-017's durable admission
transaction needs PostgreSQL and fault injection on the PRP side, which does not exist before M4.
WP24 can only examine the candidate's side, so `AT-017` stays `NOT_RUN` regardless of what is
observed here.

Runtime: the EV02 deployment with **`shared_revision`** (the 4B model), one replica, so no new
deviation is needed; EV03's smaller model was specific to that experiment. Auth is left at the
3.4.0 default (on) for step 1's exposure questions, since that is the posture an operator gets.

## Step 1 — can anything reach the runtime except the intended path

Xinference is not one listener. The deployment opens at least four:

| listener | what it is |
|---|---|
| `127.0.0.1:9997` | the REST API, the intended path |
| the worker actor port | xoscar actor pool, chosen at start |
| one port per model replica | the `ModelActor` address EV02 and EV03 recorded |
| the worker **metrics exporter** | a separate port, announced only in the log |

For each, the run records the bind address from the operating system (`netstat`), then tries to
reach it:

1. from **loopback**, which must work for the REST API;
2. from the host's own **LAN address**, which is the single-host stand-in for another machine
   (DEV-03: there is one GPU host; candidate B's equivalent step was deferred for the same reason).
   A listener bound to `127.0.0.1` must refuse it;
3. **directly against a model replica port**, to see whether a local process can bypass the
   supervisor and speak to a model actor;
4. against the **metrics exporter with no credential**, with the server's default auth enabled.
   Candidate B's `/metrics` and `POST /invocations` answered with no credential at all (EV02, EV03),
   so the same question is asked of candidate A's exporter.

Recorded: bind address, result per probe, and whether anything but the REST API can be reached.

## Step 2 — concurrency from several processes at once

**Three separate OS processes** each send a batch of requests to the one model UID at the same
moment, released together, for **12 concurrent requests** in total — the same shape as candidate B's
run so the two can be read side by side.

Measured per request: HTTP status, the time it was sent, first byte, and completion. Measured on
the server: the metrics exporter scraped continuously throughout, for any gauge that reports
in-flight or queued work.

The questions, in the procedure's words: does the candidate **queue, reject, or over-accept**; and
does its own metric **agree with what is really in flight**. The upper bound used for the metric
check is the client-side count of requests that had been sent but not yet returned — the same
bound candidate B's run used, so an over-count is provable rather than inferred.

## Step 3 — what controls concurrency, and can PRP read it back

The shipped code and the launch surface are searched for the settings that govern concurrency and
queueing for the transformers backend (the analogue of vLLM's `max_num_seqs`), along with anything
the worker uses to bound launches, which the EV02 log already hinted at (`active: 1/5, queued: 0`).
For each: its default, whether PRP can set it, and **whether the current value can be read back from
the API** — the gap that made candidate B's admission signal one-way.

## What this cannot reach

- **FR-017 durable admission** is PRP-side and out of scope before M4, as the procedure states.
- **One GPU host (DEV-03)**: the LAN probe is made from the host's own non-loopback address, not
  from a second machine. It proves a listener refuses a non-loopback address; it does not prove
  network isolation between machines.
- **DEV-07**: Windows-native transformers backend, so queueing behaviour is that backend's, not
  vLLM's. No timing comparison with candidate B is valid.
