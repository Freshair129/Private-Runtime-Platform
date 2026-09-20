"""Execution & Jobs (ARCH-PRP §2, §6).

Owns Invocation, Attempt, Job, DispatchOutbox and UsageReceipt. Exactly-once compute is not
promised: a result settles once, only when invocation, attempt, runtime epoch and content fence
match; UNKNOWN is a first-class execution state (ADR-PRP-005). Verification: FR-020/021/022/038/041,
D12/D13/D22.
"""
