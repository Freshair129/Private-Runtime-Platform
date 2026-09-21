# EV04 — identity / key semantics, candidate B

Gate `PRP-FR-003`..`PRP-FR-009`. Operator observations; no verdict is computed here.

Candidate B's key layer has two parts and they behave differently, so they are recorded separately:
bare vLLM (the engine's own `--api-key`) and the LiteLLM proxy that the owner scoped into WP24 as
candidate B's key/proxy layer.

## Part 1 — bare vLLM `--api-key`

Read from the image's own source, then confirmed against the route table captured at EV02.

`vllm/entrypoints/serve/middleware/authenticate.py`:

```python
GUARDED_PREFIX = ("/v1", "/v2", "/inference", "/cohere")
...
self.api_tokens = [hashlib.sha256(t.encode("utf-8")).digest() for t in tokens]
...
token_match |= secrets.compare_digest(param_hash, token_hash)
```

- The key **is** hashed in memory and compared in constant time, so in-process it behaves as a
  verifier.
- It is **not** verifier-only end to end: the plaintext must be supplied through `--api-key` or
  `VLLM_API_KEY` and stays in the process environment. `docker inspect --format '{{json .Config.Env}}'`
  returned the exact key in plaintext (verified by exact-match comparison; the value was never
  printed).
- `api_key: list[str]` accepts several keys but carries **no scope at all**: no organization,
  application, model, capability, expiry or quota. Revocation means restarting the server.
- `vllm/entrypoints/launchers/cli_args.py:290` states the limitation in its own docstring:
  `/invocations` "exposes the same inference capabilities as `/v1`" and stays unauthenticated.
- 16 routes in the EV02 route table sit outside `GUARDED_PREFIX`, including `POST /invocations`,
  `POST /tokenize`, `POST /detokenize`, `POST /generative_scoring`, `POST /scale_elastic_ep`,
  `POST /is_scaling_elastic_ep`, `GET /metrics`, `GET /load`, `GET /version`, `GET /docs`,
  `GET /openapi.json`.

Empirical confirmation that `POST /invocations` serves inference without a credential is **not yet
taken**; it is batched with EV03, which needs the runtime up anyway (owner decision 2026-09-21).

## Part 2 — LiteLLM proxy (v1.90.2) virtual keys

Brought up with `postgres:16`, master key and database password generated per run and kept outside
the repository. Proxy reached `/health/liveliness` 200 in about 21 s.

### Storage is verifier-only — the tool's FR-005 reading is a false positive

`tools/wp24/litellm_subspike/ev04_keys.py` reported `plaintext_reappeared_any_channel: true` at
`$.key` of `GET /key/info` and concluded "FR-005 gate ... FAIL". That conclusion is **not supported
by the evidence**: line 148 of that script calls
`GET /key/info?key=<plaintext_key>`, so the plaintext in the response is the script's own query
parameter echoed back, not a value recovered from storage.

Addressed the way a caller who does *not* hold the key would have to address it — by the sha256
hash — the plaintext never appears:

| check | result |
|---|---|
| `LiteLLM_VerificationToken.token` column | 64 hex chars, **equals `sha256(plaintext)`**, no `sk-` prefix |
| `LiteLLM_VerificationToken.key_name` column | redacted preview only, `sk-...<last 4 chars>` |
| `GET /key/info?key=<sha256 hash>` | 200; plaintext absent from the whole response body; `$.key` is the hash that was asked with |
| `GET /key/list` | 200; no plaintext (the tool agrees on this one) |

So LiteLLM stores and serves virtual keys as hashes. FR-005 is not failed by the storage design.

### The real disclosure channel is the documented lookup convention

LiteLLM's documented lookup is `GET /key/info?key=<key>`, which puts the plaintext key in the URL.
Calling it that way once and then searching the proxy container log found the plaintext key in the
log exactly once. The same call addressed by hash leaves nothing.

This is a configuration and integration constraint, not a storage defect: PRP (or any operator)
must address `/key/info` by hash and must keep the plaintext out of URLs, or every access log,
reverse proxy and log shipper in the path becomes a key disclosure channel.

### Revocation is immediate

`POST /key/delete` returned 200 and the revoked key was already rejected by `GET /v1/models` on the
first poll, 0.000 s later at a 0.2 s polling interval. No grace window was observed.

### Scope and privilege boundaries

Key generation echoed and enforced `models`, `expires`, `max_budget`, `tpm_limit`, `rpm_limit` and
`key_alias`; `/key/info` additionally exposes team, organization, project and budget fields.

| caller | route | status |
|---|---|---|
| virtual key | `GET /v1/models` | 200 (its own scope) |
| virtual key | `GET /key/list` | **403** — cannot enumerate keys |
| virtual key | `POST /key/generate` | **401** — cannot mint a key, no privilege escalation |
| virtual key A | `GET /key/info?key=<hash of key B>` | **200** — returns key B's alias, models, expiry, budget and spend |

`/key/list` is properly restricted but `/key/info` is **not scoped per key**: any valid virtual key
can read another key's metadata once it knows that key's hash, and LiteLLM's own documentation
describes that hash as the value stored as `user_api_key_hash` in spend logs. No plaintext is
disclosed, but the tenant boundary FR-006..FR-009 would expect is not enforced on this route.

### Bootstrap independence (FR-001)

The proxy and its database were brought up from nothing with only a generated master key and a
Postgres instance: no Zuri, FUNG or Lalin Studio component, and no business database, was involved.

## Clean-up

Both test keys were deleted through `POST /key/delete` (200 each) and
`SELECT count(*) FROM "LiteLLM_VerificationToken"` returned 0 afterwards. No key value, master key
or database password appears in any file in this directory.
