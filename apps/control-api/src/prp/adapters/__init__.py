"""Port implementations (SDD-PRP-REPO §6.1).

The only package allowed to import vendor SDKs, ORMs and HTTP clients. Empty in M3 by design:
adapters are added in M4 according to the WP24 fit-gap dispositions (REUSE / CONFIGURE / ADAPT /
BUILD-GAP), never before. Planned subpackages: persistence, runtimes, gateway, storage, telemetry.
"""
