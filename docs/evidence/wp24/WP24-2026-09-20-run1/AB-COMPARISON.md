# WP24 — candidate A versus candidate B, side by side

A reading aid for the reviewer, compiled on 2026-09-24 from evidence already merged into
`docs/evidence/wp24/WP24-2026-09-20-run1.json` and the artifact tree beside it. It introduces no new
measurement and **states no verdict**: dispositions and the candidate selection belong to the
reviewer, and every experiment status in the run record is still `NOT_RUN`.

**How this file was checked.** Every numeric assertion in it was matched against the run record and
the 160 files of the evidence tree: **134 distinct figures, all traced to source**, including the one
that needed expansion (`171 s` is `init_engine_seconds: 171.0` in candidate B's EV02 measurements).
Four qualitative claims that would mislead if wrong were traced individually to the record: candidate
B's `POST /invocations` answering without a credential, its startup telemetry to `stats.vllm.ai`, the
`/key/info` read-back addressing modes, and that candidate B's upgrade and rollback were never
attempted while candidate A's were. Sentences outside those checks are a summary of the cited
evidence and should be read against the linked artifacts, not in place of them.

Source of every figure below: `docs/evidence/wp24/WP24-2026-09-20-run1.json` and the evidence tree
`docs/evidence/wp24/WP24-2026-09-20-run1/{A,B}/EVnn/`. Nothing here is interpolated; where a number
exists for one candidate only, that is stated.

- Candidate A = Xinference-managed runtimes (xinference 3.4.0, transformers backend, Windows-native).
- Candidate B = independent vLLM (vLLM 0.29.0 in a Linux container), plus LiteLLM v1.90.2 as a
  key/proxy layer in EV03 and EV04 only.
- **No disposition or verdict is proposed here.** Every `gate_verdicts` entry in the record is
  `NOT_RUN` (EV07: `BLOCKED`); the `disposition_hint` fields are explicitly operator suggestions.

---

## DEV-07 WARNING — timing and throughput between A and B are NOT comparable

The run record carries deviation **DEV-07** (status OPEN):

> "Candidate B ran vLLM inside a Linux container on Docker; candidate A runs natively on Windows
> with the transformers backend, because vLLM has no Windows build and the only WSL distro on this
> host is Docker's own. The model revision, the weights and the GPU are the same."
> Mitigation: "Any measurement of time or throughput between candidates A and B is not comparable
> and must not be read as one."

Consequences a reviewer must hold throughout this document:

1. **Every row marked `NOT COMPARABLE (DEV-07)` below is a within-candidate figure only.** Cold
   start, model load, restart, recovery, cancel latency, rejection latency and tokens/throughput
   must never be read as A-vs-B.
2. Additional deviations that narrow the comparison further:
   - **DEV-03** (OPEN): only one GPU host existed in the run window, so no real A/B two-host
     replica pair was ever launched; every EV02/EV03/EV05 cross-host question is unrun.
   - **DEV-04** (OPEN): host B was not a clean host during EV02 (unrelated Docker stack, Ollama,
     Windows desktop shell holding ~3 596 MiB VRAM before launch). B's timing/capacity figures are
     shared-machine figures.
   - **DEV-05** (OPEN): B's EV05 ran with `--max-num-seqs 4`, not the vLLM default.
   - **DEV-06** (OPEN): the EV08 import ran on the same host as the export (both candidates).
   - **DEV-08** (OPEN): A's EV03 used a built-in qwen3 **0.6B** model, not `shared_revision`
     (A's EV02 measured 10 956 MiB for one 4B replica; a second launch failed on the Windows
     paging file). So A's EV03 recovery seconds are for a 0.6B model.
   - **DEV-02** (OPEN): B ran first and A afterwards; the procedure's ordering was reversed.
3. Only **qualitative / structural** properties (what an API exposes, what it protects, whether a
   replay happened, what must be built by PRP) are comparable across candidates.

---

## EV02 — Real A/B registration
**Question (record):** "protected endpoint auth, model profile, distinct physical GPUs and epochs"
— gate FR-010…FR-015. Status: both `NOT_RUN`.

| Aspect | Candidate A (Xinference) | Candidate B (vLLM) |
|---|---|---|
| Physical GPU reported | device **index only**: `accelerators: ["0"]`; no GPU UUID | **no** endpoint exposed a UUID. `nvidia-smi` on the Windows host matched **0** runtime processes (WSL2 paravirtualisation); inside the container it reported `GPU-38430611-f42d-0296-a887-d75649b21f25`, pid 131 with process_name `[Not Found]`, memory `[N/A]` |
| Restart / epoch signal | replica address changed `127.0.0.1:62147` → `127.0.0.1:63318`; **57** other identifiers unchanged; no epoch field, `created` is 0 | `created` and `permission[0].id` are **not** an epoch: three consecutive `/v1/models` calls on one origin returned three different `modelperm-*`. Only `/metrics process_start_time_seconds` is stable (1.78994622059e9 → 1.78994655054e9 after restart) |
| Two origins onto one runtime | n/a | ports 8000 and 8001 to one container give a different `created` and `permission[0].id` per origin — a consumer trusting the listing counts **one** runtime as **two** capacities |
| Auth on the endpoints probed | auth **on by default** (documented as opt-in); `/v1/models`, `/v1/model_registrations/LLM`, `/v1/workers`, `/v1/supervisor` → **401 with a WWW-Authenticate challenge** (4 endpoints); only `/v1/cluster/auth` and `/v1/admin/setup/status` open. `XINFERENCE_AUTH_ADVANCED=0` removes all auth | `/v1/models` → **401 but no challenge header**; `/metrics` → **200, 52 294 bytes** with no credential at all (`--api-key` does not cover it) |
| Same alias, different profile | **refused: HTTP 400** "Model prp-typhoon25-qwen3-4b already registered"; a second name over the same weights was accepted and kept separate | accepted; `max_model_len` changes under the same id. vLLM has **no cross-process model registry**, so two instances of one alias are never merged or compared |
| Model revision verifiable from API | (not measured for A) | **no** — listing returns only id/root/max_model_len/owned_by/created/permission. Verified out of band: `tokenizer.json` sha256 `aeb13307…dae4`, `chat_template.jinja` sha256 `64f85b19…c326`, two shards = 8 044 982 000 bytes (7.49 GiB) |
| Cold start | 44 s to first 200; model load **100 s**; VRAM after load **10 956 / 16 311 MiB**; warm chat completion 1.4 s — **NOT COMPARABLE (DEV-07)** | cold start to `/health` 200 **280 s**; warm restart **130 s**; load weights **64.72 s**; model loading **71.57 s / 7.64 GiB**; init engine **171 s**; torch.compile **27.73 s**; recompile after max_model_len change **22.13 s**; VRAM used when ready **14 249 MiB** (12 447 free before launch, 3 596 held by the desktop shell) — **NOT COMPARABLE (DEV-07, DEV-04)** |
| Capacity ceiling | second UID launch **failed before start** (Windows paging file, os error 1455) — capacity counting **unobserved** | KV cache **10 576 tokens**, **661** GPU blocks, max concurrency **1.29** at max_model_len 8192 and **2.58** at 4096 — **NOT COMPARABLE (DEV-07)** |
| Inference smoke | 1.4 s warm chat completion | 254 ms wall clock, 25 prompt / 5 completion tokens — **NOT COMPARABLE (DEV-07)** |
| Artifacts | `docs/evidence/wp24/WP24-2026-09-20-run1/A/EV02/` (FINDINGS.md, `ev02_gpu_binding_A_*.json`, `ev02_probe_A_A_*.json`, `ev02_restart_identity_A_A_20260922T201156Z.json`, negative-test1/2, launch-command.txt, xinference-server-excerpt.log) | `docs/evidence/wp24/WP24-2026-09-20-run1/B/EV02/` (before/ and after/ probes, `ev02_gpu_binding_B_20260920T222717Z.json`, `ev02_restart_identity_B_B_20260920T223039Z.json`, `nvidia-smi-*-inside-container.txt`, `negative/` set, vllm-startup-success.log, two failed launch logs) |

**Relative strength on this gate:** candidate **A is stronger on the identity/registration
properties** — it reports placement at all (device index, per-replica address, worker→replica map),
it gives a usable restart signal (address change against 57 stable fields), it refuses a duplicate
alias with a different profile, and it challenges four endpoints with 401 + WWW-Authenticate.
Candidate B reports neither physical GPU nor stable identity through its authenticated API, and its
only identity source (`/metrics`) is the one endpoint its credential mechanism does not protect.
Both still require PRP to supply its own epoch and its own index→UUID join. All timing rows:
**not comparable (DEV-07)**.

---

## EV03 — Target binding
**Question (record):** "request lease matches actual node, including framework routing/retry"
— gate NFR-023. Status: both `NOT_RUN`. Note **DEV-08**: A used a 0.6B model here.

| Aspect | Candidate A (Xinference, supervisor + replicas) | Candidate B (LiteLLM v1.90.2 in front of vLLM) |
|---|---|---|
| Binding held | **40 / 40** requests served by the UID addressed; **0** crossed to another UID | **5 / 5** requests succeeded on the addressed deployment; vLLM's access log recorded exactly **5** upstream POSTs; **1** distinct deployment; **0** mismatches |
| Retry amplification | none: no request-level retry, failover or hedging exists in the request path at all | none with `num_retries 0`: 5 client calls → 5 upstream calls; no raced duplicate observed |
| Silent failover to a healthy peer | **not applicable** (single host): the analogous case is a dead replica — requests round-robined to it fail **400 "Model not found"** / **500 "Model is in stopping state"** and are **not** re-routed to the healthy replica | **decisive negative test**: 5 requests to a down target (port 8010, connection refused) → **5 × client-visible 500**, **0** requests reached the live peer. Error body says `Available Model Group Fallbacks=None` |
| Replica visibility to the client | client cannot choose or see a replica: with `replica=2` the supervisor alternated strictly 0,1,0,1 over **20** requests, token split **48 / 51**, no response field names the replica, `/v1/models` shows **1** address for a 2-replica UID | routing headers `x-litellm-model-id` / `-api-base` / `-model-group` **absent** on this build → binding had to be confirmed from the upstream engine access log |
| Mid-flight kill | streaming request ended **HTTP 200 after 1 chunk** as if normal; **0** tokens regenerated on the killed replica and **0** on the other | client got **HTTP 500** after **4.215 s** ("Server disconnected"); **0** replayed completions. Caveat recorded: vLLM logs on completion, so the upstream count is empty by construction |
| Unrequested relocation | supervisor relaunches the dead replica by itself in **35 s and 40 s** (0.6B; EV06 measured 131.8 s on the 4B) and each recovery gives a **new address**; auto-recreate is **unbounded** by default (bounded only by `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT`) — **NOT COMPARABLE timing (DEV-07, DEV-08)** | vLLM does not relaunch itself (see EV06) |
| Unauthenticated inference path | not applicable at this layer | **`POST /invocations` returns 200 with a real completion (9 prompt / 2 completion tokens) with no credential**, while `/v1/chat/completions` returns 401 |
| Error shape for PRP | 400 / 500 with vendor text | connection refused, mid-flight disconnect and genuine internal error **all** surface as **HTTP 500** (never 502/503/504); body leaks `host.docker.internal:8010`, `192.168.65.254`, `Hosted_vllmException`, internal group alias |
| Latency | (not measured for A in EV03) | min **31 ms**, max **625 ms** — **NOT COMPARABLE (DEV-07)** and no A counterpart exists |
| Artifacts | `…/A/EV03/` (FINDINGS.md, step1-binding-40-requests.json, step2-replica-roundrobin-20-requests.json, step3a/3b kill json, worker-metrics-sample.txt) | `…/B/EV03/` (FINDINGS.md, test1-live-host-b.{result,requests}.json, test1-upstream-request-count.txt, test2-down-host-a.*, test4-kill-mid-flight.txt, client-visible-error-bodies.txt, proxy-retry-log-summary.txt, invocations-no-credential.txt) |

**Relative strength:** **partly not comparable.** Both showed binding holding on every request and
no blind replay. B produced the only direct "a request bound to a down target is not silently
re-routed onto a healthy one" measurement (0 requests reached the live peer) — the property
NFR-023 asks about — but through a proxy layer that is not in A's stack. A produced the only
evidence about replica-level behaviour (round-robin invisibility, unrequested relocation with a
changing address). B carries an extra hard finding against it: an unauthenticated inference path
(`/invocations`) and vendor topology in client-visible error bodies. A carries an extra hard finding
against it: relocation PRP never asked for, with an unbounded auto-recreate. The two sides did not
run the same test, so a straight "stronger" call is not available from the evidence; the
recovery-second figures are **not comparable (DEV-07 and DEV-08)**.

---

## EV04 — Identity / key semantics
**Question (record):** "hash/verifier or conforming authority, no reveal, scoped listing/jobs/files/revoke"
— gate FR-003…FR-009. Status: both `NOT_RUN`. B is measured in **two layers** (bare vLLM, then LiteLLM).

| Aspect | Candidate A (Xinference) | Candidate B — bare vLLM / LiteLLM |
|---|---|---|
| Key storage | **reversible**: `GET /v1/admin/keys/{id}/reveal` → **200 and the plaintext key matched the issued key**. Stored as sha256 **and** AES-encrypted; the AES key (`encryption_key`, 64 bytes) and `jwt_secret_key` sit in the **same directory** as `auth.db` | vLLM: sha256 + `compare_digest` in process, but plaintext must be given via `--api-key`/`VLLM_API_KEY` and `docker inspect` returned the exact key in plaintext. LiteLLM: `LiteLLM_VerificationToken.token` = **64 hex chars = sha256(plaintext)**; `/key/info` by hash and `/key/list` contain **no** plaintext |
| Plaintext in list/get routes | **False** (plaintext only on the dedicated reveal route) | LiteLLM `/key/info` by hash: **False**; `/key/list`: **False**. But the documented `GET /key/info?key=<plaintext>` put the plaintext in the URL and it appeared in the proxy log **exactly once** |
| Scope vocabulary present | model permission, `expires_at`, `enabled`, `rate_limit_max_failures`, `rate_limit_window_seconds`, `rate_limit_ban_seconds`; user scopes: admin, keys:create, keys:manage, users:manage, models:list/read/write/register, cache:list/delete, virtualenv:list/delete | vLLM: `api_key` is a `list[str]` with **no scope of any kind**. LiteLLM: `models`, `expires`, `max_budget`, `tpm_limit`, `rpm_limit`, `key_alias`, plus team / organization / project / budget on `/key/info` |
| Scope vocabulary absent | **organization, application, token or cost quota** | vLLM: everything. LiteLLM: covers org/team/project/budget |
| Tenant isolation on read | non-admin: **403** on `GET /v1/admin/keys` and **403** on revealing another key | virtual key: **403** on `/key/list`, **401** on `/key/generate`, **200** on `/v1/models` — but virtual key A reading `/key/info?key=<hash of key B>` returns **200** with B's alias, models, expiry, budget and spend. **Not scoped per key** |
| Revocation | key rejected **0.037 s** after delete; deleted user's token **0.012 s**; refresh token → **401**; an access token issued before the revoke keeps working (separate credential) | vLLM: **no revoke API at all** (restart the server). LiteLLM: `POST /key/delete` 200, rejected on the **first poll, 0.000 s** at a 0.2 s polling interval, **1** poll attempt |
| Auth coverage of paths | 401 on the admin/model routes; `/metrics` open (see EV05) | vLLM authenticates only `('/v1','/v2','/inference','/cohere')`; **16** routes outside it, incl. `POST /invocations`, `/tokenize`, `/detokenize`, `/metrics`, `/load`, `/version` |
| Bootstrap independence (FR-001) | first admin via single-shot `POST /v1/admin/setup` against a local sqlite; **second attempt 403**; needs `XINFERENCE_AUTH_JWT_SECRET_KEY` and `XINFERENCE_AUTH_ENCRYPTION_KEY` | proxy + Postgres brought up from nothing with a generated master key; no business database involved. Proxy `/health/liveliness` 200 **21 s** after compose up; key generate **200 in 156 ms**; `LiteLLM_VerificationToken` rows after cleanup: **0** |
| Integration trap recorded | `POST /token` takes a JSON body, not OAuth2 form encoding; a form-encoded login returns **500** with a JSON decode error | the tool's own `plaintext_reappeared_any_channel: true` was a **false positive** (the script passed the plaintext as a query parameter) — RCA `.brain/rca/RCA-2026-09-21-ev04-keys-readback-false-positive.md`; **no FR-005 verdict may be taken from it** |
| Artifacts | `…/A/EV04/FINDINGS.md`, `ev04_a_probe_result.redacted.json`, `xinference-ev04-server-excerpt.log` | `…/B/EV04/FINDINGS.md`, `ev04_keys.result.json`, `ev04_key_generate.redacted.json`, `ev04_readback_attempts.redacted.json`, `ev04_key_delete.redacted.json`, `litellm-image-digest.txt`, plus the RCA |

**Relative strength:** **split, and not a like-for-like pair.** Against *bare vLLM*, candidate A is
clearly stronger: A has real user scopes, isolated listing and measured immediate revocation, while
bare vLLM has no scopes, no revoke API and guards only four path prefixes. Against *LiteLLM*,
candidate B's layer is stronger on the property the ADR cares most about: LiteLLM **stores and
serves keys as hashes**, whereas candidate A's store is **reversible by design** (reveal route plus
the AES key beside the database). Both revoke effectively instantly (A 0.037 s measured; LiteLLM
0.000 s at a 0.2 s poll — different measurement methods, not a ranking). Both have a disclosure
condition PRP must carry (A: protect the auth directory; B: never address `/key/info` by plaintext,
and do not trust it for tenant isolation).

