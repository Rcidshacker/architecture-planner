"""Feasibility: architecture, provider, budget; compatibility DEFERRED (decision-resolution.md G-8..G-10)."""

from itertools import product
from typing import Final

from architect.feasibility.models import Dimension, FeasibilityResult, FeasibilityState, ProviderConfiguration
from architect.providers import Match, MatchState, ProviderBundle, match
from architect.requirements import RequirementModel
from architect.rules import ComponentRequirement, ComponentStatus, EngineResult

FEASIBLE: Final = FeasibilityState.FEASIBLE
INFEASIBLE: Final = FeasibilityState.INFEASIBLE
UNVERIFIED: Final = FeasibilityState.UNVERIFIED
_PRICING_KEYS = ("currency", "fixed_monthly", "usage_priced")


def _worst(states: list[Dimension]) -> Dimension:
    return INFEASIBLE if INFEASIBLE in states else UNVERIFIED if UNVERIFIED in states else FEASIBLE


def _component_state(req: ComponentRequirement, matches: list[Match]) -> tuple[Dimension, str]:
    name = req.component
    if any(m.state is MatchState.SATISFIED for m in matches):
        ok = ", ".join(m.bundle for m in matches if m.state is MatchState.SATISFIED)
        return FEASIBLE, f"{name}: satisfied by verified facts of {ok}"
    if matches and all(m.state is MatchState.VIOLATED for m in matches):
        return INFEASIBLE, f"{name}: every offering among seeded providers is verified not to meet the spec {req.spec}"
    if not matches:
        return UNVERIFIED, f"{name}: no seeded provider offers this component (missing evidence, not impossibility)"
    return UNVERIFIED, f"{name}: seeded offerings lack the verified facts needed to confirm the spec {req.spec}"


def _configurations(
    required: list[ComponentRequirement], matches: dict[str, list[Match]], bundles: dict[str, ProviderBundle]
) -> list[tuple[list[str], dict[str, Match]]]:
    """Every distinct bundle set covering all REQUIRED components with non-violated matches (G-10)."""
    options = [[m for m in matches[r.component] if m.state is not MatchState.VIOLATED] for r in required]
    best: dict[frozenset[str], tuple[Match, ...]] = {}  # insertion order = first enumeration, deterministic
    for choice in product(*options):
        names = frozenset(m.bundle for m in choice)
        satisfied = sum(m.state is MatchState.SATISFIED for m in choice)
        if names not in best or satisfied > sum(m.state is MatchState.SATISFIED for m in best[names]):
            best[names] = choice
    return [
        ([b for b in bundles if b in names], {m.component: m for m in choice})  # seed order
        for names, choice in best.items()
    ]


def _budget(
    names: list[str], bundles: dict[str, ProviderBundle], model: RequirementModel
) -> tuple[Dimension, float | None, str | None, str]:
    """Budget state of one configuration: (state, fixed_monthly, currency, explanation)."""
    budget, currency = model.constraints.monthly_budget, model.constraints.currency
    costs = []
    for name in names:
        facts = [bundles[name].fact(k) for k in _PRICING_KEYS]
        if any(f is None or not f.is_verified for f in facts):
            return UNVERIFIED, None, None, f"{name} has no verified pricing facts"
        cur, fixed, usage = (f.value for f in facts if f is not None)
        costs.append((str(cur), float(str(fixed)), usage is True))  # types enforced by ProviderFact

    currencies = {c.upper() for c, _, _ in costs}
    total = sum(fixed for _, fixed, _ in costs)
    shown_cur = next(iter(currencies)) if len(currencies) == 1 else None
    shown_total = total if shown_cur else None
    if budget.value is None:
        return UNVERIFIED, shown_total, shown_cur, "monthly budget is unknown"
    if budget.value == 0:
        if any(fixed > 0 for _, fixed, _ in costs):
            return (
                INFEASIBLE,
                shown_total,
                shown_cur,
                f"fixed monthly cost {shown_total} {shown_cur} exceeds a budget of 0",
            )
    elif currency.value is None or currencies != {currency.value.upper()}:
        return (
            UNVERIFIED,
            shown_total,
            shown_cur,
            (
                f"pricing is in {sorted(currencies)} but the budget currency is {currency.value or 'unknown'}; "
                "no verified exchange-rate fact"
            ),
        )
    elif total > budget.value:
        return (
            INFEASIBLE,
            total,
            shown_cur,
            f"fixed monthly cost {total} {shown_cur} exceeds the budget of {budget.value}",
        )
    if any(usage for _, _, usage in costs):
        return (
            UNVERIFIED,
            shown_total,
            shown_cur,
            "fixed cost fits, but usage-priced charges cannot be estimated (usage unknown)",
        )
    return FEASIBLE, shown_total, shown_cur, "fixed cost fits the budget and nothing is usage-priced"


