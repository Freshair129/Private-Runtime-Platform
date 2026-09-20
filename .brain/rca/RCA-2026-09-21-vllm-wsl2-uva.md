# RCA-2026-09-21-vllm-wsl2-uva

**Symptom.** WP24 EV02, candidate B (vLLM). `vllm/vllm-openai:latest` (0.29.0) started, read the model, then the engine core died during `init_device` with `RuntimeError: UVA is not available` (`vllm/v1/worker/gpu/buffer_utils.py:47`), followed by `RuntimeError: Engine core initialization failed`. Container exited (1) about 20 s after start. Host: DESKTOP-VETATMQ, RTX 5060 Ti (sm_120), Docker Desktop 29.8.0 on WSL2.

**Evidence.**
- `vllm/utils/platform_utils.py:51` — `is_uva_available() = is_pin_memory_available() or current_platform.is_cpu()`.
- `vllm/platforms/cuda.py:290` — on WSL, `is_pin_memory_available()` first gates on the WSL2 kernel version (`>= 4.19.121`), and **on a compatible kernel it returns `envs.VLLM_WSL2_ENABLE_PIN_MEMORY`, which is off by default**. Source comment: "On compatible WSL2 kernels, pinned memory is supported but disabled by default. Enable it via VLLM_WSL2_ENABLE_PIN_MEMORY=1."
- Container kernel: `6.18.33.2-microsoft-standard-WSL2` — far above the 4.19.121 gate, so the kernel branch was not the cause.
- `vllm/v1/worker/gpu/states.py:34` — the V2 model runner allocates `StagedWriteTensor` → `UvaBuffer` unconditionally, so with pinned memory disabled the V2 runner cannot initialise at all.

**Root cause.** vLLM 0.29.0 disables pinned host memory by default under WSL2, and its V2 GPU model runner (used by default on this build) requires UVA buffers, which require pinned memory. The two defaults are incompatible: on Docker Desktop / WSL2 the engine fails closed before any GPU allocation. Nothing about the model, the weights, the GPU, the driver or the arch list was involved — `sm_120` is present in `torch.cuda.get_arch_list()` and the weights verified against the pinned revision hashes before launch.

**Escape analysis.** The WP24 procedure §2 lists GPU driver and CUDA as preconditions but says nothing about the container/virtualisation substrate the runtime executes on. The two-host topology in SRS/ARCH is stated in terms of machines, not of an OS or hypervisor, so a Windows + WSL2 substrate was never recorded as a variable that the candidate evidence depends on. The EV02 evidence would therefore have been reported against an unstated platform assumption.

**Fix (as executed).** Launch candidate B with `VLLM_WSL2_ENABLE_PIN_MEMORY=1`. The WDDM pinned-memory cap (~50 % of physical RAM, 31.8 GB here) is not binding at this model size. No change to vLLM, the image, the weights or PRP code.

**Prevention.**
1. Record the execution substrate per GPU host in the run record (`environment.gpu_hosts[].os` plus container runtime and, where applicable, WSL2 kernel), because candidate behaviour demonstrably depends on it.
2. Record `VLLM_WSL2_ENABLE_PIN_MEMORY=1` in `candidates[].version_manifest.config_files` / launch command, since it is a launch-time condition of every candidate-B measurement taken on this host.
3. Carry the finding into the fit-gap as a candidate-B operator cost: running vLLM on Windows requires a WSL2-specific environment variable that is not in the vendor quickstart, and the failure mode is a fatal engine error rather than a warning.
