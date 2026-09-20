"""Hand-written base for generated contract models (ADR-PRP-013 rule 4)."""

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Reject unknown fields and never mutate a validated payload.

    Numeric and boolean strictness comes from the generator's StrictInt / StrictFloat / StrictBool,
    not from a global strict mode, so JSON strings for UUID and date-time fields stay accepted on
    the FastAPI validation path (Coding-Standards 3).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
