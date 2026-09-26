"""Step 7 verify: highest-impact unresolved field is asked first; the loop stops per documented conditions."""

from typing import Any

from architect.clarification import (
    FIELD_METADATA,
    ClarificationQuestion,
    FieldMeta,
    StopReason,
    candidate_questions,
    run_clarification,
)
from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import FIELD_PATHS, with_value
from architect.rules import ComponentStatus, evaluate


def blank() -> RequirementModel:
    """Synthetic requirement set: everything unresolved, confirmed by review."""
    return RequirementModel(application=Application(description="a beginner's app idea"), confirmed=True)


def user(value: Any) -> RequirementValue[Any]:
    return RequirementValue[Any](value=value, state=RequirementState.KNOWN, provenance=Provenance.USER)


class ScriptedUser:
    """Answers by field path; anything unlisted is answered "don't know" (None)."""

    def __init__(self, answers: dict[str, Any]) -> None:
        self.answers = answers
        self.rounds_seen: list[str] = []

    def __call__(self, question: ClarificationQuestion) -> RequirementValue[Any] | None:
        self.rounds_seen.append(question.field)
        return user(self.answers[question.field]) if question.field in self.answers else None


def never_infeasible(_: RequirementModel) -> bool:
    return False


def test_every_schema_field_has_static_metadata() -> None:
    assert set(FIELD_METADATA) == set(FIELD_PATHS)
    for meta in FIELD_METADATA.values():
        assert meta.decision_impact in (1, 2, 3, 4)


def test_priority_is_uncertainty_times_static_impact_only() -> None:
    questions = candidate_questions(blank(), asked=set())
    assert questions  # something is unresolved
    for q in questions:
        assert q.uncertainty == 1
        assert q.priority == q.uncertainty * q.decision_impact == FIELD_METADATA[q.field].decision_impact
    assert set(ClarificationQuestion.model_fields) == {
        "field",
        "prompt",
        "decision_impact",
        "uncertainty",
        "priority",
        "blocking_decisions",
    }  # no hidden factor


def test_highest_impact_field_is_asked_first_and_alone() -> None:
    outcome = run_clarification(blank(), ScriptedUser({"capabilities.file_uploads": True}), never_infeasible)
    first_round = outcome.rounds[0]
    assert [q.field for q in first_round] == ["capabilities.file_uploads"]
    assert first_round[0].priority == 4


def test_fields_without_an_implemented_decision_are_never_asked() -> None:
    assert FIELD_METADATA["operations.ai_request_duration"].decision_impact == 4  # high impact...
    outcome = run_clarification(blank(), ScriptedUser({}), never_infeasible)
    asked = [q.field for r in outcome.rounds for q in r]
    assert "operations.ai_request_duration" not in asked  # ...but no V1 rule consumes it


def test_full_answer_session_resolves_blocking_unknowns_and_updates_model_as_user() -> None:
    answers = {
        "capabilities.file_uploads": True,
        "storage.access_mode": "private",
        "storage.minimum_capacity_gb": 20,
        "constraints.monthly_budget": 500,
        "constraints.currency": "INR",
    }
    outcome = run_clarification(blank(), ScriptedUser(answers), never_infeasible)

    assert [[q.field for q in r] for r in outcome.rounds] == [
        ["capabilities.file_uploads"],
        ["storage.access_mode", "storage.minimum_capacity_gb", "constraints.monthly_budget"],  # ties, row order
        ["constraints.currency"],  # only relevant once a non-zero budget is known
    ]
    assert outcome.stop_reason is StopReason.NO_BLOCKING_UNKNOWNS
    access = outcome.requirements.storage.access_mode
    assert (access.value, access.state, access.provenance) == ("private", RequirementState.KNOWN, Provenance.USER)


def test_non_blocking_unknowns_do_not_trigger_rounds_or_prevent_output() -> None:
    answers = {
        "capabilities.file_uploads": True,
        "storage.access_mode": "private",
        "storage.minimum_capacity_gb": 20,
        "constraints.monthly_budget": 0,
    }
    outcome = run_clarification(blank(), ScriptedUser(answers), never_infeasible)
    assert outcome.stop_reason is StopReason.NO_BLOCKING_UNKNOWNS
    assert "storage.delivery" not in [q.field for r in outcome.rounds for q in r]  # impact 2, never asked alone
    storage = next(c for c in evaluate(outcome.requirements).components if c.component == "object_storage")
    assert storage.status is ComponentStatus.REQUIRED and storage.blocking_unknowns == ["delivery"]


def test_irrelevant_fields_are_filtered_out() -> None:
    outcome = run_clarification(blank(), ScriptedUser({"capabilities.file_uploads": False}), never_infeasible)
    asked = [q.field for r in outcome.rounds for q in r]
    assert not any(f.startswith("storage.") for f in asked)


def test_dont_know_answers_are_not_reasked_and_blocking_output_stays_undetermined() -> None:
    outcome = run_clarification(blank(), ScriptedUser({}), never_infeasible)

    asked = [q.field for r in outcome.rounds for q in r]
    assert len(asked) == len(set(asked))
    assert outcome.stop_reason is StopReason.BLOCKING_UNKNOWNS_ALREADY_ASKED
    storage = next(c for c in evaluate(outcome.requirements).components if c.component == "object_storage")
    assert storage.status is ComponentStatus.UNDETERMINED


def test_maximum_of_three_rounds_is_enforced() -> None:
    # Synthetic metadata: a chain where each answer makes the next blocking field relevant.
    chain = ["capabilities.realtime", "capabilities.payments", "capabilities.search", "capabilities.notifications"]
    metadata = {path: FieldMeta(decision_impact=1, blocks=()) for path in FIELD_PATHS}
    for i, path in enumerate(chain):
        previous = chain[i - 1] if i else None
        metadata[path] = FieldMeta(
            decision_impact=4 - min(i, 1),
            blocks=("synthetic",),
            prompt=path,
            relevant_when=(lambda m, p=previous: p is None or getattr(m.capabilities, p.split(".")[1]).is_known),
        )

    asker = ScriptedUser(dict.fromkeys(chain, True))
    outcome = run_clarification(blank(), asker, never_infeasible, metadata=metadata)

    assert len(outcome.rounds) == 3
    assert outcome.stop_reason is StopReason.MAX_ROUNDS
    assert not outcome.requirements.capabilities.notifications.is_known  # left unresolved, not guessed


def test_infeasible_state_stops_the_loop() -> None:
    outcome = run_clarification(blank(), ScriptedUser({}), lambda _m: True)
    assert outcome.rounds == [] and outcome.stop_reason is StopReason.INFEASIBLE


def test_loop_only_asks_about_unresolved_fields() -> None:
    known = with_value(blank(), "capabilities.file_uploads", user(True))
    outcome = run_clarification(known, ScriptedUser({}), never_infeasible)
    assert "capabilities.file_uploads" not in [q.field for r in outcome.rounds for q in r]
