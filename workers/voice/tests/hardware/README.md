# tests/hardware

Physical GPU / voice-quality tests (Coding-Standards §10 tier "physical GPU/voice quality"). Mark every test here with `@pytest.mark.hardware`; CI in the cloud never collects this directory. Runs only on a self-hosted runner attached to the qualified host, and every run must produce a receipt in `docs/evidence/` before any acceptance status leaves NOT_RUN (SDD-PRP-REPO §9).

No tests yet: engines arrive at M4.
