# WP24 run 2 — candidate A on Linux, vLLM engine: measurements

**Record:** `WP24-2026-09-24-run2` · **Candidate:** A (Xinference-managed) · **Measured:** 2026-09-25
**Operator:** Freshair129 (repository owner) · **Purpose:** the Linux-parity measurement named in
run 1's `rollback_exit_plan` as the trigger that would allow a measured A-versus-B comparison.

> **This file records measurements only.** It asserts no gate verdict, changes no acceptance status,
> and does not revisit run 1's selection of candidate A. The owner's instruction for this run was
> *"วัดอย่างเดียว ไม่ต้องตัดสินใหม่"* — measure only, do not re-decide. Every acceptance row remains
> `NOT_RUN` and every run 1 disposition stands.

## What ran

| | value |
|---|---|
| image | `xprobe/xinference:v3.4.0` |
| **actual Xinference version inside it** | **`3.4.1.dev0+g99868ea70.d20260911`** — a dev build, not 3.4.0 |
| **actual vLLM version** | **`0.30.0`** (`Initializing a V1 LLM engine (v0.30.0)`) |
| model | `shared_revision` typhoon2.5-qwen3-4b@ce0a741, bf16, `Qwen3ForCausalLM` |
| GPU | RTX 5060 Ti, 16 311 MiB, single host DESKTOP-VETATMQ |
| `XINFERENCE_HOME` | named Docker volume `prp-wp24-run2-home` |

Candidate B in run 1 ran **bare vLLM 0.29.0** in a Linux container on the same GPU and the same
weights. The remaining difference between the two is the management layer plus a one-minor-version
engine gap, recorded below as **DEV-09**.

## The comparison, at candidate B's own memory budget

B ran with `gpu_memory_utilization = 0.70`. The first candidate-A run used Xinference's default and
is therefore **not** comparable on cache-derived figures; a second run repeated A at exactly 0.70.
Both are recorded, and only the matched pair is compared.

| measurement | **B** — bare vLLM 0.29.0 | **A** — Xinference → vLLM 0.30.0 | source |
|---|---|---|---|
| `Model loading took … memory` | **7.64 GiB** | **7.64 GiB** | identical — same weights, same precision |
| `Loading weights took` | 64.72 s | **56.57 s** | B `EV02/vllm-startup-success.log:26` |
| `Graph capturing finished in` | 58 s / 68 s | 61 s | |
| `GPU KV cache size` | 10 576 tokens | 19 744 tokens | at the same nominal 0.70 |
| `Maximum concurrency for 8 192 tokens` | 1.29x | 2.41x | |
| `init engine (profile, create kv cache, warmup)` | 171.00 s (compilation 27.73 s) | not emitted by this build | |
| VRAM in use when ready | 8.59 GiB consumed + 1.09 peak + 0.23 CUDAGraph | 12 665 MiB | |

**The identical `7.64 GiB` is the parity proof.** It is the figure DEV-07 was missing: both
candidates demonstrably loaded the same weights into the same engine family on the same device.

**The KV-cache and concurrency gap is not a clean A-over-B result.** B's own log warns that
`gpu_memory_utilization=0.7000 is equivalent to --gpu-memory-utilization=0.6762 without CUDA graph
memory profiling`, and that profiling changed between 0.29.0 and 0.30.0. A nominal 0.70 therefore
does not mean the same reservation in the two builds. The honest statement is that **the managed
stack reached a larger usable cache at the same nominal budget, with part of the difference
attributable to the engine version.** Closing that would require pinning both to one vLLM build.

## Candidate A's own Linux figures

| measurement | default utilization | matched 0.70 |
|---|---|---|
| container cold start → `GET /v1/models` 200 | 16.2 s | 16.1 s |
| launch → **first successful completion** | 275.4 s | 255.3 s |
| UID listed in `/v1/models` | 10.2 s | 20.4 s |
| VRAM when ready | 15 361 MiB (690 free) | 12 665 MiB (3 386 free) |
| fixed greedy completion, warm | 345 ms | 360 ms |
| warm restart → API 200 | 14.1 s | 14.1 s |
| `/v1/models` after restart | `[]` | `[]` |

The fixed greedy request returned `2, 3, 5, 7, 11` with `prompt_tokens 18 / completion_tokens 15` in
every run, matching the same-input equivalence method used in run 1 EV08 step 2.

## Findings that stand on their own

1. **`/v1/engines/{model}` under-reports the usable engines.** It offered **only `Transformers`**,
   yet `POST /v1/models` with `model_engine: "vllm"` returned 200 and the vLLM engine ran. PRP must
   not use that endpoint to decide which engines are available.
2. **A model is listed ~265 s before it can serve.** The UID appeared in `/v1/models` at 10.2 s while
   the first successful completion came at 275.4 s; requests in that window return
   `503 "Model is loading, please retry later"`. Listing is not readiness. This reinforces run 1's
   condition that PRP treats the UID as the target but must verify state independently — and it is
   the defect that invalidated this run's own first attempt.