---

## EV05 — Atomic multi-process load
**Question (record):** "no duplicated capacity/quota holds; no bypass direct worker"
— gate FR-017, FR-018. Status: both `NOT_RUN`. Note **DEV-05** for B's limit value.

| Aspect | Candidate A (Xinference) | Candidate B (vLLM) |
|---|---|---|
| Listeners opened | **four**: REST API 9997, worker actor 37149, model replica actor 60421, worker metrics exporter 60308 — all bound to 127.0.0.1 | one published port 127.0.0.1:8000 |
| Non-loopback reachability | LAN 192.168.1.100, tailnet 100.76.19.65 and WSL switch 172.20.192.1 **all refused** (ConnectionRefused 10061) on all four listeners | refuses LAN and tailnet from the host and from an unrelated container, **but** an unrelated container reaches it through `host.docker.internal` |
| Unauthenticated surface | REST API **401**; `/metrics` on the API port **200**; whole worker exporter **200**, revealing `model_name`, `model_uid`, `worker_address`, `gpu_index`, `replica_index`, `xinference_home`, `model_last_load_duration_seconds`. **Telemetry only — no inference path** | `/metrics` **and** `POST /invocations` answer without a key; `/invocations` serves **real inference** (measured in EV03) |
| Raw bypass of the supervisor | raw HTTP to the actor ports → `RemoteDisconnected` (the actor protocol is not HTTP); the sockets are still open to any local process | any local process with reach can call the runtime |
| Behaviour over the limit | default `request_limits` = **-1 (unlimited)**: 12 concurrent from 3 processes → **12 × 200**, all finishing together at **29.7 s**. With `request_limits 4`: **4 × 200 + 8 × 429** ("Rate limit reached for the model") — the candidate can be configured to **reject** | with `max_num_seqs 4` (DEV-05): 12 concurrent from 3 processes → **12 × 200**, started in **3 waves of 4** (first-token waves at 0.159/0.184, 5.919/5.943, 11.69/11.715 s). Excess is **queued, not rejected**; max running **4**, max waiting **8** |
| Over-count of the in-flight gauge | **0 of 199** and **0 of 185** scrapes exceeded the client-side upper bound; peaks exactly 12 and exactly 4 | **0** scrapes above the limit, **0** above the client upper bound; **1** scrape *below* the lower bound (0 running / 0 waiting 0.144 s after release) — an **under-count** at the burst edge |
| Rejection latency | **6.525 s** — the 429 arrives only when the running batch completes; a rejected attempt still burns the caller's deadline — **NOT COMPARABLE (DEV-07)**, and B has **no counterpart figure** because B never rejects | not applicable: no rejection path exists to exercise |
| Limit readable back | **not** from `/v1/models` (21 fields); only `xinference:model_request_limit` on the **unauthenticated** exporter. Other controls env-only: `XINFERENCE_BATCH_SIZE 32`, `XINFERENCE_BATCH_INTERVAL 0.003`, `XINFERENCE_MAX_CONCURRENT_LAUNCHES 5` | `max_num_seqs` readable from the **startup log only**; `/metrics vllm:cache_config_info` gives a second ceiling `kv_cache_max_concurrency` **1.71** at 8192 tokens |
| Queue bound | no internal queue bound probed | **no bound visible and none probed** |
| Artifacts | `…/A/EV05/` (FINDINGS.md, step1-listener-exposure.json, step2a/2b/2c json, worker-metrics-unauthenticated-sample.txt) | `…/B/EV05/` (FINDINGS.md, `ev05_admission_load_B_run-A-at-limit_*.json`, `…run-B-over-limit_*.json`, step1-reachability-matrix.txt, metrics-info-and-queue-gauges.txt, vllm-startup-excerpt.txt) |

