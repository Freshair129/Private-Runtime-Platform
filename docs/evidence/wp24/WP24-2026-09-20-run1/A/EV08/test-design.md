# EV08 test design for candidate A (Xinference)

Gate `PRP-NFR-024` (adapter / exit). Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV08, steps 1–4.
Candidate B's EV08 (`../../B/EV08/`) is the comparison point; it ended at ADAPT, with an adapter
strip/rewrite list PRP has to carry for every vLLM response.

The question is the exit question: **if PRP adopts this candidate, does the public contract have to
change, and can everything be moved out again.**

Runtime: the EV02 deployment, `shared_revision`. Auth is **on** for step 3, since that step is about
the candidate's own keys, and a **fresh `XINFERENCE_HOME`** is used for the import test in step 2.
No new deviation is expected; DEV-06 (no clean second host) already covers the import being done on
this host rather than another.

## Step 1 — mapping, and what vendor content leaks

Two parts:

1. A mapping table from what the candidate calls things (`model_uid`, `model_name`, the registration
   family, `model_family`, the replica UID form `<uid>-rep<n>`) to PRP's `ModelProfile` and the
   public model name, showing that **no vendor identifier needs to appear in `prp-client.yaml`**.
   `tools/docs/validate_docs.py` then confirms the client contract is unchanged, and the client
   inventory is checked against the same 12 paths / 14 operations it has held since v0.2.0.
2. The same check candidate B needed: **what vendor content the candidate puts in a response** that
   PRP's adapter would have to strip or rewrite, given every client schema sets
   `additionalProperties: false`. Headers and bodies of a chat completion, a model listing and an
   error are captured and compared field by field against the public schema.

## Step 2 — export the configuration, re-import it clean

Candidate A's configuration is not a single file. What defines this deployment is:

- the **environment** (`XINFERENCE_HOME`, the auth switch, the two auth secrets, batching and
  recovery variables);
- the **custom model registration** posted to `/v1/model_registrations/LLM` (family, context length,
  chat template, `model_specs` pointing at the weights);
- the **launch parameters** (`model_uid`, engine, format, size, quantization, `n_gpu`,
  `request_limits`, `replica`);
- the **state files** under `XINFERENCE_HOME` (`auth/auth.db`, `launch_history.db`,
  `monitor_config.db`, `token_routers.db`, `download_tasks.db`) and the model cache.

The run exports all of it into a **redacted** bundle (secrets replaced with placeholders, no key
material), then brings up a second instance on a **fresh `XINFERENCE_HOME` and a different port**
from that bundle alone, and checks it matches the source on: the registration read back, the fields
`/v1/models` reports, and a **fixed greedy answer** to the same prompt (`temperature: 0`), which is
the same equivalence check candidate B used.

## Step 3 — key rotation without the client knowing

EV04 established that candidate A's key store is reversible, so PRP must be the client-key
authority; this step therefore covers the keys that would remain in the candidate for its **own**
administrative access. The rotation is executed, not just written:

1. issue key 1, confirm it works;
2. issue key 2 while key 1 is still valid — confirm **both** work (the overlap window);
3. delete key 1 — confirm key 1 is refused and key 2 still works, and measure the gap;
4. record whether any step required a restart (candidate B needed a new container for each key
   change).

The written rotation plan then states what PRP does when its own verifier-only keys rotate, and what
it does with the candidate's administrative keys.

## Step 4 — where job data lands, and whether PRP can fence deletion

A **marker request** with a unique string is sent, then every file under `XINFERENCE_HOME` and the
venv that changed after a recorded timestamp is scanned for that marker, so the answer is measured
rather than assumed. Recorded: which datastores the vendor owns, whether prompt or response content
reaches any of them, and whether anything leaves the host.

Candidate B's run found its own scan initially covered only part of the diff; this design avoids
that by walking the whole tree under `XINFERENCE_HOME` and the venv rather than sampling, and by
recording the file count scanned.

## What this cannot reach

- **DEV-06**: no clean second host, so the re-import is on this host with a fresh home directory and
  port. It proves the bundle is sufficient and self-contained; it does not prove portability to
  different hardware.
- **DEV-07**: Windows-native deployment, so the exported environment is Windows-shaped.
- PRP's adapter layer does not exist before M4, so the strip/rewrite list is recorded as a
  requirement on PRP, not exercised.
- Nothing here changes the public contract; if anything demanded that, it would be a finding, not an
  edit.
