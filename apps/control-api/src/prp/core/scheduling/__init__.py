"""PRP Router and Admission Coordinator (ARCH-PRP §2, §5).

Router filters and ranks eligible candidates; it never reserves. Admission atomically holds
quota, queue and physical budgets; dispatch sends only reserved attempts (ADR-PRP-002).
QuotaReservation, ModelResidency and InvocationLease are distinct objects: request completion
releases the lease, never the residency. Verification: FR-013/016..022/044, D12/D13/D33.
"""
