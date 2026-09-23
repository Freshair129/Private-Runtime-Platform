# EV07 partial for candidate A — residency only

Gate `PRP-FR-018` / `PRP-FR-044`. **EV07 remains `BLOCKED` and its blocker is unchanged.** This file
records a partial that uses no speech runtime and no stub; the design and its justification are in
`test-design.md`. Operator observations only; no verdict is computed here.

The mixed chat + ASR + TTS load was **not run**, because
`scope_decisions.speech_in_scope = false` (owner, 2026-09-20) and the procedure forbids substituting
a stub. What follows answers only the candidate-side half of EV07 step 3: whether Xinference manages
residency by itself, and whether that can be switched off.

## 1. Does the candidate unload a resident model by itself? No.

The model was launched and left **idle for 20 minutes**, sampled every 30 s (41 samples):

| measurement | result |
|---|---|
| `prp-a-llm` present in `/v1/models` | **41 of 41 samples** |
| VRAM first → last | 8 820 → 9 235 MiB |
| VRAM min / max | 8 808 / 9 237 MiB |
| unload or evict lines in the log | none |

VRAM **rose** slightly over the window rather than falling, which is other desktop software on the
same card, not the model. Nothing was unloaded, nothing was evicted, and the model never left the
listing.

This is confirmed by the shipped code: there is **no idle timeout, no model TTL and no keep-alive
eviction** anywhere for a loaded model. The only TTL in `constants.py` is
`XINFERENCE_MODEL_GPU_MEMORY_CACHE_TTL` (90 s), which caches a memory *reading*, and an HTTP
keep-alive for uvicorn. P1's requirement that the LLM stay resident is met by default, with nothing
to disable.

## 2. The auto-management that does exist

| behaviour | default | can PRP turn it off |
|---|---|---|
| **placement**: which GPU a launch lands on | `XINFERENCE_LAUNCH_STRATEGY = IDLE_FIRST_LAUNCH_STRATEGY`, the supervisor chooses | **yes** — pass `gpu_idx` in the launch body and the strategy is skipped entirely |
| **recreation**: a dead model actor is rebuilt unasked | `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` unset = **unbounded** | only **bounded**, not disabled (EV03 and EV06 measured the behaviour: 35–40 s on a 0.6B model, 131.8 s on the 4B) |
| **startup GPU-orphan cleanup** | always on | not configurable, and see below — it does not act on this deployment |

`gpu_idx` is the important one: it is the switch that turns candidate A from choosing placement
itself into doing what PRP tells it, which is what a PRP-owned physical admission authority needs.
**It is not discoverable from the API**: `POST /v1/models` has **no documented request body at
all** in `/openapi.json`, so `gpu_idx`, `request_limits` and `replica` exist only in the source. That
is the same pattern as EV05 (the limit cannot be read back) and EV06 (the abort route is not in the
route table).

## 3. The startup orphan cleanup does not reap what this deployment leaves behind

EV06 found that force-killing the supervisor leaves an orphaned worker holding the GPU. The shipped
`_cleanup_gpu_orphans_on_startup` looked like it might handle that, so the claim was tested rather
than assumed. It kills a GPU-holding process only when its **PPID is 1** *and* its **command line
looks like vLLM**.

Reproduced and measured:

| step | VRAM | processes |
|---|---|---|
| model resident, supervisor alive | 9 235 MiB | 3 |
| supervisor force-killed | **9 235 MiB** | 1 orphan survives (ppid 20176, not 1) |
| **fresh instance started** (51.6 s to answer) | **9 235 MiB** | orphan still there |

The new instance's own log says exactly why:

```
Startup GPU orphan cleanup: 23 GPU-occupying process(es) found, none are vLLM orphans
(all have live parents or non-matching cmdline)
```

So the cleanup is vLLM-specific and Unix-shaped, and on a Windows transformers deployment it
**never fires**. The orphan had to be killed by hand; VRAM then fell to 1 448 MiB. EV06's finding
stands and now has its mechanism.

## 4. An operational hazard found while running this

Two launches **stalled indefinitely** — about 10 minutes each with no VRAM allocated and no error —
against the `XINFERENCE_HOME` reused from EV06. The log showed the sub-pool starting, the request
handler starting, then silence. That home's per-model virtualenv
(`home/virtualenv/v4/prp-typhoon25-qwen3-4b/transformers/3.12.10`) had been left behind by EV06's
deliberate process kills. The same registration and launch on a **fresh home** succeeded in **51 s**.

Two things follow for an operator: a hard kill can leave the per-model environment in a state where
later launches hang silently rather than failing, and the recovery is to discard that home
directory. Related noise seen at the same time: when the local date rolled over, log rotation failed
repeatedly with `PermissionError: [WinError 32]` because several processes hold the same log file,
leaving `*.rotate.lock` files behind.

## What PRP has to carry

- Nothing to disable for residency: the candidate never unloads a resident model.
- **Pin placement with `gpu_idx`** so the supervisor's idle-first strategy does not choose for PRP,
  and keep that parameter documented on PRP's side, since the API does not describe it.
- Bound the recreation with `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` and reconcile afterwards; it
  cannot be switched off.
- Reap orphaned workers itself. The candidate's own startup cleanup will not do it here.

## What is still `BLOCKED`

Everything EV07 actually asks: the mixed chat + ASR + TTS load, the VRAM time series under that
load, OOM behaviour, and whether speech exceeds the resident envelope. Those need a licensed speech
candidate from WP10. `status` stays `BLOCKED` and the blocker still names WP10.
