#!/usr/bin/env python3
"""EV08 adapter / exit probe for WP24 candidate B (vLLM).

Design: docs/evidence/wp24/WP24-2026-09-20-run1/B/EV08/test-design.md (approved 2026-09-22).
Procedure: docs/WP24-EXPERIMENT-PROCEDURE.md EV08 (gate PRP-NFR-024).

Subcommands (one JSON output each, written to --out):
  export          docker inspect of --container -> declarative spec with secret values redacted,
                  plus sha256 of the files that define the model; fails if a key value survives
  launch          start a container from an export spec alone; keys come from --key-env names,
                  one key through VLLM_API_KEY, several through a read-only --config YAML
                  in --secrets-dir
  fingerprint     startup non-default args, /v1/models, cache_config_info and one greedy completion
  compare         diff two fingerprint files
  key-check       HTTP status per key (and with no key); whether any key value shows up in docker
                  logs or docker inspect (booleans only)
  leak-scan       six response kinds straight from vLLM, with every vendor-identifying marker found
  datastore-scan  a request carrying a unique marker, then docker diff and a marker search in the
                  changed files and in docker logs

No verdict is computed (docs/WP24-EXPERIMENT-PROCEDURE.md section 3 item 4). Key values are read
only from the environment variables named on the command line and are never printed or written,
except into the --config YAML under --secrets-dir, which must be outside the repository.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import wp24_common as common

REDACTED = "<REDACTED>"
MODEL_FILES = (
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "model.safetensors.index.json",
)
IN_CONTAINER_KEYS = "/run/prp/keys.yaml"
GREEDY_PROMPT = "ตอบสั้น ๆ: เมืองหลวงของประเทศไทยคืออะไร"
_NON_DEFAULT_RE = re.compile(r"non-default args: (\{.*\})")


# --- pure functions (unit tested) -------------------------------------------------------------


def user_env(container_env: list[str], image_env: list[str]) -> list[tuple[str, str]]:
    """Environment entries set at launch: those not identical to an entry of the image itself."""
    baked = set(image_env)
    pairs = []
    for entry in container_env:
        if entry in baked:
            continue
        name, _, value = entry.partition("=")
        pairs.append((name, value))
    return pairs


def redact_env(pairs: list[tuple[str, str]], allow: set[str]) -> list[dict[str, str]]:
    """Keep the value only for allow-listed names; every other value is replaced."""
    return [{"name": n, "value": v if n in allow else REDACTED} for n, v in pairs]


def host_path(source: str) -> str:
    """Docker Desktop reports Windows bind sources as /run/desktop/mnt/host/<drive>/...; undo it."""
    match = re.match(r"^/run/desktop/mnt/host/([a-zA-Z])/(.*)$", source)
    return f"{match.group(1).upper()}:/{match.group(2)}" if match else source


def build_spec(
    inspect: dict[str, Any],
    image_env: list[str],
    allow: set[str],
    image_entrypoint: list[str] | None = None,
) -> dict[str, Any]:
    """Declarative launch spec from one ``docker inspect`` object.

    The command is taken from ``Config.Cmd`` (``Args`` alone drops the program when the command
    replaced the image's), and the entrypoint only when it differs from the image's own.
    """
    config, host = inspect.get("Config", {}), inspect.get("HostConfig", {})
    entrypoint = config.get("Entrypoint")
    ports = [
        {"container": port, "host_ip": b.get("HostIp", ""), "host_port": b.get("HostPort", "")}
        for port, bindings in sorted((host.get("PortBindings") or {}).items())
        for b in bindings or []
    ]
    mounts = [
        {
            "source": host_path(m.get("Source", "")),
            "target": m.get("Destination"),
            "ro": not m.get("RW", True),
        }
        for m in inspect.get("Mounts", [])
    ]
    gpus = [
        r.get("Count")
        for r in host.get("DeviceRequests") or []
        if "gpu" in str(r.get("Capabilities"))
    ]
    return {
        "image": config.get("Image"),
        "image_id": inspect.get("Image"),
        "entrypoint": entrypoint if entrypoint != image_entrypoint else None,
        "args": list(config.get("Cmd") or []),
        "env": redact_env(user_env(config.get("Env") or [], image_env), allow),
        "ports": ports,
        "mounts": mounts,
        "gpus": "all" if -1 in gpus else (gpus[0] if gpus else None),
        "ipc_mode": host.get("IpcMode"),
    }


def diff_fingerprints(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Field-by-field comparison of two fingerprints; ``equal`` is true only if all fields match."""
    fields = ("non_default_args", "models", "cache_config_info", "completion_text")
    out = {f: {"equal": a.get(f) == b.get(f), "a": a.get(f), "b": b.get(f)} for f in fields}
    out["equal"] = all(v["equal"] for v in out.values())
    return out


def find_markers(text: str, markers: list[str]) -> list[str]:
    """Markers (case-insensitive) that occur in ``text``."""
    low = text.lower()
    return [m for m in markers if m and m.lower() in low]


def parse_docker_diff(text: str) -> list[dict[str, str]]:
    """``docker diff`` lines (``A /path``, ``C /path``, ``D /path``) as dicts."""
    rows = []
    for line in text.splitlines():
        kind, _, path = line.strip().partition(" ")
        if kind in {"A", "C", "D"} and path:
            rows.append({"kind": kind, "path": path})
    return rows


def diff_search_roots(rows: list[dict[str, str]]) -> list[str]:
    """Smallest set of paths that covers every added or changed file in a ``docker diff``.

    An added path is a root unless an added ancestor already covers it. A changed (``C``) path is
    kept only when nothing in the diff lies below it: that makes it a modified file, whereas a
    changed directory only means something was added inside it, and searching it would re-read
    unchanged image content.
    """
    live = [r for r in rows if r["kind"] != "D"]
    added = {r["path"] for r in live if r["kind"] == "A"}
    paths = {r["path"] for r in live}
    roots = []
    for r in live:
        p = r["path"]
        parents = [p[:i] for i in range(1, len(p)) if p[i] == "/"]
        added_root = r["kind"] == "A" and not any(q in added for q in parents)
        changed_leaf = r["kind"] == "C" and not any(q.startswith(p + "/") for q in paths)
        if added_root or changed_leaf:
            roots.append(p)
    return sorted(roots)


def non_default_args(log_text: str) -> str | None:
    """The last ``non-default args: {...}`` payload in a vLLM log, or None."""
    found = _NON_DEFAULT_RE.findall(log_text)
    return found[-1] if found else None


# --- helpers ------------------------------------------------------------------------------------


def _docker(*args: str, timeout: float = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    if env is None:
        return common.run_command(["docker", *args], timeout_seconds=timeout)
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=timeout, env=env
    )
    return {"return_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _inspect(name: str) -> dict[str, Any]:
    out = _docker("inspect", name, timeout=30)
    return json.loads(out["stdout"])[0] if out["return_code"] == 0 else {}


def _http(method: str, url: str, token: str | None, body: dict | None = None, timeout: float = 120):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data, headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers.items()), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        return None, {}, f"{type(exc).__name__}: {exc}"


def _secret_values(env_names: list[str]) -> list[str]:
    return [os.environ[n] for n in env_names if os.environ.get(n)]


def _scrub(text: str, secrets: list[str]) -> str:
    for value in secrets:
        text = text.replace(value, REDACTED)
    return common.redact_text(text)


def _chat(model: str, content: str, max_tokens: int, **extra: Any) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        **extra,
    }


