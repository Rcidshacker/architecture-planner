"""Step 8 verify: brief, diagram data, and agent prompt all trace to one resolved model; nothing extra invented."""

import json
from typing import Any

import pytest

from architect.output import agent_prompt, architecture_brief, diagram_data
from architect.providers import load_seed_bundles
from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import FIELD_PATHS, get_value, with_value
from architect.resolution import ResolvedPlan, resolve
from architect.rules import ComponentStatus

# Infrastructure vocabulary an output could plausibly hallucinate. Any term appearing in an output must be
# present in the resolved model itself.
VOCABULARY = [
    "redis",
    "queue",
    "kafka",
    "kubernetes",
    "cdn",
    "worker",
    "load balancer",
    "microservice",
    "cache",
    "relational_database",
    "authentication",
    "search",
    "websocket",
    "cloudflare",
    "supabase",
    "postgres",
    "lambda",
    "s3",
]


def requirements(**fields: Any) -> RequirementModel:
    m = RequirementModel(
        application=Application(description="Students upload PDFs and get AI summaries."), confirmed=True
    )
    m = with_value(
        m,
        "application.name",
        RequirementValue[str](
            value="PaperPal", state=RequirementState.KNOWN, provenance=Provenance.USER, source_text="PaperPal"
        ),
    )
    for key, value in fields.items():
        m = with_value(
            m,
            key.replace("__", "."),
            RequirementValue[Any](value=value, state=RequirementState.KNOWN, provenance=Provenance.USER),
        )
    return m


def outputs(plan: ResolvedPlan) -> dict[str, str]:
    return {"brief": architecture_brief(plan), "diagram": json.dumps(diagram_data(plan)), "prompt": agent_prompt(plan)}


@pytest.fixture
def plan() -> ResolvedPlan:
    return resolve(
        requirements(
            capabilities__file_uploads=True,
            capabilities__data_persistence=False,
            storage__access_mode="private",
        ),
        load_seed_bundles(),
    )


def test_diagram_nodes_are_exactly_the_models_non_excluded_components(plan: ResolvedPlan) -> None:
    data = diagram_data(plan)
    components = {n["id"] for n in data["nodes"] if n["kind"] == "component"}
    expected = {c.component for c in plan.architecture.components if c.status is not ComponentStatus.NOT_REQUIRED}
    assert components == expected == {"object_storage"}
    assert {(e["from"], e["to"]) for e in data["edges"]} == {("application", "object_storage")}


def test_every_component_and_state_appears_in_brief_and_prompt(plan: ResolvedPlan) -> None:
    brief, prompt = architecture_brief(plan), agent_prompt(plan)
    for comp in plan.architecture.components:
        assert comp.component in brief and comp.status in brief
    assert "object_storage" in prompt and "REQUIRED" in prompt
    for dimension in ("architecture", "provider", "budget", "compatibility"):
        assert dimension in brief.lower()
    assert "DEFERRED" in brief and "DEFERRED" in prompt


def test_outputs_invent_no_infrastructure_absent_from_the_model(plan: ResolvedPlan) -> None:
    # The architecture model plus only the *known* requirement values (field names alone must not count).
    known = {p: get_value(plan.requirements, p).value for p in FIELD_PATHS if get_value(plan.requirements, p).is_known}
    model_text = (plan.architecture.model_dump_json() + json.dumps(known)).lower()
    for name, text in outputs(plan).items():
        for term in VOCABULARY:
            if term in text.lower():
                assert term in model_text, f"{name} mentions {term!r}, which the resolved model does not contain"


def test_provider_names_in_outputs_come_only_from_candidates(plan: ResolvedPlan) -> None:
    candidate_bundles = {b for c in plan.architecture.provider_candidates for b in c.bundles}
    for bundle in load_seed_bundles():
        for text in outputs(plan).values():
            if bundle.name in text:
                assert bundle.name in candidate_bundles


def test_all_three_outputs_change_together_when_the_model_changes() -> None:
    without_uploads = resolve(requirements(capabilities__file_uploads=False), load_seed_bundles())
    for name, text in outputs(without_uploads).items():
        if name == "brief":
            assert "object_storage" in text and "NOT_REQUIRED" in text  # stated as not required, not as built
        else:
            assert "object_storage" not in text, name
    assert "Cloudflare" not in "".join(outputs(without_uploads).values())


def test_outputs_are_deterministic(plan: ResolvedPlan) -> None:
    again = resolve(plan.requirements, load_seed_bundles())
    assert outputs(again) == outputs(plan)


def test_undetermined_items_are_surfaced_in_every_output() -> None:
    undetermined = resolve(requirements(), load_seed_bundles())  # file_uploads unknown
    brief, prompt = architecture_brief(undetermined), agent_prompt(undetermined)
    assert "UNDETERMINED" in brief and "capabilities.file_uploads" in brief
    assert "UNDETERMINED" in prompt and "ask the user" in prompt.lower()
    node = next(n for n in diagram_data(undetermined)["nodes"] if n["id"] == "object_storage")
    assert node["status"] == "UNDETERMINED"


def test_infeasible_plan_tells_the_agent_not_to_build() -> None:
    reqs = requirements(
        capabilities__file_uploads=True,
        storage__minimum_capacity_gb=50,
        constraints__monthly_budget=0,
        constraints__currency="USD",
    )
    bundles = [b for b in load_seed_bundles() if b.name == "Supabase Pro"]  # only a paid option
    infeasible = resolve(reqs, bundles)
    assert infeasible.architecture.feasibility.budget == "INFEASIBLE"
    prompt, brief = agent_prompt(infeasible), architecture_brief(infeasible)
    assert "do not start implementation" in prompt.lower()
    assert "INFEASIBLE" in brief and "budget" in brief.lower()


def test_every_decision_has_provenance_and_a_reference(plan: ResolvedPlan) -> None:
    assert plan.architecture.decisions
    for decision in plan.architecture.decisions:
        assert decision.provenance and decision.references


def test_known_capability_without_a_v1_rule_is_surfaced_not_dropped() -> None:
    """Walkthrough 0 regression (decision-resolution.md G-15)."""
    plan = resolve(
        requirements(
            capabilities__file_uploads=True,
            capabilities__authentication=True,
            capabilities__ai_inference=True,
            capabilities__data_persistence=False,
        ),
        load_seed_bundles(),
    )
    for cap in ("authentication", "ai_inference"):
        assert any(
            u.startswith(f"capabilities.{cap}=true: no V1 architecture rule")
            for u in plan.architecture.unresolved_items
        )
        assert f"capabilities.{cap}" in agent_prompt(plan)
        assert f"capabilities.{cap}" in architecture_brief(plan)
    assert {n["id"] for n in diagram_data(plan)["nodes"]} == {"application", "object_storage"}  # no invented node
    assert "add no other infrastructure" not in agent_prompt(plan).lower()


def test_budget_decision_provenance_includes_inferred_currency() -> None:
    """Walkthrough 0 regression (decision-resolution.md G-16)."""
    reqs = with_value(
        requirements(capabilities__file_uploads=True, constraints__monthly_budget=10),
        "constraints.currency",
        RequirementValue[str](
            value="USD", state=RequirementState.INFERRED, provenance=Provenance.INFERENCE, source_text="$10"
        ),
    )
    budget = next(
        d for d in resolve(reqs, load_seed_bundles()).architecture.decisions if d.subject == "feasibility.budget"
    )
    assert Provenance.INFERENCE in budget.provenance
