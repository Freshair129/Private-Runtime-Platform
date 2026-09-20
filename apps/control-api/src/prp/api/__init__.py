"""HTTP surface bound to contracts/openapi/prp-client.yaml (SDD-PRP-REPO §6).

Thin: request id, error envelope, auth facade and routes. Translates between contract models and
core types; never imports adapters (wiring happens in ``prp.entrypoints``). FastAPI is the first
evaluation candidate per ARCH-PRP §3; an endpoint is not implemented merely because FastAPI can
render an OpenAPI page for it (API-PRP addendum).
"""
