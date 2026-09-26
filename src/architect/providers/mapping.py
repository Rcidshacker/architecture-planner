"""Match abstract component specs to provider bundles (decision-resolution.md G-9)."""

import json
from enum import StrEnum
from importlib.resources import files

from pydantic import BaseModel, ConfigDict

from architect.providers.models import ProviderBundle, ProviderFact
from architect.rules import UNKNOWN, ComponentRequirement, SpecValue
from architect.rules.models import ENUM_DOMAINS, MIN_QUANTITY_LIMITS


class MatchState(StrEnum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNVERIFIED = "UNVERIFIED"


class Match(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle: str
    component: str
    state: MatchState
    evidence: list[str]
    """refs of the verified facts relied on"""
    missing_evidence: list[str]
    explanations: list[str]


def load_seed_bundles() -> list[ProviderBundle]:
    """Load the hand-seeded provider bundles shipped with the package."""
    raw = files("architect.providers").joinpath("seed_facts.json").read_text(encoding="utf-8")
    return [ProviderBundle.model_validate(item) for item in json.loads(raw)]


class _Check:
    """Accumulates per-attribute outcomes for one bundle/component pair."""

    def __init__(self, bundle: ProviderBundle) -> None:
        self.bundle = bundle
        self.states: list[MatchState] = []
        self.evidence: list[str] = []
        self.missing: list[str] = []
        self.explanations: list[str] = []

    def verified(self, key: str) -> ProviderFact | None:
        fact = self.bundle.fact(key)
        if fact is None:
            self.missing.append(f"{self.bundle.name}: no fact for {key}")
            return None
        if not fact.is_verified:
            self.missing.append(f"{self.bundle.name}: {key} is {fact.verification_status}, not current evidence")
            return None
        self.evidence.append(fact.ref)
        return fact

    def enum_value(self, component: str, attr: str, value: str) -> MatchState:
        fact = self.verified(f"{component}.{attr}.{value}")
        if fact is None:
            return MatchState.UNVERIFIED
        return MatchState.SATISFIED if fact.value is True else MatchState.VIOLATED

    def enum(self, component: str, attr: str, value: SpecValue) -> None:
        if value != UNKNOWN:
            state = self.enum_value(component, attr, str(value))
            self.explanations.append(f"{attr}={value}: {state}")
        else:
            domain = ENUM_DOMAINS[(component, attr)]
            each = [self.enum_value(component, attr, v) for v in domain]
            ok = all(s is MatchState.SATISFIED for s in each)
            state = MatchState.SATISFIED if ok else MatchState.UNVERIFIED
            self.explanations.append(f"{attr}=UNKNOWN: {state} (supports {'all' if ok else 'not all'} of {domain})")
        self.states.append(state)

    def minimum(self, attr: str, value: SpecValue, limit_key: str) -> None:
        fact = self.verified(limit_key)
        if fact is None:
            state = MatchState.UNVERIFIED
        elif fact.value == "unlimited":
            state = MatchState.SATISFIED
        elif value == UNKNOWN:
            state = MatchState.UNVERIFIED
        else:
            # the limit's type is enforced by ProviderFact; spec quantities come from float requirement fields
            state = MatchState.SATISFIED if float(value) <= float(str(fact.value)) else MatchState.VIOLATED
        limit = "no verified limit" if fact is None else f"limit {fact.value}"
        self.explanations.append(f"{attr}={value}: {state} ({limit})")
        self.states.append(state)

    def overall(self) -> MatchState:
        if MatchState.VIOLATED in self.states:
            return MatchState.VIOLATED
        if MatchState.UNVERIFIED in self.states:
            return MatchState.UNVERIFIED
        return MatchState.SATISFIED


def match(bundle: ProviderBundle, requirement: ComponentRequirement) -> Match | None:
    """Check `bundle` against `requirement`'s spec. None if the bundle does not verifiably offer the component."""
    component = requirement.component
    offered = bundle.fact(f"component.{component}")
    if offered is None or offered.value is not True:
        return None
    check = _Check(bundle)
    if offered.is_verified:
        check.evidence.append(offered.ref)
    else:  # the offer itself is unverified: a candidate, never proof (decision-resolution.md G-9)
        check.states.append(MatchState.UNVERIFIED)
        check.missing.append(f"{bundle.name}: {offered.key} is {offered.verification_status}, not current evidence")
    for attr, value in requirement.spec.items():
        if (component, attr) in ENUM_DOMAINS:
            check.enum(component, attr, value)
        elif (component, attr) in MIN_QUANTITY_LIMITS:
            check.minimum(attr, value, MIN_QUANTITY_LIMITS[(component, attr)])
        else:  # an attribute no provider fact convention covers cannot be verified
            check.states.append(MatchState.UNVERIFIED)
            check.missing.append(f"{bundle.name}: no fact convention for {component}.{attr}")
    return Match(
        bundle=bundle.name,
        component=component,
        state=check.overall(),
        evidence=check.evidence,
        missing_evidence=check.missing,
        explanations=check.explanations,
    )
