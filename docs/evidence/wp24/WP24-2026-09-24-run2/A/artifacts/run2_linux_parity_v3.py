"""WP24 run 2 (v3): candidate A on Linux, vLLM engine, against the already-populated volume.

v2 proved the install works and left the vLLM virtualenv on the named volume, so this run
skips the install entirely. v2's defect is fixed here: it treated "the UID appears in
/v1/models" as ready, but Xinference lists a model while it is still loading, so the smoke
request got 503 and the warm restart killed the load mid-flight. Readiness is now a real
chat completion returning 200.
"""
import json
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request

IMAGE = "xprobe/xinference:v3.4.0"
NAME = "prp-wp24-xinf-a-linux"
VOLUME = "prp-wp24-run2-home"
PORT = 9997
BASE = f"http://127.0.0.1:{PORT}"
WEIGHTS_HOST = "F:/prp-models/typhoon2.5-qwen3-4b@ce0a741"
WEIGHTS_CT = "/models/shared-revision"
MODEL = "prp-typhoon25-qwen3-4b"
UID = "prp-a-llm"
READY_BUDGET_S = 3600

out = {"image": IMAGE, "volume": VOLUME, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
       "note": "virtualenv already installed on the volume by the v2 run"}
SMOKE = {"model": UID, "temperature": 0, "max_tokens": 32, "seed": 1,
         "messages": [{"role": "user",
                       "content": "List the first five prime numbers, comma separated."}]}


def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def vram():
    _, o, _ = sh(["nvidia-smi", "--query-gpu=memory.used,memory.free",
                  "--format=csv,noheader,nounits"], 120)
    used, free = (int(x) for x in o.splitlines()[0].split(","))
    return {"used_mib": used, "free_mib": free}


def api(method, path, body=None, timeout=1800):
    d = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"} if d else {}
    req = urllib.request.Request(BASE + path, d, h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:160]}"