**Relative strength:** **A is stronger on FR-018 as evidenced.** A can be configured to **reject**
over-limit work (4 × 200 + 8 × 429), which is the admission signal the gate asks for; B queues the
excess and gives no rejection at all. Neither candidate over-counted its in-flight gauge; B's gauge
additionally **under-counts** at the burst edge. A's unauthenticated surface is telemetry only,
B's includes a working inference path — a difference in kind, not degree. Both need PRP to hold the
limit in its own config and to firewall the runtime. **FR-017 is not dispositioned from either
candidate**: the durable admission transaction is PRP-side M4 work. The 6.525 s rejection latency is
a single-candidate figure and is **not comparable (DEV-07)**.

---

## EV06 — Timeout / restart
**Question (record):** "UNKNOWN/QUARANTINED evidence, no blind inference replay"
— gate FR-020, FR-021, FR-022. Status: both `NOT_RUN`.

| Aspect | Candidate A (Xinference) | Candidate B (vLLM) |
|---|---|---|
| Cancel — streaming | socket close stopped compute in **3.53 s** | **0.193 s** to idle |
| Cancel — non-streaming | socket close stopped **nothing**: **61.5 s** more compute and all **900** tokens produced into a socket nobody read | **0.194 s** to idle |
| Cancel — queued request | (not measured for A) | queue empty **0.084 s** after close; the cancelled request produced **0** tokens; running fillers unaffected |
| Explicit cancel API | **yes**: `POST /v1/models/{uid}/requests/{request_id}/abort` → 200 `{"msg":"DONE"}` in **2.295 s**, idle **0.5 s** later; needs a client-supplied `request_id` | **no** request-status or cancel API on chat completions and **no `x-request-id`** header. The Responses API has `GET /v1/responses/{id}` and `POST /v1/responses/{id}/cancel`, but background mode returns **400** without `VLLM_ENABLE_RESPONSES_API_STORE=1` (not enabled) |
| Client-visible ending on engine kill | **HTTP 200, one chunk, no `[DONE]`, no error object** — indistinguishable from success by status code | **HTTP 200 with an in-stream error object (InternalServerError code 500) and `[DONE]`, no finish_reason**; container exited; `/health` failed **1.01 s** after the kill |
| Client-visible ending on restart | `ConnectionResetError` WinError 10054; API answered again after **52.8 s** | HTTP 200, **no finish_reason, no error object**; `[DONE]` present in only **one of two runs**. On SIGTERM vLLM aborts in-flight work (mode=abort, timeout 0) rather than draining |
| Blind replay | **none** in any case: `generate_tokens_total` flat in every window, against a control that moved 0 → 11 tokens | **none**: `replay_window_gen_tokens_rise_all_cases` **0**, `replay_window_max_running_all_cases` **0** across 30 s windows |
| Self-recovery | supervisor relaunches the replica **without being asked**; UID served again **131.8 s** after the kill; during recovery: 500 "is in stopping state" then 400 "not found" — **NOT COMPARABLE (DEV-07)** | vLLM **does not restart its own engine**; recovery needs an external supervisor. Ready **73.2 s / 78.6 s** after `docker start`; **93.2 s / 98.1 s** after `docker restart` — **NOT COMPARABLE (DEV-07)** |
| State after a full restart | supervisor restart **loses all cluster state**: registrations `['prp-typhoon25-qwen3-4b'] → []`, models `['prp-a-llm'] → []`, request → 404 "Available model uids: []" (registered with `persist false`) | container keeps its filesystem; nothing running; new `process_start_time_seconds` |
| Orphans | force-killing the supervisor **orphaned the worker**, which held the model actor sub-pool with **10 610 MiB** of VRAM and recreated it within ~1 min; killing the port-9997 listener kills the API process only; VRAM fell to **2 753 MiB** only after the orphaned worker itself was killed | container exit takes the process with it; no orphan case recorded |
| Stale in-flight gauge | **30 s after the engine kill `model_serve_count` still read 1** with nothing running | not reported as stale here |
| Artifacts | `…/A/EV06/` (FINDINGS.md, case-a-client-cancel-and-abort.json, case-a-non-streaming-cancel-timed.json, case-b-c-engine-kill-and-supervisor-restart.json, two server excerpts) | `…/B/EV06/` (FINDINGS.md, `ev06_interrupt_B_{cancel-stream,cancel-nonstream,cancel-queued,restart,kill-engine}_*.json`, step3-responses-api-probe.txt, `superseded/` first runs) |

