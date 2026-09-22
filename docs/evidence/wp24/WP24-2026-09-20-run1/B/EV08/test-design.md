# EV08 test design on a single GPU host

Gate `PRP-NFR-024` (portable framework binding and exit). Procedure:
`docs/WP24-EXPERIMENT-PROCEDURE.md` EV08, steps 1–4.

The runtime is candidate B launched as in `../EV05/launch-command.txt`. By the sub-spike decision,
**LiteLLM is not run in EV08**. Its key and proxy findings from EV03 / EV04 are cited in the step 3
plan, but never re-run here.

## Step 1 — mapping, and what the vendor would leak into the public contract

**Mapping table (a document, no runtime needed).** Each row runs down four layers, from the client
to the vendor:

| layer | example | owned by |
|---|---|---|
| client `model` string | `prp-chat-th-small` | PRP, public |
| `ModelProfile` | `id`, `revision` = `typhoon-ai/typhoon2.5-qwen3-4b@ce0a741`, `profile_hash` | PRP |
| `RuntimeDeployment` | `node_id`, `profile_epoch`, `manager_uid` | PRP |
| vendor identifiers | vLLM `--served-model-name`, the `/models` mount path, the image digest | vLLM |

The columns are taken from `apps/control-api/src/prp/core/fleet/model.py` and
`contracts/openapi/prp-worker.yaml`. The worker contract already says "the control plane owns
alias → profile mapping".

**Contract check (no runtime).**

- `prp-client.yaml` must name no vendor model ID, manager schema or vendor datastore.
- A grep for vendor names is recorded (it currently finds none).
- `validate_docs.py` confirms the client inventory is unchanged: 12 paths, 14 operations.

**Leak scan (runtime).** A probe sends one of each response kind straight to vLLM and lists every
field or header that identifies the vendor or its topology:

- a chat completion;
- one stream chunk;
- `GET /v1/models`;
- a 400 (bad parameter);
- a 404 (unknown model);
- a 401 (no key).

The result is the **strip / rewrite list** a PRP adapter must apply, e.g. the response `model` field
echoing `--served-model-name`, `id` prefixes, `system_fingerprint`, `server` headers and error-body
text. EV03 found LiteLLM's error bodies leak hosts and ports, so this checks vLLM's own error
bodies.

## Step 2 — export, and import from the export alone

- **Export.** `docker inspect` of the running container is turned into a declarative spec:
  - image digest;
  - command-line arguments;
  - environment variable **names**, with every value redacted except a declared allow-list of
    non-secret switches (`VLLM_WSL2_ENABLE_PIN_MEMORY`);
  - port binding and mounts;
  - sha256 of the weight-directory files that define the model: `config.json`, `tokenizer.json`,
    `chat_template.jinja`, `generation_config.json`, and the safetensors index.

  The export must hold no plaintext key; the probe checks that as part of the export.
- **Import.** The first container is removed. A second one is launched **only from the export
  file**, with a new key supplied at launch, since the export cannot carry one.
- **Compare.** The two runs are then compared on:
  - vLLM's startup `non-default args`;
  - `/v1/models` (ignoring `created`);
  - the `vllm:cache_config_info` labels;
  - the text of one fixed greedy completion (`temperature 0`, `seed` fixed, `max_tokens` 64).

**Deviation (proposed DEV-06).** "Import on a clean host" can only be approximated. The only other
machine (the RTX 3060 host) runs Ollama and has no Docker GPU runtime. Setting one up is outside
this task. The import therefore runs as a **new container with no cache**, on the same host.

## Step 3 — key rotation plan (a document, plus one runtime check)

- **Plan.** It rests on EV04 and the ADR rule of one client-key authority:
  - client keys belong to PRP's verifier, so a framework exit never touches client keys;
  - the vLLM `--api-key` is an internal worker credential (`credential_ref` in the management
    contract);
  - bare vLLM takes a *list* of keys but has no revoke API, so a rotation is: restart with
    old + new → move the adapter to new → restart with new only;
  - each restart costs the ready time EV06 measured (about 93 s warm) unless a second replica
    carries traffic (DEV-03);
  - the LiteLLM layer's rotation (hash-addressed keys, `/key/regenerate`) is summarised from the
    EV04 evidence, not re-run.