def wait_api(limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        if api("GET", "/v1/models", timeout=8)[0] == 200:
            return round(time.time() - t0, 1)
        time.sleep(2)
    return None


def start_container(fresh):
    t0 = time.time()
    if fresh:
        sh(["docker", "rm", "-f", NAME], 300)
        rc, o, e = sh([
            "docker", "run", "-d", "--name", NAME, "--gpus", "all",
            "-p", f"{PORT}:9997",
            "-v", f"{WEIGHTS_HOST}:{WEIGHTS_CT}:ro",
            "-v", f"{VOLUME}:/data",
            "-e", "XINFERENCE_AUTH_ADVANCED=0",
            "-e", "XINFERENCE_HOME=/data",
            IMAGE, "xinference-local", "-H", "0.0.0.0", "--port", "9997",
        ], 900)
    else:
        rc, o, e = sh(["docker", "restart", NAME], 900)
    if rc != 0:
        return {"error": (e or o)[:400]}
    return {"seconds_to_api_200": wait_api(),
            "wall_seconds_including_docker": round(time.time() - t0, 1)}


def register():
    api("DELETE", f"/v1/model_registrations/LLM/{MODEL}", timeout=120)
    template = open(WEIGHTS_HOST + "/chat_template.jinja", encoding="utf-8").read()
    family = {
        "version": 2, "context_length": 8192, "model_name": MODEL,
        "model_lang": ["en", "th"], "model_ability": ["chat"],
        "model_description": "WP24 shared_revision, linux parity run (vllm engine)",
        "chat_template": template,
        "stop_token_ids": [151643, 151644, 151645],
        "stop": ["<|endoftext|>", "<|im_start|>", "<|im_end|>"],
        "model_specs": [{"model_format": "pytorch", "model_size_in_billions": 4,
                         "model_uri": WEIGHTS_CT, "quantization": "none",
                         "quantizations": ["none"]}],
        "model_family": "qwen3", "model_type": "qwen3", "architectures": ["Qwen3ForCausalLM"],
        "virtualenv": {"packages": [
            '#transformers_dependencies# ; #engine# == "Transformers"',
            '#vllm_dependencies# ; #engine# == "vllm"',
            '#system_numpy# ; #engine# == "vllm"',
        ]},
    }
    return api("POST", "/v1/model_registrations/LLM",
               {"model": json.dumps(family), "persist": False}, timeout=300)[0]


samples = []
stop_watch = threading.Event()


def watchdog():
    while not stop_watch.is_set():
        _, state, _ = sh(["docker", "inspect", NAME, "--format",
                          "{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}"], 120)
        _, freeram, _ = sh(["powershell", "-NoProfile", "-Command",
                            "[math]::Round((Get-CimInstance Win32_OperatingSystem)"
                            ".FreePhysicalMemory/1MB,2)"], 120)
        samples.append({"t": time.strftime("%H:%M:%S"), "container": state,
                        "host_free_ram_gib": freeram, "vram": vram()})
        stop_watch.wait(30)


def launch_and_wait(tag):
    """Launch on vLLM and wait until a real completion returns 200."""
    res = {}

    def do_launch():
        t = time.time()
        st, body = api("POST", "/v1/models", {
            "model_uid": UID, "model_name": MODEL, "model_type": "LLM",
            "model_engine": "vllm", "model_format": "pytorch", "model_size_in_billions": 4,
            "quantization": "none", "n_gpu": 1, "max_model_len": 8192,
        }, timeout=READY_BUDGET_S)
        res.update({"launch_status": st, "launch_body": body if isinstance(body, str) else "ok",
                    "launch_call_seconds": round(time.time() - t, 1)})

    t0 = time.time()
    th = threading.Thread(target=do_launch, daemon=True)
    th.start()
    listed_at = ready_at = None
    last = None
    while time.time() - t0 < READY_BUDGET_S:
        st, models = api("GET", "/v1/models", timeout=20)
        if listed_at is None and st == 200 and isinstance(models, dict) and any(
                m.get("id") == UID for m in models.get("data", [])):
            listed_at = round(time.time() - t0, 1)
        if listed_at is not None:
            sst, sres = api("POST", "/v1/chat/completions", SMOKE, timeout=180)
            last = (sst, str(sres)[:200])
            if sst == 200:
                ready_at = round(time.time() - t0, 1)
                res["first_completion"] = {
                    "answer": sres["choices"][0]["message"]["content"],
                    "usage": sres.get("usage")}
                break
        _, state, _ = sh(["docker", "inspect", NAME, "--format", "{{.State.Status}}"], 120)
        if state != "running":
            res["container_died"] = True
            break
        time.sleep(10)
    th.join(timeout=20)
    res.update({"tag": tag, "listed_in_models_seconds": listed_at,
                "seconds_to_first_200_completion": ready_at, "last_probe": last})
    return res


# ---------------- cold start, launch, ready ----------------
out["vram_before"] = vram()
out["cold_start"] = start_container(fresh=True)
threading.Thread(target=watchdog, daemon=True).start()
out["register_status"] = register()
st, engines = api("GET", f"/v1/engines/{MODEL}", timeout=120)
out["engines_offered"] = engines if isinstance(engines, str) else json.dumps(engines,
                                                                            ensure_ascii=False)[:400]
out["launch"] = launch_and_wait("cold")
out["vram_when_ready"] = vram()

# ---------------- the engine's own log lines, as candidate B recorded them ----------------
_, logs, _ = sh(["docker", "logs", NAME], 600)
logs = re.sub(r"\x1b\[[0-9;]*m", "", logs)
pats = {
    "vllm_version": r"vLLM (?:API server )?version[= ]([\d.]+)",
    "load_weights_seconds": r"Loading weights took ([\d.]+) seconds",
    "model_loading_seconds": r"Model loading took ([\d.]+) seconds",
    "model_loading_gib": r"Model loading took .*?([\d.]+) GiB",
    "init_engine_seconds": r"init engine .*?took ([\d.]+) seconds",
    "torch_compile_seconds": r"torch\.compile takes ([\d.]+) s",
    "gpu_kv_cache_size_tokens": r"GPU KV cache size: ([\d,]+) tokens",
    "num_gpu_blocks": r"GPU blocks: (\d+)",
    "max_concurrency": r"Maximum concurrency for ([\d,]+) tokens per request: ([\d.]+)x",
    "graph_capture_seconds": r"Graph capturing finished in ([\d]+) secs",
}
out["engine_log_values"] = {k: [g for g in m.groups() if g]
                            for k, p in pats.items() if (m := re.search(p, logs))}
out["engine_log_tail"] = logs[-1500:]

# ---------------- timed smoke on the warm model ----------------
if out["launch"].get("seconds_to_first_200_completion") is not None:
    t = time.time()
    st, res = api("POST", "/v1/chat/completions", SMOKE, timeout=600)
    out["smoke_warm"] = {"status": st, "wall_ms": round((time.time() - t) * 1000),
                         "answer": (res["choices"][0]["message"]["content"]
                                    if isinstance(res, dict) else str(res)[:160]),
                         "usage": res.get("usage") if isinstance(res, dict) else None}

    # ---------------- warm restart: does the registration survive? ----------------
    out["warm_restart"] = start_container(fresh=False)
    st, models = api("GET", "/v1/models", timeout=60)
    out["warm_restart"]["models_after"] = ([m["id"] for m in models["data"]]
                                           if isinstance(models, dict) else models)
    st, engines2 = api("GET", f"/v1/engines/{MODEL}", timeout=60)
    out["warm_restart"]["family_after_restart_status"] = st

stop_watch.set()
out["watchdog_samples"] = samples[-60:]
out["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
print(json.dumps(out, ensure_ascii=False, indent=1))