**Relative strength:** **mixed, and the timings are not comparable (DEV-07).**
- On **cancel semantics** B is stronger structurally: closing the socket stops compute for both
  streaming and non-streaming work, while on A a non-streaming cancel stops nothing and 900 tokens
  were burned; A compensates only through an explicit abort route needing a PRP-generated
  `request_id` — a route B does not have on chat completions.
- On **failure signalling** B is stronger: it emits an in-stream error object on an engine kill,
  where A emits nothing distinguishable from success.
- On **self-recovery** the two differ in kind: A recovers unasked (and so relocates state PRP did
  not authorise, plus leaves a VRAM-holding orphan); B does not recover at all and needs a
  supervisor PRP supplies.
- On **no blind replay** — the gate's core question — **both passed the observation equally**: zero
  regenerated tokens in every window.

---

## EV07 — Mixed chat/speech — BLOCKED for both candidates
**Question (record):** "resident profile + actual placement, no silent unload or OOM under admitted load"
— gate FR-018, FR-044. Status: **BLOCKED** for A and B; `gate_verdicts` = `BLOCKED` on both.
Blocker (identical text for both): *"speech out of WP24 scope; blocked until WP10 (owner decision
2026-09-20)"* — `scope_decisions.speech_in_scope` is false and the procedure forbids substituting a
stub.

