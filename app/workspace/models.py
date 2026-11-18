"""Typed domain objects for the generic PONTE workspace."""

from dataclasses import dataclass, field
from typing import Any


SUPPORTED_COLUMN_TYPES = {
    "text", "integer", "decimal", "boolean", "date", "datetime", "json"
}


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataTable:
    id: int
    project_id: int
    name: str
    description: str = ""


@dataclass(frozen=True)
class Column:
    id: int
    table_id: int
    name: str
    data_type: str
    required: bool = False
    default_value: Any = None
    position: int = 0


@dataclass(frozen=True)
class DataRecord:
    id: int
    table_id: int
    values: dict[str, Any]
    created_at: str
    updated_at: str
