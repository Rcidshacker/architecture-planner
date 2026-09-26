"""Clarification ranking and bounded loop (decision-resolution.md G-12, requirements-schema.md G-2)."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from architect.clarification.models import ClarificationQuestion
from architect.requirements import RequirementModel, RequirementValue
from architect.requirements.fields import FIELD_PATHS, get_value, with_value

MAX_ROUNDS = 3
BLOCKING_IMPACT = 3


def _always(_: RequirementModel) -> bool:
    return True


def _uploads_possible(m: RequirementModel) -> bool:
    return m.capabilities.file_uploads.value is not False


def _budget_nonzero(m: RequirementModel) -> bool:
    return m.constraints.monthly_budget.value not in (None, 0)


def _persistence_possible(m: RequirementModel) -> bool:
    return m.capabilities.data_persistence.value is not False


@dataclass(frozen=True)
class FieldMeta:
    """Static decision metadata for one requirement field."""

    decision_impact: Literal[1, 2, 3, 4]
    blocks: tuple[str, ...]
    """V1-implemented decisions this field gates; empty means never asked in V1"""
    prompt: str = ""
    relevant_when: Callable[[RequirementModel], bool] = field(default=_always)


_ACTIVE: dict[str, FieldMeta] = {  # row order = tie-break order (requirements-schema.md G-2)
    "capabilities.file_uploads": FieldMeta(
        4, ("object_storage",), "Will users upload files (images, documents, media)? (true/false)"
    ),
    "storage.access_mode": FieldMeta(
        3,
        ("object_storage.spec.access_mode", "provider"),
        "Should uploaded files be private to their owners or publicly readable? (private/public)",
        _uploads_possible,
    ),
    "storage.minimum_capacity_gb": FieldMeta(
        3,
        ("object_storage.spec.minimum_capacity", "provider", "budget"),
        "Roughly how many GB of uploaded files do you need to store? (number)",
        _uploads_possible,
    ),
    "storage.delivery": FieldMeta(
        2,
        ("object_storage.spec.delivery", "provider"),
        "Should files be served via expiring signed links or direct public URLs? (signed_url/direct)",
        _uploads_possible,
    ),
    "constraints.monthly_budget": FieldMeta(
        3, ("budget",), "What is your monthly infrastructure budget? (number, 0 for free only)"
    ),
    "constraints.currency": FieldMeta(
        3, ("budget",), "Which currency is that budget in? (e.g. USD, INR)", _budget_nonzero
    ),
    "capabilities.data_persistence": FieldMeta(
        4,
        ("relational_database",),
        "Does your app need to persist structured data long-term (e.g. user accounts, posts, records)? (true/false)",
    ),
    "database.minimum_capacity_gb": FieldMeta(
        3,
        ("relational_database.spec.minimum_capacity", "provider", "budget"),
        "Roughly how many GB of database storage do you need? (number)",
        _persistence_possible,
    ),
}
_RECORDED_ONLY = {"operations.ai_request_duration": FieldMeta(4, ())}  # queue/worker rules not in V1

FIELD_METADATA: dict[str, FieldMeta] = {
    **_ACTIVE,
    **_RECORDED_ONLY,
    **{p: FieldMeta(1, ()) for p in FIELD_PATHS if p not in _ACTIVE and p not in _RECORDED_ONLY},
}


class StopReason(StrEnum):
    NO_BLOCKING_UNKNOWNS = "no_blocking_unknowns"
    MAX_ROUNDS = "max_rounds"
    INFEASIBLE = "infeasible"
    BLOCKING_UNKNOWNS_ALREADY_ASKED = "blocking_unknowns_already_asked"


class ClarificationOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    requirements: RequirementModel
    rounds: list[list[ClarificationQuestion]]
    stop_reason: StopReason


def _open_fields(model: RequirementModel, metadata: dict[str, FieldMeta]) -> list[str]:
    """Unresolved fields that still affect an implemented decision, in metadata order."""
    return [
        path
        for path, meta in metadata.items()
        if meta.blocks and not get_value(model, path).is_known and meta.relevant_when(model)
    ]


def candidate_questions(
    model: RequirementModel, asked: set[str], metadata: dict[str, FieldMeta] = FIELD_METADATA
) -> list[ClarificationQuestion]:
    """Rank open, not-yet-asked fields by `uncertainty x decision_impact` (highest first, stable)."""
    questions = [
        ClarificationQuestion(
            field=path,
            prompt=metadata[path].prompt or f"What is {path}?",
            decision_impact=metadata[path].decision_impact,
            uncertainty=1,
            priority=1 * metadata[path].decision_impact,
            blocking_decisions=list(metadata[path].blocks),
        )
        for path in _open_fields(model, metadata)
        if path not in asked
    ]
    return sorted(questions, key=lambda q: -q.priority)


def run_clarification(
    model: RequirementModel,
    ask: Callable[[ClarificationQuestion], RequirementValue[Any] | None],
    is_infeasible: Callable[[RequirementModel], bool],
    max_rounds: int = MAX_ROUNDS,
    metadata: dict[str, FieldMeta] = FIELD_METADATA,
) -> ClarificationOutcome:
    """Ask the top-priority questions each round until a documented stop condition holds.

    `ask` returns the user's answer as a USER value, or None for "don't know" (field stays UNKNOWN).
    `is_infeasible` re-runs decisions and feasibility on the current model.
    """
    asked: set[str] = set()
    rounds: list[list[ClarificationQuestion]] = []
    while True:
        if is_infeasible(model):
            reason = StopReason.INFEASIBLE
            break
        questions = candidate_questions(model, asked, metadata)
        if not any(q.decision_impact >= BLOCKING_IMPACT for q in questions):
            still_blocked = any(metadata[p].decision_impact >= BLOCKING_IMPACT for p in _open_fields(model, metadata))
            reason = StopReason.BLOCKING_UNKNOWNS_ALREADY_ASKED if still_blocked else StopReason.NO_BLOCKING_UNKNOWNS
            break
        if len(rounds) >= max_rounds:
            reason = StopReason.MAX_ROUNDS
            break
        top = [q for q in questions if q.priority == questions[0].priority]
        rounds.append(top)
        for question in top:
            asked.add(question.field)
            answer = ask(question)
            if answer is not None:
                model = with_value(model, question.field, answer)
    return ClarificationOutcome(requirements=model, rounds=rounds, stop_reason=reason)
