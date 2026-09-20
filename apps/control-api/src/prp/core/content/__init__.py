"""Artifact Service (ARCH-PRP §2, API-PRP §6).

Owns Artifact, ArtifactGrant and ErasureTombstone: uploads, TTL, lineage, explicit share grants
and erasure. Reads are authorized by organization and principal grants, never by filename hashes;
shared storage does not imply shared authorization (ARCH-PRP §8). Verification: ADR-PRP-007
(FR-028/039..041, SEC-008/009).
"""
