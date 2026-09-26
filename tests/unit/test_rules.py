"""Step 4 verify: TESTING.md rule-engine cases for STORAGE-001 and CACHE-DEFAULT-001."""

from typing import Any

import pytest

from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import with_value
from architect.rules import (
    SEEDED_RULES,
    UNKNOWN,
    ComponentStatus,
    Rule,
    RuleCategory,
    UnconfirmedRequirementsError,
    evaluate,
)


def model(**fields: Any) -> RequirementModel:
    """A confirmed model; each kwarg is `section__name=value` stated by the user (or a RequirementValue)."""
    m = RequirementModel(application=Application(description="test app"), confirmed=True)
    for key, value in fields.items():
        rv = (
            value
            if isinstance(value, RequirementValue)
            else RequirementValue[Any](value=value, state=RequirementState.KNOWN, provenance=Provenance.USER)
        )
        m = with_value(m, key.replace("__", "."), rv)
    return m


def component(result: Any, name: str) -> Any:
    return next(c for c in result.components if c.component == name)


def test_file_uploads_true_requires_object_storage_with_full_unknown_spec() -> None:
    storage = component(evaluate(model(capabilities__file_uploads=True)), "object_storage")

    assert storage.status is ComponentStatus.REQUIRED
    assert storage.spec == {"access_mode": UNKNOWN, "delivery": UNKNOWN, "minimum_capacity": UNKNOWN}
    assert storage.blocking_unknowns == ["access_mode", "delivery", "minimum_capacity"]
    assert storage.rules_triggered == ["STORAGE-001"]
    assert Provenance.USER in storage.provenance and Provenance.RULE in storage.provenance


def test_no_numeric_threshold_is_invented_from_a_boolean() -> None:
    result = evaluate(model(capabilities__file_uploads=True))
    for comp in result.components:
        for attr, value in comp.spec.items():
            assert not (isinstance(value, int | float) and not isinstance(value, bool)), (comp.component, attr)


def test_user_stated_storage_values_flow_into_the_spec_with_user_provenance() -> None:
    requirements = model(
        capabilities__file_uploads=True, storage__access_mode="private", storage__minimum_capacity_gb=50
    )
    storage = component(evaluate(requirements), "object_storage")
    assert storage.spec == {"access_mode": "private", "delivery": UNKNOWN, "minimum_capacity": 50}
    assert storage.blocking_unknowns == ["delivery"]


def test_file_uploads_false_means_object_storage_not_required() -> None:
    storage = component(evaluate(model(capabilities__file_uploads=False)), "object_storage")
    assert storage.status is ComponentStatus.NOT_REQUIRED
    assert storage.provenance == [Provenance.USER, Provenance.RULE]


def test_unknown_file_uploads_leaves_object_storage_undetermined() -> None:
    storage = component(evaluate(model()), "object_storage")
    assert storage.status is ComponentStatus.UNDETERMINED
    assert storage.blocking_unknowns == ["capabilities.file_uploads"]
    assert Provenance.UNKNOWN in storage.provenance


def test_inferred_trigger_keeps_inference_provenance() -> None:
    inferred = RequirementValue[bool](
        value=True, state=RequirementState.INFERRED, provenance=Provenance.INFERENCE, source_text="x"
    )
    storage = component(evaluate(model(capabilities__file_uploads=inferred)), "object_storage")
    assert storage.status is ComponentStatus.REQUIRED
    assert Provenance.INFERENCE in storage.provenance and Provenance.USER not in storage.provenance


def test_cache_default_avoid_yields_not_required_and_is_listed_as_avoided() -> None:
    result = evaluate(model(capabilities__file_uploads=True))
    cache = component(result, "cache")
    assert cache.status is ComponentStatus.NOT_REQUIRED
    assert cache.rules_triggered == ["CACHE-DEFAULT-001"]
    assert result.avoided == ["cache"]
    assert result.conflicts == []


HARD_CACHE = Rule(
    id="TEST-HARD-CACHE",
    category=RuleCategory.HARD_REQUIREMENT,
    component="cache",
    status=ComponentStatus.REQUIRED,
    trigger="capabilities.realtime",
)


