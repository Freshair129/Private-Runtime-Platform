"""Contract models generated from contracts/openapi/*.yaml (ADR-PRP-013).

client_v1      server side of the public client contract (used by prp.api)
worker_v1      client side of the worker adapter contract (used by prp.adapters.runtimes)
management_v1  private management contract, DRAFT until WP03 (used by prp.api)

Only ``base.py`` is hand-written. Every ``*_v1.py`` module is a derived file produced by
``tools/contracts/gen_models.py``; edit the YAML and regenerate, never the module. This package sits
below the ``api | adapters`` layer so both may import it without importing each other.
"""
