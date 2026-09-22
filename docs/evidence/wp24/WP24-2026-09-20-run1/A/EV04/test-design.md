# EV04 test design for candidate A (Xinference)

Gate `PRP-FR-003`..`PRP-FR-009`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV04, steps 1–4.
Candidate B's EV04 is the comparison point (`../../B/EV04/` and the run record).

The runtime is the deployment from `../EV02/launch-command.txt`, **restarted with the default
auth path** (`XINFERENCE_AUTH_ADVANCED` left at its default) instead of the `0` used for EV02
steps 1–3.

## What reading the shipped code already shows, to be confirmed by running

`xinference/api/oauth2/advanced/` in the pinned install:

- `create_api_key_for_user` stores **both** `key_hash = sha256_hex(key)` **and** `key_encrypted =
  aes_encrypt(plaintext, encryption_key)`, plus a 7-character `key_prefix`;
- `reveal_api_key(key_id)` decrypts that copy and returns the plaintext;
- it is exposed as **`GET /v1/admin/keys/{key_id}/reveal`**, guarded by the `keys:manage` scope;
- the `api_keys` table carries `expires_at`, `enabled` and rate-limit columns, and
  `api_key_model_permissions` carries `permission_type` / `permission_value`;
- user passwords use bcrypt, and refresh tokens are stored as sha256 hashes.

The procedure says FR-005 fails the moment a key can be read back after issue, and names this as the
**known SRC-10 gap that this run must confirm rather than assume**. The run therefore tries the
route for real, and does not rest on the source reading alone.

## Steps

### Step 1 — create a key, then try to read it back through every channel

**Bootstrap** (owner approved 2026-09-22): `POST /v1/admin/setup` creates the first administrator on
this throw-away instance. The username and password are generated per run, kept in environment
variables, never printed and never written to any artifact; only the fact that a bootstrap was
required is recorded.

Then create one API key and attempt read-back through:

| channel | how |
|---|---|
| the reveal route | `GET /v1/admin/keys/{key_id}/reveal` |
| ordinary key reads | `GET /v1/admin/keys`, `GET /v1/admin/keys/{key_id}` |
| the auth database | the sqlite file under `XINFERENCE_HOME/auth`: does a row hold anything that recovers the key, and is the encryption key itself on disk beside it |
| config dump and logs | the server log and any config echo, searched for the key and its prefix |

Every channel is recorded as "plaintext recovered" or "not recovered". **The key value itself is
never written into an artifact**; the probe stores a boolean and, where relevant, the 7-character
prefix that the product itself treats as non-secret.

### Step 2 — how far a key can be scoped

Each `PRP-FR-003`..`009` requirement gets a row: what the candidate supports, from the API rather
than the documentation. Known columns to test: model permissions
(`permission_type` / `permission_value`), `expires_at`, `enabled`, per-key rate limits, user scopes
(`keys:create`, `keys:manage`, …). Listing behaviour is checked too: does a non-admin user's list
show only its own keys.

A second, non-admin user is created for that check, with the same per-run credential handling.

### Step 3 — revoke, and measure

Three measurements, each real:

1. delete (or disable) the key, then call `/v1/models` in a tight loop and record **how long until
   the first rejection**. The implementation keeps an in-memory cache keyed by the key hash, with
   `remove()` and `invalidate_user_keys()`, so the question is whether revocation is immediate or
   waits for a cache expiry;
2. whether an **access token** issued from `/token` before the revocation still works afterwards
   (`ACCESS_TOKEN_EXPIRE_MINUTES` governs it);
3. whether the refresh token can still mint a new access token after the user is disabled.

### Step 4 — first-admin bootstrap independence (FR-001)

Record what the bootstrap needed: no Zuri, FUNG or Lalin Studio, no external database, and where
its state lives (the sqlite file under `XINFERENCE_HOME`). Also record whether the two environment
variables the code demands for advanced auth (`XINFERENCE_AUTH_JWT_SECRET_KEY`,
`XINFERENCE_AUTH_ENCRYPTION_KEY`) must be supplied by the operator, since that is part of the same
bootstrap story.

## Tooling

No new repo tooling. The probe is a short scratch script kept outside the repository, and its
redacted JSON output plus a findings file are the artifacts. `tools/wp24/ev02_probe.py` is reused
for the endpoint sweep under the default auth path.

## What this cannot reach

- **Organisation / application scoping**: the schema has users and keys, not organisations, so the
  answer is expected to be "not supported"; the run records what exists rather than inventing it.
- **Quota**: the columns are rate limits, not token or cost quotas; again recorded as observed.
- OIDC is present in the package but out of scope for this run.
- One host (DEV-03), Windows-native deployment (DEV-07).

## Run precondition

No GPU work is needed: EV04 touches the control plane only, so the model does not have to be
loaded. The server runs with the default auth path for the whole experiment.
