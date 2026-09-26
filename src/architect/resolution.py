"""Architecture model: the single resolved model every output is derived from."""

from pydantic import BaseModel, ConfigDict

from architect.feasibility import FeasibilityResult, ProviderConfiguration, assess
from architect.providers import ProviderBundle
from architect.requirements import Provenance, RequirementModel
from architect.rules import SEEDED_RULES, ComponentRequirement, ComponentStatus, evaluate


class Decision(BaseModel):
    """One consequential decision and what it is attributable to."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str
    outcome: str
    provenance: list[Provenance]
    references: list[str]
    explanation: str


class ArchitectureModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    components: list[ComponentRequirement]
    provider_candidates: list[ProviderConfiguration]
    feasibility: FeasibilityResult
    decisions: list[Decision] = []
    unresolved_items: list[str] = []
    avoided_items: list[str] = []
    scaling_triggers: list[str] = []


class ResolvedPlan(BaseModel):
    """The single object every output is rendered from: confirmed requirements + resolved architecture."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirements: RequirementModel
    architecture: ArchitectureModel
    clarification_rounds: int = 0
    clarification_stop: str | None = None


def _component_decision(c: ComponentRequirement, notes: list[str]) -> Decision:
    related = [n for n in notes if n.startswith(f"{c.component}:")]
    blocked = f"; blocked by {', '.join(c.blocking_unknowns)}" if c.blocking_unknowns else ""
    return Decision(
        subject=c.component,
        outcome=c.status,
        provenance=c.provenance,
        references=c.rules_triggered,
        explanation=f"{c.status} per {', '.join(c.rules_triggered)}{blocked}" + "".join(f"; {n}" for n in related),
    )


def _feasibility_decisions(f: FeasibilityResult, model: RequirementModel) -> list[Decision]:
    def about(prefix: str) -> str:
        lines = [e for e in f.explanations + f.conflicts if e.startswith(prefix)]
        return " | ".join(lines) or "no issues found"

    budget_prov = list(
        dict.fromkeys([model.constraints.monthly_budget.provenance, model.constraints.currency.provenance])
    )
    return [
        Decision(
            subject="feasibility.architecture",
            outcome=f.architecture,
            provenance=[Provenance.RULE],
            references=["architecture-rules.md G-7"],
            explanation="; ".join(f.conflicts) or "no rule conflicts",
        ),
        Decision(
            subject="feasibility.provider",
            outcome=f.provider,
            provenance=[Provenance.PROVIDER_FACT],
            references=["seeded provider facts"],
            explanation=about("provider:"),
        ),
        Decision(
            subject="feasibility.budget",
            outcome=f.budget,
            provenance=[*budget_prov, Provenance.PROVIDER_FACT],
            references=["constraints.monthly_budget", "constraints.currency", "seeded pricing facts"],
            explanation=about("budget:"),
        ),
        Decision(
            subject="feasibility.compatibility",
            outcome=f.compatibility,
            provenance=[Provenance.UNKNOWN],
            references=["decision-resolution.md: compatibility deferred in V1"],
            explanation="cross-provider compatibility is not verified in V1",
        ),
    ]


def _uncovered_capabilities(model: RequirementModel) -> list[str]:
    """Known-true capabilities that no V1 rule consumes (decision-resolution.md G-15)."""
    triggers = {r.trigger for r in SEEDED_RULES}
    return [
        f"capabilities.{name}=true: no V1 architecture rule; infrastructure for it is not determined by this tool"
        for name, rv in model.capabilities
        if rv.value is True and f"capabilities.{name}" not in triggers
    ]


def _unresolved(components: list[ComponentRequirement], f: FeasibilityResult, model: RequirementModel) -> list[str]:
    items = _uncovered_capabilities(model)
    for c in components:
        if c.status is ComponentStatus.UNDETERMINED:
            items.append(f"{c.component}: UNDETERMINED (blocked by {', '.join(c.blocking_unknowns) or 'a conflict'})")
        elif c.status is ComponentStatus.REQUIRED:
            items += [f"{c.component}.{attr}: UNKNOWN" for attr in c.blocking_unknowns]
    items += [
        f"{dim} feasibility: UNVERIFIED"
        for dim in ("architecture", "provider", "budget")
        if getattr(f, dim) == "UNVERIFIED"
    ]
    items.append("compatibility: DEFERRED (cross-provider integration is not verified in V1)")
    return items


def resolve(model: RequirementModel, bundles: list[ProviderBundle]) -> ResolvedPlan:
    """Rules -> components -> provider configurations -> feasibility -> one architecture model.

    Raises:
        UnconfirmedRequirementsError: `model` has not been confirmed in review.
    """
    rules = evaluate(model)
    feasibility, configs = assess(rules, model, bundles)
    architecture = ArchitectureModel(
        components=rules.components,
        provider_candidates=configs,
        feasibility=feasibility,
        decisions=[_component_decision(c, rules.notes) for c in rules.components]
        + _feasibility_decisions(feasibility, model),
        unresolved_items=_unresolved(rules.components, feasibility, model),
        avoided_items=rules.avoided,
        scaling_triggers=[],  # no documented scaling rule exists in V1
    )
    return ResolvedPlan(requirements=model, architecture=architecture)


def is_infeasible(model: RequirementModel, bundles: list[ProviderBundle]) -> bool:
    return resolve(model, bundles).architecture.feasibility.is_infeasible
