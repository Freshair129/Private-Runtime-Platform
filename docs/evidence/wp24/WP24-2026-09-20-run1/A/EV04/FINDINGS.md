# EV04 — identity / key semantics, candidate A (Xinference)

Gate `PRP-FR-003`..`PRP-FR-009`. Operator observations only; no verdict is computed here. The design
is in `test-design.md`. Candidate B's EV04 is the comparison point.

Runtime: the EV02 deployment restarted with the **default auth path** (`XINFERENCE_AUTH_ADVANCED`
unset). The model was not loaded; EV04 touches the control plane only. Per-run credentials were
generated, held in environment variables and never written to any artifact. The probe output
(`ev04_a_probe_result.redacted.json`) records booleans, timings and the key prefix the product
itself treats as public, never a key or password.

## Step 1 — can an issued key be read back?

**Yes. `GET /v1/admin/keys/{key_id}/reveal` returned the plaintext key, and it matched the key
issued at creation.** The procedure says FR-005 fails the moment that is possible, and names it as
the SRC-10 gap this run must confirm rather than assume. It is now confirmed by execution, not by
reading the source.

| channel | plaintext recovered |
|---|---|
| `POST /v1/admin/keys` (creation) | yes, by design: the response carries `key` once |
| **`GET /v1/admin/keys/{key_id}/reveal`** | **yes** — 200, body `{"key": …}`, guarded only by the `keys:manage` scope |
| `GET /v1/admin/keys` (list) | no. Fields: `id`, `user_id`, `key_prefix`, `name`, `description`, `enabled`, `expires_at`, `model_permissions`, `owner_username`, `created_at` |
| `GET /v1/admin/keys/{key_id}` | no |
| `XINFERENCE_HOME/auth/auth.db` | not as plaintext: the row holds `key_hash` (sha256), `key_encrypted` (AES-GCM) and `key_prefix` |
| server log | no; the admin password did not appear either |

The mechanism, from the shipped code (`api/oauth2/advanced/`): `create_api_key_for_user` stores
**both** a sha256 hash and an AES-encrypted copy of the key; `reveal_api_key` decrypts that copy.

**Where the decryption key lives matters as much as the route.** The directory listing of
`XINFERENCE_HOME/auth/` is:

```
auth.db           57344 bytes
encryption_key       64 bytes
jwt_secret_key       64 bytes
```

The AES key sits **next to the database it protects**. Anyone who can read that directory — a
backup, a stray copy of the home directory, another process on the host — can decrypt every stored
key. So the read-back is not merely an API affordance that could be firewalled off; the data model
is reversible by design.

For PRP this settles the question the way ADR-PRP does: PRP must be the client-key authority and
keep verifier-only keys. Candidate A cannot hold them.

## Step 2 — how far a key can be scoped

| requirement | what candidate A offers | observed |
|---|---|---|
| FR-003 issuing | `POST /v1/admin/keys` with `name`, `description` | 201, key returned once |
| FR-004 scope by model | `api_key_model_permissions` rows: `permission_type` / `permission_value`, default `all` | set `model` → `prp-a-llm`, 200, visible on read-back of the key record |
| FR-005 storage | **reversible** (see step 1) | **fails** |
| FR-006 expiry | `expires_at` on the key | set to 2027-01-01, 200, visible |
| FR-007 quota | **no quota**. The columns are failure-based rate limits: `rate_limit_max_failures`, `rate_limit_window_seconds`, `rate_limit_ban_seconds` | set, 200. No token, request or cost quota exists |
| FR-008 organisation / application | **no such concept**. The schema has users and keys only | — |
| FR-009 revoke | `DELETE /v1/admin/keys/{id}`, plus an `enabled` flag | see step 3 |

User-level scopes exist and are real: the vocabulary in the shipped code is `admin`, `keys:create`,
`keys:manage`, `users:manage`, `models:list`, `models:read`, `models:write`, `models:register`,
`cache:list`, `cache:delete`, `virtualenv:list`, `virtualenv:delete`.

**Listing is properly isolated.** A second, non-admin user was created and logged in: its
`GET /v1/admin/keys` returned **403**, and `GET /v1/admin/keys/{id}/reveal` on the admin's key also
returned **403**. A key holder cannot enumerate or reveal another user's keys; only a
`keys:manage` holder can.

## Step 3 — revocation, measured

| measurement | value |
|---|---|
| key works before revoke | 200 |
| `DELETE /v1/admin/keys/{id}` | 200 |
| **time until the next request with that key was rejected** | **0.037 s**, on the very first attempt |
| access token issued earlier, after the key was deleted | still 200 — a separate credential, as expected |
| deleting the **user**: time until its access token was rejected | **0.012 s**, first attempt |
| refresh token after the user was deleted | **401** |

Revocation is immediate in both cases: the in-memory cache is invalidated on the write path rather
than expiring on a timer. That is better than candidate B's bare vLLM, which has no revoke API at
all and requires a restart (EV04 candidate B).

## Step 4 — first-admin bootstrap (FR-001)

- `GET /v1/admin/setup/status` returned `needs_setup: true` on a fresh home directory; after
  `POST /v1/admin/setup` it returned `needs_setup: false, initialized: true`, and a second setup
  attempt was refused with **403**. The bootstrap is single-shot.
- It required **no Zuri, FUNG or Lalin Studio and no external database**: state lives in
  `XINFERENCE_HOME/auth/auth.db`, a local sqlite file. FR-001 independence holds for this step.
- The operator must supply two secrets for advanced auth, `XINFERENCE_AUTH_JWT_SECRET_KEY` and
  `XINFERENCE_AUTH_ENCRYPTION_KEY`; the server also persists key material as the two 64-byte files
  shown above.
- Login is `POST /token` with a **JSON** body. It is not the OAuth2 form encoding the path name
  suggests: a form-encoded request returns **500** with a JSON decode error, not a 4xx. An
  integration written from the endpoint name alone will fail confusingly.

## Comparison with candidate B

| question | A (Xinference) | B (bare vLLM) | B with LiteLLM |
|---|---|---|---|
| key read-back | **yes, by API and by design** | n/a: one static key list, no issuing | hashed; plaintext only if the caller puts it in a `/key/info` URL |
| scopes | model permission, expiry, user scopes | none at all | model, budget, expiry, alias |
| quota | rate limits only | none | budgets |
| org / app | none | none | teams |
| revoke | **immediate, 0.037 s** | no API; restart required | API |
| bootstrap | local sqlite, single-shot, no external DB | n/a | its own database |

## Limits of this run

- One host (DEV-03) and a Windows-native deployment (DEV-07).
- OIDC, which the package also ships, was not exercised.
- The audit log table was not examined beyond noting that it records `api_key_prefix`, not the key.
- Rate limits were set but not driven to their trigger.