| Aspect | Candidate A | Candidate B |
|---|---|---|
| EV07 itself | **did not run** | **did not run** |
| Candidate-side partial (owner-approved 2026-09-24) | **yes** | **none** — no measurements, no observations, **no artifacts** |
| Residency over idle | **41** samples at 30 s over **20 minutes**; uid present in **every** sample; VRAM first/last **8 820 → 9 235 MiB**, min/max **8 808 / 9 237 MiB**; **0** silent unload events; idle-unload mechanism in code: **none exists** | not measured |
| Placement control | `XINFERENCE_LAUNCH_STRATEGY` default `IDLE_FIRST_LAUNCH_STRATEGY`, **skipped entirely when `gpu_idx` is passed**; `POST /v1/models` has **no documented request body** in `/openapi.json` | not measured |
| Auto-recover | **unbounded** by default; boundable via `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT`, **not disableable** | not measured |
| Orphan reaping | after a supervisor kill the orphan held **9 235 MiB**; a fresh instance (up in 51.6 s) left VRAM unchanged, logging "23 GPU-occupying process(es) found, none are vLLM orphans" — the shipped cleanup matches PPID 1 + a vLLM-like cmdline and **never fires** on this deployment | not measured |
| Operational hazard | **2** launches stalled ~10 min each with no VRAM and no error on an `XINFERENCE_HOME` reused after EV06's kills; the same launch on a fresh home succeeded in **51 s**. Log rotation failed at the date rollover (`PermissionError WinError 32`) | not measured |
| Artifacts | `…/A/EV07/` (FINDINGS.md, residency-idle-20min.json, stalled-launch-log-excerpt.log, startup-cleanup-log-excerpt.log, startup-orphan-cleanup-test.json, test-design.md) | **none** |

