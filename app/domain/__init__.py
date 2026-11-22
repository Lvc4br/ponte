"""Engineering domain models for PONTE."""
from app.domain.bridges import Bridge, BridgeSpan, DomainIssue, IssueSeverity, MaterialQuantity, Project, validate_bridge
from app.domain.indicators import IndicatorDefinition, IndicatorResult, IndicatorStatus, IndicatorValueStatus
from app.domain.indicator_catalog import legacy_indicator_catalog

__all__ = [
    "Bridge", "BridgeSpan", "DomainIssue", "IssueSeverity", "MaterialQuantity",
    "Project", "validate_bridge", "IndicatorDefinition", "IndicatorResult",
    "IndicatorStatus", "IndicatorValueStatus", "legacy_indicator_catalog",
]
