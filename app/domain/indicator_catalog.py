"""Conservative starter catalog for legacy EGT indicators.

This catalog preserves requested identifiers and reported units while leaving
technical meaning and formulas unapproved until engineering validates them.
"""
from app.domain.indicators import IndicatorDefinition, IndicatorStatus


def legacy_indicator_catalog() -> tuple[IndicatorDefinition, ...]:
    """Return draft definitions; this function never supplies calculation formulas."""
    return (
        IndicatorDefinition(
            code="Paf",
            name="Paf — indicador legado",
            unit="kg/m²",
            description="Sigla e unidade referenciadas em material legado. Numerador, denominador e escopo aguardam validação da engenharia.",
            status=IndicatorStatus.DRAFT,
        ),
        IndicatorDefinition(
            code="Pap",
            name="Pap — indicador legado",
            unit="kg/m²",
            description="Sigla e unidade referenciadas em material legado. Numerador, denominador e escopo aguardam validação da engenharia.",
            status=IndicatorStatus.DRAFT,
        ),
        IndicatorDefinition(
            code="Ecm",
            name="Ecm — indicador legado",
            unit="m³/m² (provisória)",
            description="Unidade citada como referência no projeto; confirmar a notação e a definição técnica antes de utilizar.",
            status=IndicatorStatus.DRAFT,
        ),
        IndicatorDefinition(
            code="Af",
            name="Af — indicador legado",
            unit="m²/m²",
            description="Sigla e unidade referenciadas em material legado. Numerador, denominador e escopo aguardam validação da engenharia.",
            status=IndicatorStatus.DRAFT,
        ),
        IndicatorDefinition(
            code="ACO_TOTAL_KG_M2",
            name="Aço total indicativo por área",
            unit="kg/m²",
            description="Indicador solicitado para o produto. Fórmula, escopo e critérios de agregação aguardam validação da engenharia.",
            status=IndicatorStatus.DRAFT,
        ),
        IndicatorDefinition(
            code="ACO_TOTAL_KG_M3",
            name="Aço total indicativo por volume",
            unit="kg/m³",
            description="Indicador solicitado para o produto. Fórmula, escopo e critérios de agregação aguardam validação da engenharia.",
            status=IndicatorStatus.DRAFT,
        ),
    )
