"""Single-capability rule engine (architecture-rules.md, including G-4..G-7)."""

from pydantic import BaseModel, ConfigDict

from architect.requirements import Provenance, RequirementModel
from architect.requirements.fields import get_value
from architect.rules.models import UNKNOWN, ComponentRequirement, ComponentStatus, RuleCategory, SpecValue


class UnconfirmedRequirementsError(Exception):
    """Rules were asked to consume requirements that human review has not confirmed."""


class Rule(BaseModel):
    """A single-capability rule. `trigger=None` means the condition always holds in V1 (G-6)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    category: RuleCategory
    component: str
    status: ComponentStatus
    trigger: str | None = None
    trigger_value: bool = True
    spec_sources: dict[str, str] = {}
    """spec attribute -> requirement field it is copied from (G-5)"""


SEEDED_RULES: tuple[Rule, ...] = (
    Rule(
        id="STORAGE-001",
        category=RuleCategory.HARD_REQUIREMENT,
        component="object_storage",
        status=ComponentStatus.REQUIRED,
        trigger="capabilities.file_uploads",
        spec_sources={
            "access_mode": "storage.access_mode",
            "delivery": "storage.delivery",
            "minimum_capacity": "storage.minimum_capacity_gb",
        },
    ),
    # V1 has no explicit cache signal, so `no_explicit_cache_requirement` always holds (G-6).
    Rule(
        id="CACHE-DEFAULT-001",
        category=RuleCategory.DEFAULT_AVOID,
        component="cache",
        status=ComponentStatus.NOT_REQUIRED,
    ),
)

_STRENGTH = {RuleCategory.HARD_REQUIREMENT: 3, RuleCategory.PREFERENCE: 2, RuleCategory.DEFAULT_AVOID: 1}


class _Output(BaseModel):
    rule: Rule
    requirement: ComponentRequirement


class EngineResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    components: list[ComponentRequirement]
    conflicts: list[str]
    avoided: list[str]
    """components left out by a DEFAULT_AVOID rule"""
    notes: list[str]
    """precedence explanations"""


def _dedupe(items: list[Provenance]) -> list[Provenance]:
    return list(dict.fromkeys(items))


def _apply(rule: Rule, model: RequirementModel) -> ComponentRequirement:
    provenance = [Provenance.RULE]
    status = rule.status
    blocking: list[str] = []
    if rule.trigger is not None:
        trigger = get_value(model, rule.trigger)
        provenance = [trigger.provenance, Provenance.RULE]
        if not trigger.is_known:
            status, blocking = ComponentStatus.UNDETERMINED, [rule.trigger]
        elif trigger.value != rule.trigger_value:
            status = ComponentStatus.NOT_REQUIRED

    spec: dict[str, SpecValue] = {}
    for attr, source in rule.spec_sources.items():
        rv = get_value(model, source)
        spec[attr] = UNKNOWN if rv.value is None else rv.value
        if status is not ComponentStatus.NOT_REQUIRED:
            provenance.append(rv.provenance)
            if status is ComponentStatus.REQUIRED and not rv.is_known:
                blocking.append(attr)
    return ComponentRequirement(
        component=rule.component,
        status=status,
        spec=spec,
        provenance=_dedupe(provenance),
        rules_triggered=[rule.id],
        blocking_unknowns=blocking,
    )


def _combine(component: str, outputs: list[_Output]) -> tuple[ComponentRequirement, str | None, str | None]:
    """Resolve one component's outputs: conflicts first (G-7 step 2), then precedence (step 3)."""
    all_ids = [o.rule.id for o in outputs]
    all_prov = _dedupe([p for o in outputs for p in o.requirement.provenance])
    hard_decided = [
        o
        for o in outputs
        if o.rule.category is RuleCategory.HARD_REQUIREMENT and o.requirement.status is not ComponentStatus.UNDETERMINED
    ]
    if len({o.requirement.status for o in hard_decided}) > 1:
        detail = ", ".join(f"{o.rule.id} -> {o.requirement.status}" for o in hard_decided)
        undetermined = ComponentRequirement(
            component=component,
            status=ComponentStatus.UNDETERMINED,
            spec=hard_decided[0].requirement.spec,
            provenance=all_prov,
            rules_triggered=all_ids,
            blocking_unknowns=[],
        )
        return undetermined, f"{component}: hard requirements disagree ({detail})", None

    strongest = max(_STRENGTH[o.rule.category] for o in outputs)
    # Among hard outputs, a decided status beats an UNDETERMINED one (the undetermined rule did not fire).
    winners = [o for o in outputs if _STRENGTH[o.rule.category] == strongest]
    decided = [o for o in winners if o.requirement.status is not ComponentStatus.UNDETERMINED] or winners
    chosen = decided[0].requirement
    losers = [o.rule.id for o in outputs if _STRENGTH[o.rule.category] < strongest]
    note = None
    if losers:
        note = (
            f"{component}: {', '.join(losers)} not applied; overridden by stronger rule(s) "
            f"{', '.join(o.rule.id for o in decided)}"
        )
    merged = chosen.model_copy(update={"provenance": all_prov, "rules_triggered": all_ids})
    return merged, None, note


def evaluate(model: RequirementModel, rules: tuple[Rule, ...] | list[Rule] = SEEDED_RULES) -> EngineResult:
    """Evaluate `rules` against confirmed requirements. Rule order never affects the result.

    Raises:
        UnconfirmedRequirementsError: `model.confirmed` is False.
    """
    if not model.confirmed:
        raise UnconfirmedRequirementsError("requirements must be reviewed and confirmed before rules run")

    by_component: dict[str, list[_Output]] = {}
    for rule in rules:
        by_component.setdefault(rule.component, []).append(_Output(rule=rule, requirement=_apply(rule, model)))

    components, conflicts, avoided, notes = [], [], [], []
    for name in sorted(by_component):
        outputs = sorted(by_component[name], key=lambda o: o.rule.id)
        requirement, conflict, note = _combine(name, outputs)
        components.append(requirement)
        conflicts += [conflict] if conflict else []
        notes += [note] if note else []
        avoid_won = all(o.rule.category is RuleCategory.DEFAULT_AVOID for o in outputs)
        if avoid_won and requirement.status is ComponentStatus.NOT_REQUIRED:
            avoided.append(name)
    return EngineResult(components=components, conflicts=conflicts, avoided=avoided, notes=notes)
