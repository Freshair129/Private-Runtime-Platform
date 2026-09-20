"""Identity & Policy (ARCH-PRP §2).

Owns Organization, Principal, TeamMembership, Application, AccessKeyGrant and RBAC. Client keys
are stored as verifiers only (PRP-FR-005); nothing in this context ever holds or returns key
material. Verification: ADR-PRP-001, ADR-PRP-004 (FR-003/004/005/007/048, D05).
"""
