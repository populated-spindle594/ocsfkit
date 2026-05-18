from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ProvenanceKind = Literal["mapped", "transformed", "defaulted", "guessed"]


class FieldDecision(BaseModel):
    target: str
    source: str | None = None
    value: Any = None
    transform: str | None = None
    provenance: ProvenanceKind
    required: bool = False


class MappingExplanation(BaseModel):
    schema_version: str | None = None
    target_class: dict[str, Any] = Field(default_factory=dict)
    mapped_fields: list[FieldDecision] = Field(default_factory=list)
    defaulted_fields: list[FieldDecision] = Field(default_factory=list)
    guessed_fields: list[FieldDecision] = Field(default_factory=list)
    dropped_fields: list[str] = Field(default_factory=list)
    unmapped_source_fields: list[str] = Field(default_factory=list)
    missing_target_fields: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class MappingResult(BaseModel):
    event: dict[str, Any]
    explanation: MappingExplanation


class LintIssue(BaseModel):
    level: Literal["error", "warning"]
    path: str
    message: str


class DiffChange(BaseModel):
    path: str
    before: Any = None
    after: Any = None
    kind: Literal["added", "removed", "changed"]
