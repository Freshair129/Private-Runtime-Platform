"""Registry & Qualification (ARCH-PRP §2).

Owns Node, RuntimeDeployment, ModelProfile, QualificationReceipt, physical identities and epochs.
A node is eligible only with a PASS receipt for its current epoch and ENABLED state (OPS-PRP RB02,
API-PRP §8 resume rule). Verification: ADR-PRP-006, D04/D18 (FR-018/044/050).
"""