**Relative strength: not comparable.** EV07 did not run for either candidate, so the gate yields
nothing on either side. Candidate A additionally carries an approved **partial** on residency,
placement and orphan cleanup; candidate B has **no EV07 data at all**, so the absence of an
equivalent B figure is an absence of measurement, **not** evidence that B behaves differently.

---

## EV08 — Adapter / exit
**Question (record):** "public schemas unchanged; config export; key rotation plan; deletion fences preserved"
— gate NFR-024. Status: both `NOT_RUN`. Note **DEV-06** (same-host import) applies to both.

| Aspect | Candidate A (Xinference) | Candidate B (vLLM) |
|---|---|---|
| Vendor identifiers in the public contract | **0** occurrences in `prp-client.yaml`; inventory unchanged at **12 paths / 14 operations**, info.version 0.3.0; `validate_docs` **0 errors** | **0** vendor name matches; inventory unchanged; the public name maps to ModelProfile/RuntimeDeployment behind the adapter |
| Leakage in success bodies | completion body: **no vendor words** (the `model` field echoes the PRP-chosen `model_uid`); header `server: uvicorn`; model listing carries `pytorch, qwen, transformers, typhoon, xinference` | `server: uvicorn`; `model` = served-model-name; `chatcmpl-` ids; **`system_fingerprint vllm-0.29.0-de711e39` (vendor and version)**; extra fields `kv_transfer_params, ec_transfer_params, metrics, prompt_logprobs, prompt_text, prompt_token_ids, service_tier, routed_experts, stop_reason, token_ids`…; `/v1/models` `owned_by vllm`, `root /models`, `permission[]` |
| Leakage in error bodies | **worst finding of the gate**: an error carries the internal **actor address**, the **pid** and **every model uid on the cluster** | error bodies carry **no host, port or stack trace**; but the **401 body is a bare string** while 400 and 404 are objects → PRP needs a normalised mapping |
| Config export | **5 declarative files** (`environment.env`, `launch-params.json`, `model-registration.json`, `reference-from-source.json`, `state-files-inventory.txt`); **no secrets** | redacted export; **no plaintext key** (the key is supplied at launch); this revision has no `generation_config.json` |
| Import fidelity | imported instance answered in **31.2 s**, launched in **49.3 s**; matched source on the `/v1/models` field set, the full model record (except address and `created`), a fixed greedy answer (2, 3, 5, 7, 11) and usage **18 / 14 / 32** — **timing NOT COMPARABLE (DEV-07)** | fingerprint equal on **4/4** fields; ready **223.2 s**; matched on startup args, `/v1/models`, `cache_config_info` and a fixed greedy answer — **timing NOT COMPARABLE (DEV-07)** |
| Key rotation | **fully online**: both keys work during overlap, deleted key refused **0.027 s** later, new key 200 / old key 401, **restart required: False** | **relaunch per key change**: overlap (no key 401 / old 200 / new 200) then new-only (old 401 / new 200); relaunch ready **226.1 s** and **217.1 s** — **timing NOT COMPARABLE (DEV-07)**. `VLLM_API_KEY` is visible in `docker inspect` (**True**); via a `--config` YAML it is **not** (**False**); no key in `docker logs` at any stage |
| Job data in vendor datastores | **57 562** files scanned; **5** changed after the marker request; **0** contained the marker. All datastores are local sqlite under `XINFERENCE_HOME` — nothing leaves the host | marker found in **0** files and **not** in docker logs across **1 292** search roots. **But**: `usage_stats.json` and a telemetry post to **`https://stats.vllm.ai`** at startup and every **600 s** — the opt-outs were **not** set in this launch; actual egress **not captured** |
| Artifacts | `…/A/EV08/` (FINDINGS.md, `config-export/` 5 files, step2-import-on-fresh-home.json, steps-1-3-4-leakage-rotation-datastores.json, xinference-ev08-import-excerpt.log) | `…/B/EV08/` (FINDINGS.md, `ev08_export_B_src_*.json`, `ev08_fingerprint_B_{src,import}_*.json`, `ev08_compare_B_src-vs-import_*.json`, `ev08_key_check_B_{src-env-single,import-env-single,overlap,new-only}_*.json`, `ev08_launch_B_*`, `ev08_datastore_scan_B_src_*.json`, `ev08_leak_scan_B_src_*.json`, step4-usage-stats.txt, `superseded/`) |

**Relative strength:** **A is stronger on the exit mechanics, B is stronger on error-body hygiene.**
A's rotation is online with **no restart** (B needs a relaunch per key change) and A's datastores are
entirely local with **no telemetry egress path**, where B posts host/config telemetry to an external
endpoint by default unless `VLLM_NO_USAGE_STATS=1`/`DO_NOT_TRACK=1` is set. Against that, A's
**error bodies are the worse leak** (internal address, pid, every model uid on the cluster — the
adapter must replace them wholesale), while B's errors leak no topology and its leakage is confined
to headers, ids and `system_fingerprint`. Both exported and re-imported to a matching instance, and
both kept the public contract free of vendor identifiers. Both import timings are **not comparable
(DEV-07)**, and both imports were same-host (**DEV-06**).

---

## Operator cost

### Deploy steps and time

