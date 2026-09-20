"""Bounded contexts of the PRP control plane, one per ARCH-PRP §2 ownership row.

access        Identity & Policy
fleet         Registry & Qualification
scheduling    PRP Router (select) + Admission Coordinator (reserve)
execution     Execution & Jobs
content       Artifact Service
observability Observer & Audit

Pure Python: contexts import only ``prp.platform`` and each other's declared ports/value types.
No framework, ORM or vendor SDK import is allowed here (import-linter enforces it).
"""
