# WP24 run 2 — Linux parity for candidate A, so A and B can finally be timed against each other

**Record:** `WP24-2026-09-24-run2` · **Purpose:** remove **DEV-07**, the deviation that bars every
timing comparison between the two candidates.

## Why this is a new record and not an edit to run 1

`WP24-2026-09-20-run1` is **closed and approved** (decision receipt approved 2026-09-24, selecting
candidate A with nine conditions). Adding measurements to an approved record would rewrite the basis
someone already signed. This run therefore has its own record, and its only formal power over run 1
is the trigger the receipt itself names:

> *"the arrival of cross-host evidence (DEV-03, DEV-06) or of a Linux-parity run that removes DEV-07
> and finally allows a measured performance comparison"* — `rollback_exit_plan`, run 1

So run 2 either confirms the selection or hands the reviewer a reason to revisit it. It does not
change run 1's verdicts, statuses or dispositions.

## What parity means here, and the choice it forces

Candidate B was **bare vLLM in a Linux container**. Candidate A on Windows had to use the
**transformers** backend, because vLLM has no Windows build — that asymmetry *is* DEV-07.

Running Xinference on Linux with transformers would leave the engine difference in place and answer
nothing. **Parity is Xinference driving the vLLM engine, in a Linux container, on the same GPU.**
What then differs between A and B is the management layer, which is the actual A-versus-B question:
a managed runtime versus an independent one.

| | candidate A, run 2 | candidate B, run 1 |
|---|---|---|
| platform | Linux container | Linux container |
| engine | vLLM, driven by Xinference 3.4.0 | vLLM 0.29.0, bare |
| image | `xprobe/xinference:v3.4.0` (pinned) | `vllm/vllm-openai:latest` at the recorded digest |
| model | `shared_revision` typhoon2.5-qwen3-4b@ce0a741 | same |
| GPU | the same RTX 5060 Ti, 16 311 MiB | same |

**Residual deviation, to be recorded as DEV-09:** the vLLM version inside the Xinference image will
not be exactly 0.29.0. The comparison is therefore *managed vLLM versus bare vLLM on the same host
and model*, with the engine build differing by whatever the image ships. That is a far smaller gap
than DEV-07's platform-plus-engine difference, and it will be stated with the measured versions
rather than assumed away.

## What is measured, and against what

Every figure candidate B recorded in run 1 EV02 has a counterpart here, measured the same way:

| measurement | B's run-1 value | how it is taken again |
|---|---|---|
| cold start to first healthy response | 280 s | container create → first `200`, no image pull, no weights download in the window |
| warm restart | 130 s | restart of an existing container |
| weights load | 64.72 s | from the engine's own log lines |
| engine init | 171.0 s | same |
| torch compile | 27.73 s | same |
| VRAM when ready | 14 249 MiB | `nvidia-smi` at first healthy response |
| KV cache tokens / blocks | 10 576 / 661 | from the engine log |
| smoke latency | 254 ms | one fixed greedy prompt |

Then the throughput comparison run 1 could never make: **12 concurrent requests from 3 processes**,
the same shape EV05 used for both candidates, measuring completion times and tokens per second.

## Preconditions checked before proposing this

- GPU passthrough into a Linux container works on this host: `nvidia/cuda` reported the RTX 5060 Ti
  with 16 311 MiB.
- `xprobe/xinference:v3.4.0` exists and is roughly 6.8 GiB compressed.
- C: had 79 GB free at the start; Docker's storage lives there.

## What this run cannot settle

- **DEV-03 and DEV-06 stand**: still one GPU host, still no clean second machine.
- **DEV-04 stands**: the host runs other workloads, so both candidates' figures carry that caveat.
- Capability findings from run 1 are not re-measured. Run 2 is about time, not about whether the
  key store is reversible or replicas relocate themselves.
- If the numbers favour candidate B materially, that is **input to the reviewer**, not an automatic
  reversal: run 1's selection rested on capability, and NFR-023's requirements do not change because
  something is faster.