| | Candidate A | Candidate B |
|---|---|---|
| Prerequisites (once per host, **not timed** in either case) | **3**: Python 3.12 + venv; NVIDIA driver and CUDA-capable GPU; weights on local disk (**7.51 GiB**) | **3**: NVIDIA driver + GPU-capable container runtime; `docker pull` of the pinned image (**30.5 GB**); fetch and hash-verify the model revision (**7.49 GiB**) |
| Per-deployment steps performed | **7** | **5** |
| The step that surprises the operator | step 3 of 7 is **reinstalling the CUDA torch build**, undocumented and mandatory: installing `xinference==3.4.0` replaces it with `torch 2.14.0+cpu` and the cluster then reports `gpu_count 0` | step 5 is a **host network policy** in front of the runtime — required by EV05/EV03 and **not yet implemented on this host** |
| Install time | venv create **5.6 s**; `pip install` **200.1 s**; server start to first 200 **24, 28, 31.2, 32, 44 s**; model launch warm **49.3, 51, 55, 61, 62 s**; cold **100 s**. One clean sequence ≈ **4.5 min** to a serving model, excluding downloads | container create → `/health` 200, cold: **217, 223, 225, 226, 260 s** (≈ **3.7–4.3 min**); restart of an existing container **93 s**; `docker start` of an exited one **73 s** |
| Comparability | **NOT COMPARABLE (DEV-07)** — different OS, engine and packaging | **NOT COMPARABLE (DEV-07)**; also neither figure is a clean-host figure (A: pip cache and weights local; B: image and weights already local, pull/download **not measured**) |
| On-disk footprint | venv **3.97 GiB**; weights **7.51 GiB** (shared); pip cache retained **4.73 GiB**; `XINFERENCE_HOME` state **2.8 GiB** across the run | image **30.5 GB**; weights **7.49 GiB**. No equivalent per-deployment state figure is recorded |

### Services and datastores to run

| | Candidate A | Candidate B |
|---|---|---|
| Processes / services | the `xinference-local` **process tree**: API process + worker process + one sub-pool per model replica — one command to start, **not one process to manage** (killing the API listener leaves the worker alive); **plus an orphan reaper PRP must write**; plus a host firewall in front of the metrics endpoints. **No external database and no proxy layer** | vLLM runtime, one container per GPU host; **a supervisor** (vLLM does not restart its own engine — this run used no restart policy, so recovery was manual); **LiteLLM** key/proxy layer *if* B's key layer is used (not run in EV05–EV08); **PostgreSQL 16** as its virtual-key store; a host network policy |
| Datastores | `auth/auth.db` (keys hashed **and** AES-encrypted, the encrypted copy reversible), `auth/encryption_key` + `auth/jwt_secret_key` **in the same directory**, `launch_history.db`, `monitor_config.db`, `token_routers.db`, `download_tasks.db`, `cache/v2/<model>` weights, `virtualenv/v4/…` per-model venv (a hard kill can make later launches **hang ~10 min silently**; recovery is to discard the home directory). All local; a marker request traced across **57 562** files gave **0** hits | PostgreSQL virtual keys and spend rows (with the proxy); container writable-layer compile caches (**no job data**; marker absent across **1 292** roots; lost on recreate — why a recreate costs 3.7–4.3 min rather than 93 s); `docker logs` json-file (request counts, no prompts); **`usage_stats.json` + telemetry to `https://stats.vllm.ai` every 600 s unless opted out**; GPU prefix cache (prompt tokens, volatile, **cannot be deleted on request**) |

### Custom code PRP must write

Both candidates require PRP to build the **entire client-key authority** (FR-003…009) — A because
its store is reversible and has no organisation/application/quota scoping, B because bare vLLM has a
flat key list, no scopes and no revoke API.

| Requirement area | A must build | B must build |
|---|---|---|
| FR-010…015 identity | PRP's own **epoch** and an **index → GPU UUID join** | (B's identity gap is recorded in EV02: no UUID, no stable identity outside `/metrics`) |
| NFR-023 binding | **reconciliation after an unrequested relocation** (the address changes on every recovery); pin placement with **`gpu_idx`** | binding confirmation from the **engine access log** (LiteLLM v1.90.2 sends no routing headers); a **host-level network policy** |
| FR-017 admission | (PRP-side M4 work; not dispositioned) | the **durable admission transaction** (PostgreSQL + fencing) |
| FR-018 concurrency | set `request_limits` at launch (the default is unlimited) and **scrape the metrics exporter** for the limit and the in-flight count | hold `max_num_seqs` in PRP's own config (no API returns it); treat the gauges as under-countable; respect the KV ceiling (**1.71** at 8192 tokens) |
| FR-020…022 interrupts | cancel via the **abort endpoint** with a PRP-generated `request_id`; map a stream without `[DONE]` to UNKNOWN | UNKNOWN/QUARANTINED reconciliation; only an in-stream error object means "failed"; **supply the supervisor** vLLM lacks |
| NFR-024 adapter | **replace error bodies wholesale** (internal address, pid, every model uid) and strip `server` | strip/rewrite `model`, `chatcmpl-` ids, `system_fingerprint`, ~a dozen extra fields, `owned_by`/`root`, the `server` header; **normalise the error mapping** (401 is a bare string) |
| Security / privacy | protect the auth directory (the AES key sits beside the database) | keys via a **read-only config file** (not `VLLM_API_KEY`, which `docker inspect` shows in plaintext); **`VLLM_NO_USAGE_STATS=1` in every launch** |
| Operations | an **orphan reaper** and a bound on `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT`; PRP-side documentation of launch parameters (`POST /v1/models` has **no documented body** in `/openapi.json`) | — |

Item counts as recorded: **8** custom-gap entries for A, **10** for B. The two lists use different
granularity, so the counts are not a ranking.

### Upgrade and rollback