3. **Registration loss on restart reproduces on Linux.** `/v1/models` was empty after every restart,
   exactly as run 1 EV06 measured on Windows. It is **not** a Windows artefact. The custom family
   registration (`persist: false`) is likewise gone, though `GET /v1/engines/{model}` still answers 200.
4. **The image's tag does not identify its contents.** The tag `v3.4.0` ships
   `3.4.1.dev0+g99868ea70.d20260911`. Pinning by tag does not pin the version, which bears directly
   on run 1's `immutable_version_matrix` and its `pinning_rule`.
5. **vLLM is absent from the image and is installed on demand at first launch.** The first attempt
   failed outright with `Model prp-typhoon25-qwen3-4b cannot be run on engine vllm.` Declaring the
   family's `virtualenv` markers made Xinference download and install vLLM plus a full CUDA
   dependency set into `XINFERENCE_HOME` at launch time: ~13 GB, ~8 minutes on a warm cache and
   ~41 minutes on the first attempt. **If `XINFERENCE_HOME` is not durable, that cost is paid again
   on every container replacement.**
6. **`XINFERENCE_HOME` cannot live on a Windows path.** Xinference symlinks the weights into it, and
   Windows refuses the symlink (`A required privilege is not held by the client`) — the same
   privilege wall met in run 1. A Docker-native volume is the only workable location on this host.

## Deviations

| id | statement |
|---|---|
| **DEV-09** | The engine builds differ: B ran vLLM **0.29.0**, A runs vLLM **0.30.0** inside the Xinference image. Cache-derived figures (KV cache size, maximum concurrency) are affected by a documented change to CUDA-graph memory profiling between those versions and are **not** a like-for-like result. Weight-load time and the 7.64 GiB model-loading figure are unaffected. |
| **DEV-04** (carried) | The host ran unrelated workloads during measurement. Free host RAM dipped to 0.93 GiB during the install. Timing figures inherit a shared-host caveat. |
| **DEV-03** (carried) | Single GPU host. No cross-host evidence. |

## Effect on DEV-07 — narrowed, not removed

DEV-07 barred **every** timing comparison between A and B because A ran Windows-native with the
transformers backend while B ran vLLM on Linux. That platform-plus-engine asymmetry **is gone**:
both now run vLLM in a Linux container on the same GPU and the same weights, evidenced by the
identical 7.64 GiB model-loading figure.

What replaces it is **DEV-09**, a strictly smaller gap: one vLLM minor version. Weight-load time is
comparable today; cache-derived figures are not.

**This file proposes no change to run 1.** Whether DEV-07 is narrowed in the run 1 record, and
whether the `rollback_exit_plan` trigger is considered met, is the reviewer's decision and is not
recorded here.

## Operator notes — what this run cost the host

The first attempt died with container **exit 255**, `OOMKilled=false`, no traceback, last log line
`Downloaded vllm`. The cause was **disk, not memory**: `C:\pagefile.sys` had grown to **43.58 GiB**
against a lifetime peak usage of **5.04 GiB**, leaving C: at 99% full, and Docker's
`docker_data.vhdx` can only grow into C:'s free space. This is the same Windows paging-file
mechanism that killed EV02's second replica and forced EV03 onto the 0.6B model in run 1.

**This is a feedback loop, and it is the most operationally significant finding of run 2.** Measured
across this run: the workload drives host free RAM down (to **0.93 GiB** during the vLLM install),
Windows responds by expanding the paging file, and the expansion is **not** given back. The paging
file grew from **43.58 GiB to 71 266 MiB (69.6 GiB)** over the course of these runs, while its
lifetime peak *usage* only ever reached **8 978 MiB (8.8 GiB)** — roughly 61 GiB of allocation
serving a 8.8 GiB high-water mark. C: fell from 32 GB free to **2.3 GB free**, and Docker's vhdx did
not grow at all (135.6 GB throughout), so the paging file accounts for the entire loss.

The operational consequence for PRP: **on this Windows host, running the candidate under memory
pressure consumes disk irreversibly, and that consumed disk is what kills the next run.** Any
deployment of candidate A on a Windows host needs the paging file explicitly bounded, or it will
eventually fail on disk for reasons that appear, in the container's own logs, to be nothing at all.

Reclaimed to make room, all inside the existing vhdx (110 GB → 88 GB used): Docker build cache
6.59 GB, the dead container 4.11 GB, ten stale `ki17-acceptance` build artifacts ~20.7 GB (the two
newest kept), and the unused `lalin-voice-worker-tts:test` image 11.6 GB. No running container was
touched. `docker image prune -a` was **not** used: it removes by "no container references it", which
would have taken the `xprobe/xinference:v3.4.0` image this run depends on.

## Artifacts

| file | contents |
|---|---|
| `artifacts/run-matched-utilization-0.70.json` | the comparable run: timings, engine log values, watchdog samples |
| `artifacts/run-default-utilization.json` | the first successful run, Xinference's default budget |
| `artifacts/run-install-attempt.json` | the run that installed vLLM onto the volume, with the disk/RAM watchdog trace |
| `artifacts/xinference-vllm-startup.log` | full container log including the vLLM engine start |
| `artifacts/run2_linux_parity_v3.py`, `_v4.py` | the harnesses, verbatim |
