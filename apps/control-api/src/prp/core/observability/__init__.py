"""Observer & Audit (ARCH-PRP §2).

Owns normalized observations, usage and audit facts and alert rules. The critical observer runs
as its own process, independent of any dashboard. Audit and usage records carry metadata only,
never raw content (Coding-Standards §8). Verification: FR-044/046, D18/D22.
"""
