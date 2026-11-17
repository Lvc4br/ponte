from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NumericRange:
    minimum: float
    maximum: float

    def overlaps(self, other: "NumericRange") -> bool:
        return self.minimum <= other.maximum and other.minimum <= self.maximum


@dataclass
class SearchCriteria:
    width: NumericRange | None = None
    span: NumericRange | None = None
    total_length: NumericRange | None = None
    type_obra: str | None = None


@dataclass
class BridgeRecord:
    values: dict[str, Any]
    source_row: int

    def get(self, key: str, default=None):
        return self.values.get(key, default)