# --- subcommands --------------------------------------------------------------------------------


def cmd_export(a: argparse.Namespace) -> dict[str, Any]:
    inspect = _inspect(a.container)
    image = _docker("image", "inspect", inspect.get("Image", ""), timeout=30)
    image_config = json.loads(image["stdout"])[0]["Config"] if image["return_code"] == 0 else {}
    spec = build_spec(
        inspect, image_config.get("Env") or [], set(a.allow_env), image_config.get("Entrypoint")
    )
    digests = (
        json.loads(image["stdout"])[0].get("RepoDigests", []) if image["return_code"] == 0 else []
    )
    spec["image_digest"] = digests[0] if digests else None
    weights: dict[str, str | None] = {}
    for name in MODEL_FILES:
        path = Path(a.weights_dir) / name
        weights[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    spec["model_files_sha256"] = weights
    text = json.dumps(spec)
    leaked = [n for n in a.secret_env if os.environ.get(n) and os.environ[n] in text]
    return {
        "spec": spec,
        "checks": {"secret_env_checked": a.secret_env, "plaintext_secret_present": bool(leaked)},
        "exit_code": 2 if leaked else 0,
    }


def cmd_launch(a: argparse.Namespace) -> dict[str, Any]:
    exported = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    spec = exported.get("result", exported)["spec"]
    keys = _secret_values(a.key_env)
    if len(keys) != len(a.key_env):
        raise SystemExit("every --key-env must name a set environment variable")
    if a.replace:
        _docker("rm", "-f", a.name, timeout=60)
    run = ["run", "-d", "--name", a.name]
    if spec.get("gpus"):
        run += ["--gpus", str(spec["gpus"])]
    if spec.get("entrypoint"):
        run += ["--entrypoint", spec["entrypoint"][0]]
    if spec.get("ipc_mode"):
        run += [f"--ipc={spec['ipc_mode']}"]
    for p in spec["ports"]:
        run += ["-p", f"{p['host_ip']}:{p['host_port']}:{p['container'].split('/')[0]}"]
    for m in spec["mounts"]:
        run += ["-v", f"{m['source']}:{m['target']}" + (":ro" if m["ro"] else "")]
    for e in spec["env"]:
        if e["value"] != REDACTED:
            run += ["-e", f"{e['name']}={e['value']}"]
    env = dict(os.environ)
    key_mode = "none"
    extra_args: list[str] = []
    if len(keys) == 1:
        env["VLLM_API_KEY"] = keys[0]
        run += ["-e", "VLLM_API_KEY"]
        key_mode = "env VLLM_API_KEY"
    elif keys:
        secrets_dir = Path(a.secrets_dir).resolve()
        if Path.cwd().resolve() in secrets_dir.parents or secrets_dir == Path.cwd().resolve():
            raise SystemExit("--secrets-dir must be outside the repository working tree")
        secrets_dir.mkdir(parents=True, exist_ok=True)
        key_file = secrets_dir / f"{a.name}-keys.yaml"
        key_file.write_text("api-key:\n" + "".join(f'  - "{k}"\n' for k in keys), encoding="utf-8")
        run += ["-v", f"{key_file.as_posix()}:{IN_CONTAINER_KEYS}:ro"]
        extra_args = ["--config", IN_CONTAINER_KEYS]
        key_mode = f"--config YAML with {len(keys)} keys"
    image = spec.get("image_digest") or spec["image"]
    entry_rest = (spec.get("entrypoint") or [])[1:]
    command = run + [image, *entry_rest, *spec["args"], *extra_args]
    started = time.time()
    out = _docker(*command, timeout=300, env=env)
    ready_s = None
    if out["return_code"] == 0:
        base = a.base_url.rstrip("/")
        while time.time() - started < a.ready_timeout:
            if _http("GET", f"{base}/health", None, timeout=3)[0] == 200:
                ready_s = round(time.time() - started, 1)
                break
            time.sleep(3)
    return {
        "name": a.name,
        "key_mode": key_mode,
        "key_env_names": a.key_env,
        "docker_run": _scrub(" ".join(["docker", *command]), keys),
        "return_code": out["return_code"],
        "stderr": _scrub(out["stderr"], keys)[:600],
        "ready_s_from_docker_run": ready_s,
    }


def cmd_fingerprint(a: argparse.Namespace) -> dict[str, Any]:
    base, token = a.base_url.rstrip("/"), os.environ.get(a.token_env or "", "") or None
    secrets = _secret_values([a.token_env] if a.token_env else [])
    logs = _docker("logs", a.container, timeout=60)
    nda = non_default_args(logs["stdout"] + logs["stderr"])
    _, _, models_text = _http("GET", f"{base}/v1/models", token)
    try:
        models = json.loads(models_text)
        for m in models.get("data", []):
            m.pop("created", None)
            for perm in m.get("permission") or []:
                perm.pop("id", None)
                perm.pop("created", None)
    except ValueError:
        models = models_text[:300]
    _, _, metrics = _http("GET", f"{base}/metrics", token)
    info = next(
        (ln for ln in metrics.splitlines() if ln.startswith("vllm:cache_config_info")), None
    )
    status, _, body = _http(
        "POST",
        f"{base}/v1/chat/completions",
        token,
        _chat(a.model, GREEDY_PROMPT, 64, temperature=0, seed=1234),
    )
    try:
        text = json.loads(body)["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError):
        text = None
    return {
        "container": a.container,
        "non_default_args": _scrub(nda, secrets) if nda else None,
        "models": models,
        "cache_config_info": info,
        "completion_status": status,
        "completion_text": text,
        "completion_sha256": hashlib.sha256(text.encode()).hexdigest() if text else None,
    }


def cmd_compare(a: argparse.Namespace) -> dict[str, Any]:
    fa = json.loads(Path(a.a).read_text(encoding="utf-8"))["result"]
    fb = json.loads(Path(a.b).read_text(encoding="utf-8"))["result"]
    return {"a": a.a, "b": a.b, "diff": diff_fingerprints(fa, fb)}


def cmd_key_check(a: argparse.Namespace) -> dict[str, Any]:
    base = a.base_url.rstrip("/")
    body = _chat(a.model, "hi", 1)
    statuses = {"no key": _http("POST", f"{base}/v1/chat/completions", None, body)[0]}
    for name in a.key_env:
        statuses[name] = _http("POST", f"{base}/v1/chat/completions", os.environ.get(name), body)[0]
    exposure: dict[str, Any] = {}
    if a.container:
        logs = _docker("logs", a.container, timeout=60)
        log_text = logs["stdout"] + logs["stderr"]
        inspect_text = json.dumps(_inspect(a.container))
        for name in a.key_env:
            value = os.environ.get(name, "")
            exposure[name] = {
                "in_docker_logs": bool(value) and value in log_text,
                "in_docker_inspect": bool(value) and value in inspect_text,
            }
    return {"stage": a.stage, "status_by_key": statuses, "key_value_exposure": exposure}


def cmd_leak_scan(a: argparse.Namespace) -> dict[str, Any]:
    base, token = a.base_url.rstrip("/"), os.environ.get(a.token_env or "", "") or None
    secrets = _secret_values([a.token_env] if a.token_env else [])
    markers = [
        a.model,
        "vllm",
        "chatcmpl",
        "system_fingerprint",
        "/models",
        "uvicorn",
        "dist-packages",
        "traceback",
        "kv_transfer_params",
        "prompt_logprobs",
        "service_tier",
        "127.0.0.1",
        "172.17.",
        "engine",
        "typhoon",
        "qwen",
    ]
    probes = {
        "chat": ("POST", "/v1/chat/completions", token, _chat(a.model, "hi", 8)),
        "stream": ("POST", "/v1/chat/completions", token, _chat(a.model, "hi", 4, stream=True)),
        "models": ("GET", "/v1/models", token, None),
        "bad_request_400": (
            "POST",
            "/v1/chat/completions",
            token,
            _chat(a.model, "hi", 8, temperature=-5),
        ),
        "unknown_model_404": (
            "POST",
            "/v1/chat/completions",
            token,
            _chat("no-such-model", "hi", 8),
        ),
        "no_key_401": ("POST", "/v1/chat/completions", None, _chat(a.model, "hi", 8)),
    }
    results = {}
    for label, (method, path, tok, body) in probes.items():
        status, headers, text = _http(method, base + path, tok, body)
        if label == "stream":
            text = "\n".join(text.splitlines()[:2])
        try:
            parsed = json.loads(text)
            fields = sorted(parsed) if isinstance(parsed, dict) else None
        except ValueError:
            fields = None
        header_text = "\n".join(f"{k}: {v}" for k, v in headers.items())
        results[label] = {
            "status": status,
            "headers": {k: v for k, v in headers.items() if k.lower() != "authorization"},
            "top_level_fields": fields,
            "body": _scrub(text, secrets)[:1500],
            "markers_in_body": find_markers(text, markers),
            "markers_in_headers": find_markers(header_text, markers),
        }
    return {"markers_searched": markers, "responses": results}


def cmd_datastore_scan(a: argparse.Namespace) -> dict[str, Any]:
    base, token = a.base_url.rstrip("/"), os.environ.get(a.token_env or "", "") or None
    marker = f"EV08MARK{uuid.uuid4().hex[:12]}"
    before = parse_docker_diff(_docker("diff", a.container, timeout=60)["stdout"])
    status = _http(
        "POST",
        f"{base}/v1/chat/completions",
        token,
        _chat(a.model, f"จำรหัสนี้: {marker} แล้วตอบว่า รับทราบ", 16),
    )[0]
    time.sleep(2)
    after = parse_docker_diff(_docker("diff", a.container, timeout=60)["stdout"])
    before_paths = {r["path"] for r in before}
    new_rows = [r for r in after if r["path"] not in before_paths]
    changed = diff_search_roots(after)
    hits: list[str] = []
    if changed:
        grep = _docker(
            "exec",
            a.container,
            "sh",
            "-c",
            'grep -rlF "$0" "$@" 2>/dev/null; true',
            marker,
            *changed,
            timeout=120,
        )
        hits = [ln for ln in grep["stdout"].splitlines() if ln]
    logs = _docker("logs", a.container, timeout=60)
    inspect = _inspect(a.container)
    return {
        "marker": marker,
        "marker_request_status": status,
        "diff_entries_total": len(after),
        "search_roots": changed,
        "diff_entries_new_after_request": new_rows[:100],
        "diff_paths_sample": [r["path"] for r in after][:60],
        "changed_files_containing_marker": hits,
        "marker_in_docker_logs": marker in (logs["stdout"] + logs["stderr"]),
        "docker_log_driver": inspect.get("HostConfig", {}).get("LogConfig", {}).get("Type"),
        "docker_log_path": common.redact_text(inspect.get("LogPath", "")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token-env", default=None, help="NAME of the env var holding the key")
    parser.add_argument("--model", default="typhoon2.5-qwen3-4b")
    parser.add_argument("--container", default="prp-wp24-vllm-b")
    parser.add_argument("--candidate", default="B")
    parser.add_argument("--label", default="run")
    parser.add_argument("--out", default="wp24-out")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export")
    p.add_argument("--weights-dir", required=True)
    p.add_argument("--allow-env", action="append", default=["VLLM_WSL2_ENABLE_PIN_MEMORY"])
    p.add_argument("--secret-env", action="append", default=[])
    p = sub.add_parser("launch")
    p.add_argument("--spec", required=True)
    p.add_argument("--name", default="prp-wp24-vllm-b")
    p.add_argument("--key-env", action="append", default=[])
    p.add_argument("--secrets-dir", default=None)
    p.add_argument("--replace", action="store_true")
    p.add_argument("--ready-timeout", type=float, default=600.0)
    sub.add_parser("fingerprint")
    p = sub.add_parser("compare")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p = sub.add_parser("key-check")
    p.add_argument("--key-env", action="append", default=[])
    p.add_argument("--stage", required=True)
    sub.add_parser("leak-scan")
    sub.add_parser("datastore-scan")
    a = parser.parse_args()
    if a.cmd == "export" and a.token_env and a.token_env not in a.secret_env:
        a.secret_env.append(a.token_env)
    if a.cmd == "launch" and len(a.key_env) > 1 and not a.secrets_dir:
        parser.error("several --key-env need --secrets-dir (outside the repository)")

    handlers = {
        "export": cmd_export,
        "launch": cmd_launch,
        "fingerprint": cmd_fingerprint,
        "compare": cmd_compare,
        "key-check": cmd_key_check,
        "leak-scan": cmd_leak_scan,
        "datastore-scan": cmd_datastore_scan,
    }
    result = handlers[a.cmd](a)
    exit_code = result.pop("exit_code", 0) if isinstance(result, dict) else 0
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"ev08_{a.cmd.replace('-', '_')}_{a.candidate}_{a.label}_{stamp}.json"
    payload = common.redact_json(
        {
            "generated_at_utc": common.utc_now_iso(),
            "command_line": common.command_line(),
            "candidate": a.candidate,
            "ev": "EV08",
            "subcommand": a.cmd,
            "label": a.label,
            "result": result,
            "measurements": [],
            "observations": [],
            "source_observations": [],
            "artifacts": [name],
        }
    )
    path = common.write_json(Path(a.out), name, payload)
    print(f"wrote {path}")
    print(json.dumps(result, ensure_ascii=False, indent=1)[:3000])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
