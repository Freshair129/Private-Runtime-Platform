# EV07 partial for candidate A — residency only

Gate `PRP-FR-018` / `PRP-FR-044`. **EV07 itself stays `BLOCKED`.**

## Why this is a partial, not the experiment

The procedure (§6, and EV07's own precondition) allows EV07 to run only when the owner has decided a
speech candidate is ready and past the license gate, and it says in terms that **no stub may be
substituted** for either candidate. The run record holds
`scope_decisions.speech_in_scope = false`, decided by the owner on 2026-09-20, with EV07 `BLOCKED`
for both candidates until WP10 delivers a licensed speech candidate.

That decision stands, so the mixed chat + ASR + TTS load is not run and **the status and blocker are
left untouched**. A `lalin-voice-worker-tts` image exists on this host from unrelated work; it is not
a WP10 deliverable and has no license receipt in `shared_revision`, so it is not used.

What *can* be answered without any speech runtime is the candidate-side half of EV07 step 3: the
procedure states the requirement as "A: Xinference auto-management ต้องปิดได้ เพราะ P1 ไม่ unload LLM
อัตโนมัติ". Whether the candidate manages residency by itself is a property of the candidate alone.
Owner approved this partial on 2026-09-24.

## What is measured

**1. Does the candidate unload a resident model by itself?**
The model is launched and then left **idle for 20 minutes**, with `nvidia-smi` VRAM, `/v1/models`
and the worker metrics exporter sampled every 30 s. Any drop in VRAM, disappearance from
`/v1/models`, or unload line in the log is a silent unload. The requirement is that a resident LLM
stays resident.

**2. Which auto-management knobs exist, and can they be turned off?**
From the shipped code, with defaults and whether each can be disabled:
`XINFERENCE_LAUNCH_STRATEGY` (default `IDLE_FIRST_LAUNCH_STRATEGY`, placement chosen by the
supervisor), `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` (default unbounded, the unrequested
recreation EV03 and EV06 measured), and the startup GPU-orphan cleanup.

**3. Does the startup GPU-orphan cleanup reap what EV06 left behind?**
`_cleanup_gpu_orphans_on_startup` kills a GPU-holding process only when its **PPID is 1** *and* its
**command line looks like vLLM**. EV06 left an orphaned worker holding 10.6 GiB on Windows with the
transformers backend, which matches neither condition. The claim is therefore tested: reproduce the
orphan, start a fresh instance, and record whether the orphan is reaped or survives.

## What this partial does not do

- No speech runtime, no mixed load, no ASR or TTS: EV07's actual question is untouched.
- No VRAM envelope for speech, which is what WP10 has to supply.
- `status` stays `BLOCKED` and the blocker keeps naming WP10; only `observations`, `measurements` and
  `artifacts` are added, so the reviewer sees the partial without the gate appearing to have run.
- One GPU host (DEV-03) and a Windows-native transformers deployment (DEV-07).
