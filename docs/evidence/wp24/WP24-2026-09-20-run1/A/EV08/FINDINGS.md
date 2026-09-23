# EV08 — adapter / exit, candidate A (Xinference)

Gate `PRP-NFR-024`. Operator observations only; no verdict is computed here. The design is in
`test-design.md`. Candidate B's EV08 is the comparison point; it ended at ADAPT with a strip/rewrite
list PRP has to carry.

Runtime: the EV02 deployment, `shared_revision`, auth **on** (step 3 is about the candidate's own
keys). The import in step 2 used a **fresh `XINFERENCE_HOME` and port 9998** on this host, since
DEV-06 records that no clean second host is available.

## Step 1 — the mapping, and what leaks

**The public contract does not have to change.** `contracts/openapi/prp-client.yaml` contains **no**
occurrence of `xinference`, `vllm`, `xoscar`, `typhoon`, `qwen` or `litellm`, and the client
inventory is unchanged at **12 paths / 14 operations** with `info.version 0.3.0`.
`tools/docs/validate_docs.py` reports 0 errors.

| PRP concept | candidate A name in this run | leaks to the client? |
|---|---|---|
| public model name in `ModelProfile` | `model_uid` = `prp-a-llm` | the `model` field echoes the UID, so **PRP chooses it**; keep it equal to the public name and nothing vendor-shaped appears |
| `ModelProfile` revision (`typhoon-ai/typhoon2.5-qwen3-4b@ce0a741`) | registration `model_name` = `prp-typhoon25-qwen3-4b`, `model_specs[].model_uri` | only in `/v1/models`, never in a completion |
| engine / runtime kind | `model_engine: transformers`, `model_format: pytorch`, `model_family: qwen3` | `/v1/models` only |
| replica identity | `<uid>-rep<n>`, `address`, `accelerators` | `/v1/models` and `/v1/workers` |
| capacity control | `request_limits` (EV05) | not in `/v1/models` at all |

**What an adapter must strip or rewrite**, measured on live responses:

| response | vendor content found |
|---|---|
| chat completion **body** | **none**. `model` echoed the PRP-chosen UID; no vendor word appears. The `id` is `chatc…` (OpenAI-shaped, not vendor-shaped) |
| chat completion **headers** | `server: uvicorn` — the same infrastructure leak candidate B had |
| `/v1/models` | `xinference`, `typhoon`, `qwen`, `transformers`, `pytorch` all appear (`owned_by`, `model_name`, `model_engine`, `model_format`, `model_family`) |
| **error body** | the internal actor address and pid, the offending uid, and **a list of every model uid on the cluster** |

The error case is the sharpest finding. A candidate error carries `[address=127.0.0.1:57403,
pid=66248]` together with `Available model uids: [...]`, so it discloses internal topology and every
other model name on the cluster. Passing that through would leak both to a caller. PRP's adapter
must replace candidate error bodies wholesale rather than forward them, which is a stronger
requirement than candidate B's, where the leak was limited to headers and ids.

Since every client schema sets `additionalProperties: false`, none of this can pass through by
accident; the adapter must map explicitly, which is the behaviour NFR-024 wants.

## Step 2 — export and re-import

The exported bundle is `config-export/` (5 files): `environment.env` with **secrets redacted**,
`model-registration.json`, `launch-params.json`, `state-files-inventory.txt` and the captured
`reference-from-source.json`. No key material is in the bundle; the inventory marks
`auth/auth.db`, `encryption_key` and `jwt_secret_key` as holding secrets and **not exported**.

A second instance was then brought up **from the bundle alone**, on a fresh home directory and port,
with newly generated secrets:

| check | result |
|---|---|
| new instance answered | **31.2 s** |
| bootstrap, registration, launch | 201 / 200 / 200, launch took **49.3 s** |
| `/v1/models` field set | **identical** to the source |
| full model record (minus `address`, `created`) | **identical**, no differences |
| fixed greedy answer | `2, 3, 5, 7, 11` on both — **identical** |
| token usage | 18 / 14 / 32 on both — **identical** |

So the deployment is fully described by a small declarative bundle plus the weights. Nothing had to
be copied out of the running instance's state, and the only host-specific steps were generating new
secrets and creating the weights **junction** (the Windows detail EV02 found).

## Step 3 — key rotation, executed

| step | result |
|---|---|
| issue key 1, use it | 201, then 200 |
| issue key 2 while key 1 lives | 201 |
| **overlap window**: both keys | key 1 **200**, key 2 **200** |
| delete key 1 | 200 |
| old key refused after | **0.027 s** |
| after rotation | key 1 **401**, key 2 **200** |
| restart needed at any step | **no** |

Rotation by overlap-then-drop works entirely online. Candidate B needed a **new container for each
key change**; candidate A needs none.

**The rotation plan.** EV04 established that candidate A's key store is reversible (a `reveal`
route plus the AES key beside the database), so client keys stay with PRP as verifier-only. That
gives two separate rotations:

1. **PRP client keys** — rotated entirely inside PRP. Clients see nothing, and the candidate is not
   involved, because it never holds a client key.
2. **The candidate's administrative keys** — the ones PRP itself uses to drive Xinference. Rotate by
   the overlap sequence measured above: issue the new key, switch PRP's configuration to it, delete
   the old one, confirm the old one 401s. No downtime and no client-visible change. Because EV04
   showed the store is reversible, these keys must be treated as **exposed to anyone who can read
   the auth directory**, so rotation should be routine and the directory access-controlled.

## Step 4 — where job data lands

A marker request (`PRP-EV08-MARKER-…`) was sent, then **57 562 files** under `XINFERENCE_HOME` and
the virtual environment were scanned (the whole tree, not a sample; the weights junction was
excluded deliberately).

- **5 files changed** after the marker timestamp: `logs/audit.log`, `logs/xinference.log` in the
  home directory, the same two under the venv, and the run's own server log.
- **0 files contained the marker.** No prompt or response content reached any datastore or log.

Datastores the vendor owns, all local files under `XINFERENCE_HOME`:

| file | holds |
|---|---|
| `auth/auth.db` | users, API keys (hash **and** reversible copy — EV04) |
| `auth/encryption_key`, `auth/jwt_secret_key` | key material, beside the database |
| `launch_history.db` | model launch history |
| `monitor_config.db` | monitor configuration |
| `token_routers.db` | token-router configuration |
| `download_tasks.db` | model download tasks |

Nothing leaves the host: every listener is loopback-bound (EV05) and no external datastore is
involved. PRP can therefore fence deletion by owning the directory, with one caveat already
recorded: `auth.db` plus the key file beside it means deleting a key requires deleting it from a
store that can be decrypted by anyone holding the directory.

## What PRP has to carry

- An adapter that **replaces candidate error bodies entirely** — they carry the internal address,
  pid and every model UID on the cluster.
- Header handling for `server: uvicorn`, exactly as candidate B needed.
- Keep `model_uid` equal to the public model name, so the echoed `model` field never leaks anything.
- Rotate the candidate's administrative keys by overlap-then-drop (no restart needed) and treat the
  auth directory as sensitive.
- Keep the export bundle as the source of truth for redeployment; it reproduced the deployment
  exactly.

## Limits of this run

- **DEV-06**: the re-import was on this host with a fresh home and port, not a clean second machine.
  It proves the bundle is self-contained, not that it ports to different hardware.
- **DEV-07**: the exported environment is Windows-shaped (the junction step would differ elsewhere).
- PRP's adapter layer does not exist before M4, so the strip/rewrite list is recorded as a
  requirement on PRP rather than exercised through a conformance test.
- Only one marker request was traced; a long-running instance under real load was not observed.
