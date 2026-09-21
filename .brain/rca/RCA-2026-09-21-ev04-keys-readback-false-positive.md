# RCA-2026-09-21-ev04-keys-readback-false-positive

**Symptom.** On its first real run, `tools/wp24/litellm_subspike/ev04_keys.py` reported
`plaintext_reappeared_any_channel: true` with the observation "FR-005 gate: plaintext reappeared
through at least one management endpoint after issuance -> FAIL per WP24-EXPERIMENT-PROCEDURE.md
section 5 EV04 criteria". Taken at face value this would have put a FAIL on `PRP-FR-005` for
candidate B's key layer.

**Evidence.**
- `ev04_keys.py:148` builds the readback request as
  `http_call("GET", f"{base_url}/key/info?key={plaintext_key}", bearer=master_key)`, so the
  plaintext key is sent by the script as a query parameter.
- The recorded response (`ev04_readback_attempts.redacted.json`) reports the plaintext at `$.key`
  and nowhere else; every other field in the body is a hash or metadata.
- Addressing the same endpoint by the key's sha256 hash instead returns 200 with the plaintext
  absent from the entire body; `$.key` then holds the hash that was asked with. The endpoint echoes
  its lookup argument.
- `LiteLLM_VerificationToken.token` holds 64 hex characters equal to `sha256(plaintext)`, and
  `key_name` holds only a redacted preview (`sk-...<last 4 chars>`). Storage is verifier-only.

**Root cause.** The script infers "the key can be read back" from the presence of the plaintext
anywhere in a response, without accounting for the plaintext it supplied itself in that same
request. `GET /key/info?key=<key>` is a lookup keyed by the secret, so its response necessarily
contains the caller's own input. The check therefore cannot distinguish disclosure from echo, and
on this endpoint it always reports disclosure.

FR-005 asks whether a party that does **not** hold the key can recover it. A readback test must
address the key by a non-secret handle — the hash, the alias, or a listing — which
`ev04_keys.py` never does.

**Escape analysis.** The kit was written and reviewed without a running proxy (it is labelled
TEMPLATE / NOT_QUALIFIED for exactly that reason), so the echo could not be observed. The script's
own docstring at lines 28-39 anticipates ambiguity about whether `token` holds plaintext or a hash
and resolves to "report what it actually observes" — a sound instinct that nonetheless left the
request shape unexamined. Its unit tests assert the reporting logic against synthetic responses, so
they reproduce the same blind spot.

**Fix.** Not applied in this run; the finding is recorded so the false FAIL never reaches the run
record. The change needed in `ev04_keys.py`:
1. Perform the readback by sha256 hash (and by `key_alias` where the endpoint supports it), never by
   the plaintext.
2. If a request must carry the plaintext, exclude the echoed field from the disclosure check and say
   so in the observation text.
3. Keep one deliberate plaintext-in-URL call, but repurpose it: its real value is proving whether
   the plaintext reaches the proxy log, which it does — that is the genuine disclosure channel and
   is currently not checked at all.
4. Add a unit test whose fixture is an echo response, asserting that it is **not** reported as
   disclosure.

**Prevention.** Any probe that decides a security property from string presence must state which
strings it supplied itself and exclude them. For WP24 specifically: a tool observation that names a
gate and a verdict word ("FAIL") is still an observation, and the procedure's rule that verdicts
belong to the reviewer (section 3 item 4) is what stopped this from being written into the record
as a gate verdict.