- **Runtime check.** The imported container is launched with two keys, then restarted with the new
  key only. At each stage the probe records old key / new key / no key → HTTP status on
  `/v1/chat/completions`. This proves the overlap-then-drop sequence works.

## Step 4 — where job data could end up outside PRP's deletion fence

After serving a request that carries a unique marker string, the probe records:

- `docker diff` of the container: every file vLLM wrote, and whether any contains the marker;
- whether the marker appears in `docker logs`, which Docker keeps in a host-side log file that PRP
  would have to fence;
- the Responses API store: off by default (EV06), so nothing is kept unless it is enabled;
- vLLM's in-memory prefix cache. It is noted as volatile: it cannot be deleted on request, but it
  does not survive a restart (EV06).

The output is a list of vendor-held datastores, each marked persistent, volatile or absent.

## Tooling

`tools/wp24/ev08_exit_probe.py` (design approved by the owner 2026-09-22), stdlib only, same conventions as EV05 / EV06 (redaction,
`--token-env`, one JSON output, no verdict). Subcommands:

| subcommand | does |
|---|---|
| `export` | `docker inspect` → redacted spec, plus weight-file hashes; fails if any key value survives redaction |
| `leak-scan` | the six responses in step 1, and the vendor-identifying fields and headers found in each |
| `fingerprint` | startup args, `/v1/models`, `cache_config_info` and the fixed greedy completion, for step 2's compare |
| `compare` | diffs two fingerprints |
| `key-check` | status per key for step 3, with key values taken from env var names only |
| `datastore-scan` | the marker request, `docker diff`, and a marker search in changed files and logs |

Unit tests cover the pure parts: env redaction, fingerprint diff, and vendor-field detection.

Three details were settled while writing the tool, from reading the vLLM source in the image:

- **Several keys at once.** `VLLM_API_KEY` holds a single key
  (`entrypoints/serve/middleware/register.py`), so the step 3 overlap stage needs `--api-key k1 k2`.
  On the command line that would put both keys into `docker inspect`. vLLM's `--config <yaml>`
  (`utils/argparse_utils.py`) turns a YAML list into repeated arguments, so `launch` writes
  `api-key: [...]` to a file outside the repository and mounts it read-only. `key-check` then
  records whether either key shows up in `docker logs` (vLLM logs its `non-default args` at
  startup) or in `docker inspect`.
- **The command comes from `Config.Cmd`, not `Args`.** `Args` drops the program when the command
  replaced the image's own. The entrypoint is recorded only when it differs from the image's.
- **Windows bind sources** reported as `/run/desktop/mnt/host/<drive>/…` are converted back to
  `<DRIVE>:/…`, so the spec can be launched as-is.

### Dry run (validates the tool only; not evidence about vLLM)

Every subcommand was run against the stdlib fake server from EV06, in a `python:3.12-alpine`
container, with two throw-away keys:

- `export` → `launch` → `fingerprint` → `compare`: the relaunch from the spec alone matched the
  source on all four fields.
- `launch` with two keys used the `--config` route.
- No key value appeared in any output file.

The dry run caught three bugs, fixed before this commit:

- the command was taken from `Args`, which dropped the program;
- `launch` read the spec from the wrong level of the export file;
- the export redacted a home-directory mount path, which only matters for mounts under a user
  directory; the vLLM weights mount is on `F:/`.

It also showed one behaviour worth checking on vLLM: with one key passed through the environment,
`key-check` found the key value in `docker inspect` (`Config.Env`); through the `--config` file it
did not.

## What this cannot reach

- **A truly clean second host** (proposed DEV-06).
- **Fake-adapter replacement through client conformance** (NFR-024 acceptance). It needs PRP's
  adapter layer (M4). The mapping table and strip list are its inputs, not its proof.
- **Replay of approved synthetic workloads through a replacement candidate.** Candidate A has not
  run (DEV-02).

## Run precondition

The GPU must be free (about 11 GB). There are two launches (export source, then import), each cold
or warm at about 1.5–4.5 min, plus two restarts for the key check. Start the container only on the
owner's go-ahead, and stop it afterwards.