def assess(
    rules: EngineResult, model: RequirementModel, bundles: list[ProviderBundle]
) -> tuple[FeasibilityResult, list[ProviderConfiguration]]:
    """Evaluate every feasibility dimension. Never changes component states."""
    explanations: list[str] = []
    conflicts = list(rules.conflicts)
    missing: list[str] = []
    architecture: Dimension = INFEASIBLE if rules.conflicts else FEASIBLE

    required = [c for c in rules.components if c.status is ComponentStatus.REQUIRED]
    if not required:
        undetermined = [c.component for c in rules.components if c.status is ComponentStatus.UNDETERMINED]
        state: Dimension = UNVERIFIED if undetermined else FEASIBLE
        note = (
            f"cannot evaluate while {', '.join(undetermined)} UNDETERMINED (G-17)"
            if undetermined
            else "no REQUIRED provider-backed components"
        )
        return FeasibilityResult(
            architecture=architecture,
            provider=state,
            budget=state,
            explanations=[f"provider: {note}", f"budget: {note}"],
            conflicts=conflicts,
        ), []

    by_name = {b.name: b for b in bundles}
    matches: dict[str, list[Match]] = {}
    states: list[Dimension] = []
    for req in required:
        found = [m for b in bundles if (m := match(b, req)) is not None]
        matches[req.component] = found
        missing += [item for m in found for item in m.missing_evidence]
        explanations += [
            f"provider: {m.bundle} excluded for {req.component}: "
            + "; ".join(e for e in m.explanations if MatchState.VIOLATED in e)
            for m in found
            if m.state is MatchState.VIOLATED
        ]
        state, why = _component_state(req, found)
        states.append(state)
        (conflicts if state is INFEASIBLE else explanations).append(f"provider: {why}")
    provider = _worst(states)

    configs: list[ProviderConfiguration] = []
    for names, covers in _configurations(required, matches, by_name):
        provider_state = _worst([FEASIBLE if m.state is MatchState.SATISFIED else UNVERIFIED for m in covers.values()])
        budget_state, fixed, cur, why = _budget(names, by_name, model)
        if provider_state is UNVERIFIED and budget_state is FEASIBLE:
            budget_state, why = UNVERIFIED, why + "; but a component match is unverified"
        configs.append(
            ProviderConfiguration(
                bundles=names,
                covers={c: m.bundle for c, m in covers.items()},
                provider_state=provider_state,
                budget_state=budget_state,
                fixed_monthly=fixed,
                currency=cur,
                explanations=[why],
            )
        )

    if provider is INFEASIBLE or not configs:
        budget: Dimension = UNVERIFIED
        explanations.append("budget: no valid provider configuration to price")
    elif any(c.budget_state is FEASIBLE for c in configs):
        budget = FEASIBLE
        explanations.append("budget: at least one configuration fits the budget with verified pricing")
    elif all(c.budget_state is INFEASIBLE for c in configs):
        budget = INFEASIBLE
        priced = [c for c in configs if c.fixed_monthly is not None]
        cheapest_text = ""
        if priced:
            cheapest = min(priced, key=lambda c: c.fixed_monthly or 0)
            cheapest_text = (
                f" (cheapest priced: {' + '.join(cheapest.bundles)} at "
                f"{cheapest.fixed_monthly} {cheapest.currency}/month)"
            )
        conflicts.append(
            f"budget: monthly budget {model.constraints.monthly_budget.value} {model.constraints.currency.value} "
            f"is below the fixed cost of every configuration{cheapest_text}; "
            "raise the budget or drop a hard requirement"
        )
    else:
        budget = UNVERIFIED
        explanations.append("budget: no configuration can be verified within budget")

    return FeasibilityResult(
        architecture=architecture,
        provider=provider,
        budget=budget,
        explanations=explanations,
        conflicts=conflicts,
        missing_evidence=list(dict.fromkeys(missing)),
    ), configs