| | Candidate A | Candidate B |
|---|---|---|
| Upgrade attempted? | **Yes — 4 attempts, all failed.** `pip install -U xinference==3.4.0` over a working 3.3.0 environment failed every time with `OSError WinError 32` on `Scripts/xinference-local.exe` | **Not attempted** (owner decision 2026-09-22): a real upgrade needs a second ~30.5 GB image. `upgrade_steps_tried` and `rollback_steps_tried` are **null** |
| Was it a race? | **No**: the runtime was stopped first, zero processes from that environment remained, a manual rename returned "Device or resource busy", and the file was still locked after 60 s and again after 120 s. The holder was never identified (no Sysinternals on this host) | n/a |
| Damage from the failure | the environment was **left broken**: `importlib.metadata` could no longer find `xinference`, pip reported "Ignoring invalid distribution ~inference", while the old 3.3.0 executables still started a working server | n/a |
| Rollback | `pip install xinference==3.3.0` over the broken environment: same `WinError 32`, non-zero exit — though the server still started afterwards in **28.2 s** reporting 3.3.0. **The working path is rebuild + re-import**: venv 5.6 s + install 200.1 s, then the EV08 bundle → instance in **31.2 s**, model launch **49.3 s**, matching the original on the model record, a fixed greedy answer and token usage | Inferred from other runs and explicitly **not a substitute for trying it**: a deployment is one `docker run` from a digest-pinned image plus the redacted export, and an import from that export alone reproduced the source exactly (EV08 step 2), so a **configuration** rollback is one relaunch; any relaunch costs a cold start of **3.7–4.3 min**; **no job state or queue survives it** |
| Comparability | **Not comparable**: A has a measured, failed in-place upgrade on Windows; B has **no upgrade evidence at all**. B's absence is an unmeasured item, not a success | |

### Licences

| | Candidate A | Candidate B |
|---|---|---|
| Runtime | Xinference 3.4.0 **Apache-2.0**; xoscar 0.10.0, transformers 5.17.0, accelerate 1.15.0, bcrypt 5.0.0 **Apache-2.0**; torch 2.14.0+cu130 **BSD-3-Clause** with bundled NVIDIA CUDA components under the **NVIDIA CUDA EULA** | vLLM 0.29.0 **Apache-2.0** (checked in the image's `vllm-*.dist-info/licenses/`) |
| Key/proxy layer | none required | LiteLLM v1.90.2 — **not verified in this run** (the image carries no package metadata at the expected path); PostgreSQL 16 — **not verified in this run** |
| Model | **BYOM**, the owner holds the rights; a SEC-007 licence receipt is required before activation | `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741` **Apache-2.0** (HF licence tag at that revision); the SEC-007 receipt is still to be filed |
| Paid licence | **none required** for the runtime itself | none recorded as required |

Relative position: **A's licence picture is fully verified in this run; B's has two unverified
components** (LiteLLM and PostgreSQL) — and B's stack is the one that *requires* those two
components if its key layer is used.

### Operator skills

A: Python venvs and pip index pinning (incl. why the PyPI torch wheel displaces the CUDA build);
Windows specifics (directory junctions instead of symlinks; shared log files breaking rotation);
process-tree management for an actor system; **reading the vendor's source**, because the abort
route, the launch parameters and the auth switch are absent from both the API and the documentation;
Prometheus scraping; sqlite handling and file-level ACLs on the auth directory.

B: GPU-passthrough containers (incl. the WSL2 quirk needing `VLLM_WSL2_ENABLE_PIN_MEMORY=1`);
reading engine logs for what the API does not return (concurrency limit, `EngineDeadError`,
abort-on-shutdown mode); Prometheus metrics and knowing which of them under-count; key handling that
keeps a key out of `docker inspect`, logs and command lines; YAML/CLI configuration and file-hash
verification.

---

## Where the two candidates differ most

1. **Placement and identity reporting.** A reports a device index, a per-replica address and a
   worker→replica map; B reports no GPU at all through its API and its only stable identity is
   `process_start_time_seconds` on the unauthenticated `/metrics`.
2. **What the unauthenticated surface exposes.** A leaks telemetry (`model_uid`, `worker_address`,
   `gpu_index`, `xinference_home`); B leaks a **working inference path** (`POST /invocations`,
   200 with a real completion).
3. **Over-limit behaviour.** A can be configured to **reject** (4 × 200 + 8 × 429); B **queues**
   (12 × 200 in 3 waves of 4) and offers no rejection.
4. **Cancel semantics.** B stops compute on a socket close in **0.19 s** in both modes; A stops
   nothing for non-streaming work (**61.5 s**, 900 tokens) and needs its explicit abort route —
   which B does not have on chat completions.
5. **Failure signalling.** B emits an in-stream error object on an engine kill; A emits HTTP 200
   with a truncated stream and nothing to distinguish it from success.
6. **Self-recovery.** A relaunches replicas unasked (and orphans a worker holding 10 610 MiB of
   VRAM); B does not recover at all and needs a supervisor PRP supplies.
7. **Key storage.** A's store is **reversible** (a reveal route returning plaintext, the AES key
   beside the database); LiteLLM stores virtual keys as **sha256 hashes** — but LiteLLM's
   `/key/info` is not scoped per key.
8. **Key rotation.** A rotates **online with no restart** (old key refused 0.027 s later);
   B needs a **relaunch per key change**.
9. **Error-body leakage.** A's errors disclose the internal actor address, the pid and **every model
   uid on the cluster**; B's errors disclose no host or stack trace but are inconsistently shaped.
10. **Operational footprint.** A needs no external database or proxy but a 7-step install with an
    undocumented mandatory CUDA-torch reinstall, and its in-place upgrade **failed 4/4**, leaving a
    broken environment; B needs a supervisor, a network policy and (for keys) LiteLLM + PostgreSQL,
    posts telemetry to `stats.vllm.ai` by default, and its upgrade path was **never tested**.
