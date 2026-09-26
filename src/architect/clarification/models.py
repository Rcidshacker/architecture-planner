"""Clarification question contract (SCHEMA.md)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ClarificationQuestion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    prompt: str
    decision_impact: Literal[1, 2, 3, 4]
    uncertainty: Literal[0, 1]
    priority: int
    blocking_decisions: list[str] = []