@pytest.mark.parametrize("rules", [[*SEEDED_RULES, HARD_CACHE], [HARD_CACHE, *reversed(SEEDED_RULES)]])
def test_default_avoid_never_overrides_a_hard_requirement_regardless_of_order(rules: list[Rule]) -> None:
    result = evaluate(model(capabilities__realtime=True), rules)
    cache = component(result, "cache")
    assert cache.status is ComponentStatus.REQUIRED
    assert sorted(cache.rules_triggered) == ["CACHE-DEFAULT-001", "TEST-HARD-CACHE"]
    assert result.avoided == []
    assert any("CACHE-DEFAULT-001" in note for note in result.notes)


def test_conflicting_hard_rules_are_a_conflict_not_resolved_by_precedence() -> None:
    forbid = Rule(
        id="TEST-HARD-NO-STORAGE",
        category=RuleCategory.HARD_REQUIREMENT,
        component="object_storage",
        status=ComponentStatus.NOT_REQUIRED,
        trigger="capabilities.file_uploads",
    )
    result = evaluate(model(capabilities__file_uploads=True), [*SEEDED_RULES, forbid])
    storage = component(result, "object_storage")
    assert storage.status is ComponentStatus.UNDETERMINED
    assert len(result.conflicts) == 1 and "STORAGE-001" in result.conflicts[0]
    assert "TEST-HARD-NO-STORAGE" in result.conflicts[0]


def test_rules_refuse_an_unconfirmed_extraction_result() -> None:
    unconfirmed = model(capabilities__file_uploads=True).model_copy(update={"confirmed": False})
    with pytest.raises(UnconfirmedRequirementsError):
        evaluate(unconfirmed)


def test_seeded_rules_match_architecture_rules_md() -> None:
    by_id = {r.id: r for r in SEEDED_RULES}
    assert set(by_id) == {"STORAGE-001", "CACHE-DEFAULT-001", "DATABASE-001"}
    assert by_id["STORAGE-001"].category is RuleCategory.HARD_REQUIREMENT
    assert by_id["CACHE-DEFAULT-001"].category is RuleCategory.DEFAULT_AVOID
    assert by_id["DATABASE-001"].category is RuleCategory.HARD_REQUIREMENT


# --- DATABASE-001 (V1.1, spec gap G-18; walkthrough evidence: WALKTHROUGH.md e2/e3/e4) -----------------------------


def test_persistent_data_true_requires_relational_database_with_unknown_spec() -> None:
    db = component(evaluate(model(capabilities__data_persistence=True)), "relational_database")
    assert db.status is ComponentStatus.REQUIRED
    assert db.spec == {"minimum_capacity": UNKNOWN}
    assert db.blocking_unknowns == ["minimum_capacity"]
    assert db.rules_triggered == ["DATABASE-001"]
    assert Provenance.USER in db.provenance and Provenance.RULE in db.provenance


def test_user_stated_database_capacity_flows_into_the_spec_with_user_provenance() -> None:
    db = component(
        evaluate(model(capabilities__data_persistence=True, database__minimum_capacity_gb=0.02)), "relational_database"
    )
    assert db.spec == {"minimum_capacity": 0.02}
    assert db.blocking_unknowns == []


def test_persistent_data_false_means_relational_database_not_required() -> None:
    db = component(evaluate(model(capabilities__data_persistence=False)), "relational_database")
    assert db.status is ComponentStatus.NOT_REQUIRED
    assert db.provenance == [Provenance.USER, Provenance.RULE]


def test_unknown_persistent_data_leaves_relational_database_undetermined() -> None:
    db = component(evaluate(model()), "relational_database")
    assert db.status is ComponentStatus.UNDETERMINED
    assert db.blocking_unknowns == ["capabilities.data_persistence"]
    assert Provenance.UNKNOWN in db.provenance


def test_database_rule_does_not_invent_an_engine_type_attribute() -> None:
    """DATABASE-001 mirrors STORAGE-001 minimally: no access_mode/delivery-equivalent attribute exists for it."""
    db = component(evaluate(model(capabilities__data_persistence=True)), "relational_database")
    assert set(db.spec) == {"minimum_capacity"}
