"""Hand-written Literal aliases in prp_voice.contract.models never drift from generated fields."""

from typing import get_args

from prp_voice.contract import generated, models


def test_literal_aliases_equal_generated_field_types() -> None:
    pairs = [
        (models.ErrorCode, generated.ErrorBody, "code"),
        (models.ReadinessValue, generated.Readiness, "state"),
        (models.EvidenceValue, generated.ExecutionEvidence, "evidence"),
        (models.CancelValue, generated.CancelResult, "disposition"),
    ]
    for alias, model, field in pairs:
        assert get_args(alias) == get_args(model.model_fields[field].annotation), (
            model.__name__,
            field,
        )


def test_models_module_only_re_exports_generated_classes() -> None:
    for name in models.__all__:
        exported = getattr(models, name)
        if isinstance(exported, type):
            assert exported is getattr(generated, name), name
