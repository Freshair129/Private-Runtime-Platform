# RCA-2026-09-20-ev01-host-precondition

**Symptom.** The first WP24 run record (`WP24-2026-09-20-run1`) carries deviation DEV-01: "control host has an NVIDIA driver; the procedure requires none". The owner asked why a GPU on the host is forbidden when the deployment has only two machines, both with GPUs, each acting as control host and GPU worker.

**Evidence.**
- SRS-PRP context (host topology): control services use the CPU / RAM / disk of an allocated machine; no third machine is required; placing control on A makes A the control-plane SPOF.
- ARCH-PRP §3: "Control plane/database may co-locate on CPU of A with an independent service lifecycle."
- PRP-NFR-021 requires that control web workers never load weights or initialise CUDA / ASR / TTS at import or startup, and that blocking inference runs in a dedicated bounded process. PRP-NFR-022 requires separate dependency locks or image boundaries. Neither requires a host without a GPU.
- STACK-EVALUATION-PRP §6 EV01 expected evidence: "control import without ML/GPU" (a property of the control process, not of the host).
- `docs/WP24-EXPERIMENT-PROCEDURE.md` §2 (precondition row) and EV01 question paragraph, written 2026-09-20, demanded "control host without GPU driver".

**Root cause.** While writing the procedure I translated "control import without ML/GPU" into a host-level precondition (no GPU driver) because a driver-less host is the simplest way to make CUDA initialisation impossible. That is a stronger condition than any requirement states and contradicts the documented two-host topology, where control co-locates with a GPU runtime. The record then correctly flagged the mismatch as a deviation, which exposed the procedure error rather than a run error.

**Escape analysis.** The procedure was approved as a proposal without cross-checking each precondition against the SRS topology paragraph and ARCH §3; the validator checks document structure, not semantic consistency between a procedure and the requirements it cites.

**Fix (this RCA's PR).**
1. Procedure §2: the control-host precondition becomes "a host where the control processes run without GPU access; a GPU driver on the same machine is expected in the two-host topology and is recorded, not forbidden".
2. Procedure EV01: the question and criteria state the evidence that actually proves NFR-021: no ML module in `sys.modules` after importing every control module, and the control process absent from the GPU process list while serving; a driver-less host is optional stronger evidence, never a precondition.
3. Record `WP24-2026-09-20-run1`: DEV-01 kept for history with a `resolution` stating that it was a procedure defect, not a requirement deviation; EV01 verdicts unchanged.
4. Template: `environment.control_host.gpu_driver_present` defaults to `null` (a fact to record) instead of `false` (an expectation).

**Prevention.** Every precondition in an experiment procedure must cite the requirement or document paragraph it derives from; the reviewer checklist in §7 gains "preconditions trace to a requirement" once the first reviewer is named.
