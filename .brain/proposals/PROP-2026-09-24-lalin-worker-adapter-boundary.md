# PROP-2026-09-24 — Worker adapter boundary: answers to the five Lalin decisions

**Status:** DECIDED, 2026-09-24. DEC-01 is accepted as [ADR-PRP-014](../../docs/ADR-PRP.md#ADR-PRP-014). DEC-02, DEC-04 and DEC-05 are acknowledged by the repository owner and need no contract change, so the adapter may be built against them when M4 opens. DEC-03 is agreed as written here and is recorded in the mapping table at the WP03 freeze. Nothing here opens M4, and no contract is changed by this document.
**Date:** 2026-09-24
**Author:** Operator (assistant), at the owner's request
**Requested by:** Lalin worker team, "[Lalin → PRP] ขอข้อตัดสิน 5 ข้อ ก่อนเขียน RuntimeInvoker adapter ที่ M4",
their full document `docs/product/REQ-PRP-LALIN-WORKER-ADAPTER.md` (their repository; **not present in
this one**, so their evidence has not been read and none of it is relied on below).
**Related:** `contracts/openapi/prp-worker.yaml` (`x-prp-status: DRAFT`, freezes at WP03) ·
`contracts/openapi/prp-client.yaml` (frozen public contract) · PRP-FR-041 · PRP-FR-042 ·
PRP-NFR-023 · ADR-PRP-013 · WP24 evidence `docs/evidence/wp24/WP24-2026-09-20-run1.json`

## Why this is a proposal and not a decision

Two of the five items change `prp-worker.yaml`, which is `DRAFT` and **freezes at WP03**. WP03 has not
started, and M4 is gated behind it. So DEC-01 and DEC-03 are WP03 freeze items, and DEC-01 needs an
ADR because it changes a field's type. The other three need no contract change and can proceed as
adapter work whenever M4 opens.

Every answer below is checked against what the repository already specifies. **Two of the five
proposals from the Lalin team conflict with the existing contract**, which is the main content of this
document.

---

## DEC-04 — where audio enters and where the result leaves

> **ACKNOWLEDGED 2026-09-24** by the repository owner. The worker pulls from `artifact_grant_url` and the result returns in `InvocationResult`; multipart stays on the client edge. No contract change, and the six-step adapter flow below is the agreed shape. Buildable at M4.

**They proposed:** the worker takes multipart on submit and serves the result from `/output`, but
`prp-worker.yaml` has neither route and the client contract says multipart is waiting on the M4 upload
path. They asked for this to be decided first because it shapes the whole adapter. They are right that
it comes first.

**Answer: the contract already decides this, and the premise is a conflation of two different edges.**

`AsrPayload` in `prp-worker.yaml` carries:

> `artifact_grant_url` — *Time-bound, revocable read grant minted by PRP for this attempt only. The
> worker never receives a client key or storage credential.*

| edge | how bytes move | where it is specified |
|---|---|---|
| **client → PRP** | multipart upload: `POST /v1/audio/transcriptions`, `POST /prp/v1/artifacts` | `prp-client.yaml`; these are the operations still unbound pending the M4 upload path |
| **PRP → worker** | **the worker pulls** from `artifact_grant_url`; the result returns in `InvocationResult.result`, or from `GET /prp/worker/v1/invocations/{attempt_id}` | `prp-worker.yaml` |

The "multipart waiting on M4" note belongs to the **client** edge. It was read as if it applied to the
worker edge. On the worker edge there is no multipart and no `/output` by design, and the design reason
is stated in the field description: the worker must never hold a client key or a storage credential.

**Consequence for the adapter.** The RuntimeInvoker is the bridge, and the Lalin worker needs no change:

1. receive `InvocationRequest` with `payload.artifact_grant_url`;
2. fetch the audio through that grant (time-bound, revocable, attempt-scoped);
3. submit it to the Lalin worker as multipart over the Unix socket;
4. retrieve the result from the worker's `/output`;
5. normalise into `InvocationResult` and return it;
6. delete at the worker, per DEC-05.

Steps 2 and 4 stay **inside** the adapter. Neither contract changes.

---

## DEC-01 — `profile_epoch` is an integer, their `ep-xxxx` is a different epoch

> **RESOLVED 2026-09-24:** accepted as [ADR-PRP-014](../../docs/ADR-PRP.md#ADR-PRP-014) — opaque string, bounded at 128 characters, synthesis rule kept in the ADR. Applied at the WP03 freeze.

**They proposed:** pass their opaque string through as `profile_epoch`, or change the type at WP03
freeze; and not to keep a mapping inside the adapter, because that state is lost on restart.

**Answer: do not map `ep-xxxx` onto `profile_epoch`. They are two different things, and the contract
already has both.**

| field | type today | meaning |
|---|---|---|
| `InvocationRequest.profile_epoch` | `integer`, min 0 | the epoch **the reservation was made against**; the worker rejects a mismatch with `409 EPOCH_MISMATCH` |
| `ExecutionEvidence.runtime_epoch` | `integer`, min 0 | the **actual runtime** epoch at observation |

Their `ep-xxxx` changes every time the engine starts, which makes it a *runtime* epoch. It belongs to
`runtime_epoch`. `profile_epoch` is PRP's reservation epoch and stays an integer: it is what Admission
reserved against, not what the engine happens to be running.

Their `409 TARGET_MISMATCH` maps to PRP's `EPOCH_MISMATCH`.

**The real question is therefore the type of `runtime_epoch`, which is an integer today and cannot
hold `ep-xxxx` either.** Their objection to adapter-side mapping is accepted: a mapping table in the
adapter is lost on restart, which is exactly when an epoch matters.

**Recommendation for WP03 freeze, needs an ADR:** make `runtime_epoch` an **opaque string** that PRP
compares only for equality and never parses or orders.

WP24 evidence supports this independently of Lalin. Candidate A (the selected runtime) **exposes no
epoch at all**: `created` is always `0` in `/v1/models`, and the only value that changes across a
restart is a replica address, which changed on every unrequested recovery
(`docs/evidence/wp24/.../A/EV02/FINDINGS.md`, `.../A/EV03/FINDINGS.md`). Candidate B offered only
`process_start_time_seconds`. An integer epoch assumes a monotonic counter that neither candidate
provides, so PRP will be synthesising the value in both cases and an opaque token is the honest type.

If the owner prefers not to change the type, the fallback is a sibling field carrying the runtime's
own token, with `runtime_epoch` remaining PRP's synthesised integer. That keeps the contract additive,
at the cost of two epoch-shaped fields.

---

## DEC-03 — the proposed fence mapping inverts what `fence_token` means

> **AGREED 2026-09-24** as written: `fence_token` is the content fence, `deadline_at` maps directly, and a lease correlator is added only if the Lalin Admission genuinely needs one. To be recorded in the mapping table at the WP03 freeze.

**They proposed:** `fence_token → lease_id`, `Invocation.deadline_at → deadline_at`, and leaving
`content_fence` empty until there is a use case.

**Answer: `deadline_at` is right; the other two are backwards.**

`prp-worker.yaml` defines `fence_token` as:

> *Content fence for this attempt; required again on cancel*

and `CancelRequest` requires `fence_token`. It is the content fence, already, by name and by use.

| their field | correct mapping | why |
|---|---|---|
| `content_fence` | **`fence_token`** | same concept; it must be populated, not left empty |
| `deadline_at` | `deadline_at` | already present in `InvocationRequest` |
| `lease_id` | **not `fence_token`** | the lease belongs to PRP's admission side. Pass `attempt_id` if their Admission needs a correlator, or add a dedicated field at WP03 if it genuinely needs the lease identity |

Mapping the content fence onto `lease_id` would break cancellation, because cancel is authorised by
`fence_token`, and it would leave the content fence unset — removing the protection that FR-041's
erasure fencing depends on.

---

## DEC-02 — `runtime_uid` and `runtime_id`

> **ACKNOWLEDGED 2026-09-24** by the repository owner. No contract change; the adapter translates the name. Buildable at M4.

**Agreed as proposed.** Pure adapter translation, no contract change on either side.
`InvocationResult.runtime_uid` is the PRP-side name.

---

## DEC-05 — who deletes the payload

> **ACKNOWLEDGED 2026-09-24** by the repository owner, including that the TTL sweep and the erasure tombstone are required by PRP-FR-041 rather than optional, and that the worker is never the retention authority. No contract change. Buildable at M4.

**They proposed:** delete as soon as the result is fetched, with a sweeper as a safety net, and noted
this is a data policy rather than a technical question.

**Answer: agreed on the mechanism, but it is not a free choice and the sweeper is not optional.**

PRP-FR-041 (Retention and erasure) already requires deleting orphan, raw and output data on TTL **and**
on an authorised command, and requires an **erasure tombstone so that a late result cannot resurrect
deleted content**. SRS §"delete ต้อง fence queued/late result/grants" says the same for grants.

So the policy is:

1. the adapter deletes at the worker immediately after a successful fetch — their proposal, accepted;
2. a TTL sweeper runs regardless — **required by FR-041**, not a backstop;
3. deletion is **fenced against late results** through the tombstone, so a worker that returns after a
   delete cannot re-create content;
4. **the worker is never the retention authority.** It holds bytes only for the life of one attempt,
   and PRP decides what survives.

---

## Their three standing notices

All three match positions PRP already holds; recorded here so the adapter work can cite them.

| notice | PRP's position |
|---|---|
| **no retry inside the transport**; re-sending is the coordinator's decision | Exactly PRP-NFR-023. WP24 confirmed the selected runtime has no request-level retry, failover or hedging to disable (`A/EV03/FINDINGS.md` step 4), so PRP classifies every retry itself |
| **D18** `repeated_oom` is not retryable; the worker locks itself and does not return | Maps to FR-042's quarantine path. WP24 found a comparable case: a killed engine returns HTTP 200 with a truncated stream and no error object, which PRP must map to `UNKNOWN` rather than success (`A/EV06/FINDINGS.md`) |
| **D16** results are not stable across runs; never verify by re-sending and comparing | Consistent with WP24 practice: a fixed greedy answer was used only for same-input equivalence between two instances (EV08 step 2), never as cross-run verification |
| **D15** glossary helps clear audio and hurts distant audio | Noted; it is a speech-quality property and belongs to WP10's evidence, not to this boundary |

---

## What the owner is being asked to approve

| item | state on 2026-09-24 | what remains |
|---|---|---|
| DEC-02, DEC-04, DEC-05 | **acknowledged by the owner** | nothing; the adapter may be built against them when M4 opens |
| DEC-01 | **accepted as ADR-PRP-014** (opaque string, 128 characters, synthesis rule in the ADR) | the contract edit itself, carried out at the WP03 freeze per that ADR |
| DEC-03 | **agreed as written** | record `fence_token` as the content fence in the WP03 mapping table; add a lease correlator only if the Lalin Admission requires one |

None of this opens M4, changes the frozen client contract, or alters any WP24 verdict. If DEC-01 is
approved, the ADR should be written before WP03 freezes the worker contract, because after the freeze
it becomes a breaking change.

## What this document does not do

- It does not rely on the Lalin team's own evidence: their document is not in this repository, and
  their production figures (RTF 0.22–0.61, the socket probe, the sample client) have not been verified
  here.
- It does not edit `prp-worker.yaml`, which they did not request and which is not this document's to
  change.
- It records no runtime test result and changes no acceptance status.
