"""Regression tests for the /code-review findings (one test per finding, CR1-CR10)."""

import json
import math
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from architect.cli import main, review
from architect.extraction import extract
from architect.feasibility import FeasibilityState, assess
from architect.output import architecture_brief
from architect.providers import MatchState, ProviderBundle, match
from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import parse_user_value, with_value
from architect.resolution import resolve
from architect.rules import ComponentRequirement, ComponentStatus, EngineResult

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def fact(
    provider: str, key: str, value: Any, fact_type: str = "capability", status: str = "VERIFIED"
) -> dict[str, Any]:
    return {
        "provider": provider,
        "service": "svc",
        "fact_type": fact_type,
        "key": key,
        "value": value,
        "source_url": "https://example.test",
        "retrieved_at": NOW,
        "verified_at": NOW,
        "verification_status": status,
    }


def bundle(provider: str, facts: list[dict[str, Any]], fixed: float = 0, currency: str = "USD") -> ProviderBundle:
    pricing = [
        fact(provider, k, v, "pricing")
        for k, v in (("currency", currency), ("fixed_monthly", fixed), ("usage_priced", False))
    ]
    return ProviderBundle.model_validate(
        {"provider": provider, "services": ["svc"], "included_capabilities": [], "evidence": facts + pricing}
    )


def user(value: Any) -> RequirementValue[Any]:
    return RequirementValue[Any](value=value, state=RequirementState.KNOWN, provenance=Provenance.USER)


def reqs(**fields: Any) -> RequirementModel:
    m = RequirementModel(application=Application(description="t"), confirmed=True)
    for k, v in fields.items():
        m = with_value(m, k.replace("__", "."), user(v))
    return m


def llm_returning(entries: dict[str, Any]) -> Any:
    return lambda _prompt: json.dumps(entries)


def engine_of(*components: ComponentRequirement) -> EngineResult:
    return EngineResult(components=list(components), conflicts=[], avoided=[], notes=[])


# CR1: numeric values must be finite and non-negative
@pytest.mark.parametrize("raw", ["NaN", "Infinity", "-5"])
def test_cr1_non_finite_or_negative_numbers_are_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_user_value("constraints.monthly_budget", raw, "t")
    with pytest.raises(ValidationError):
        RequirementValue[float](value=float(raw), state=RequirementState.KNOWN, provenance=Provenance.USER)
    assert not math.isnan(parse_user_value("constraints.monthly_budget", "0", "t").value)


# CR2: whitespace-only quote is no quote
def test_cr2_whitespace_source_text_is_refused() -> None:
    entry = {"value": True, "state": "KNOWN", "provenance": "USER", "source_text": "   "}
    result = extract("a todo app", llm_returning({"capabilities.file_uploads": entry}))
    assert not result.requirements.capabilities.file_uploads.is_known and len(result.issues) == 1


# CR3: a KNOWN number must appear in its own quote
def test_cr3_known_number_absent_from_its_quote_is_refused() -> None:
    entry = {"value": 100000, "state": "KNOWN", "provenance": "USER", "source_text": "todo"}
    result = extract("a todo app", llm_returning({"workload.users": entry}))
    assert not result.requirements.workload.users.is_known and "workload.users" in result.issues[0]


def test_cr3_number_with_thousands_separator_in_quote_is_kept() -> None:
    entry = {"value": 1500, "state": "KNOWN", "provenance": "USER", "source_text": "₹1,500 a month"}
    result = extract("budget is ₹1,500 a month", llm_returning({"constraints.monthly_budget": entry}))
    assert result.requirements.constraints.monthly_budget.value == 1500 and result.issues == []


# CR4: currency comparison is case-insensitive
def test_cr4_lowercase_currency_matches_provider_currency() -> None:
    store = bundle("Store", [fact("Store", "component.object_storage", True)], fixed=0)
    comp = ComponentRequirement(component="object_storage", status=ComponentStatus.REQUIRED)
    result, _ = assess(engine_of(comp), reqs(constraints__monthly_budget=10, constraints__currency="usd"), [store])
    assert result.budget is FeasibilityState.FEASIBLE


# CR5: stale component offer is an UNVERIFIED candidate, reported as missing evidence
def test_cr5_stale_component_fact_is_unverified_candidate_not_ignored() -> None:
    stale = bundle("Old", [fact("Old", "component.object_storage", True, status="STALE")])
    m = match(stale, ComponentRequirement(component="object_storage", status=ComponentStatus.REQUIRED))
    assert m is not None and m.state is MatchState.UNVERIFIED
    assert any("STALE" in item for item in m.missing_evidence)


# CR6: EOF during review saves edits unconfirmed instead of crashing
def test_cr6_eof_in_review_keeps_edits(monkeypatch: pytest.MonkeyPatch) -> None:
    lines: Iterator[str] = iter(["workload.users=5"])

    def fake_input(_prompt: str = "") -> str:
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)
    model = review(RequirementModel(application=Application(description="t")))
    assert model.workload.users.value == 5 and model.confirmed is False


# CR7: empty --description reaches the extractor's validation, not a TypeError
def test_cr7_empty_description_is_a_clean_error(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["extract", "--description", "", "--out", str(tmp_path / "r.json")]) == 1
    assert "required" in capsys.readouterr().err


# CR8: quotes in the application name are escaped in the Mermaid diagram
def test_cr8_mermaid_label_is_escaped() -> None:
    m = with_value(
        reqs(),
        "application.name",
        RequirementValue[str](
            value='My "Pro" App', state=RequirementState.KNOWN, provenance=Provenance.USER, source_text="x"
        ),
    )
    mermaid = architecture_brief(resolve(m, [])).split("```mermaid")[1].split("```")[0]
    assert '"Pro"' not in mermaid and "#quot;Pro#quot;" in mermaid


# CR9: cheapest-configuration message never treats an unknown (mixed-currency) cost as free
def test_cr9_infeasible_message_ignores_unpriceable_configurations() -> None:
    comps = [ComponentRequirement(component=c, status=ComponentStatus.REQUIRED) for c in ("a", "b")]
    usd = bundle("Usd", [fact("Usd", "component.a", True)], fixed=3)
    inr = bundle("Inr", [fact("Inr", "component.b", True)], fixed=50, currency="INR")
    both = bundle("Both", [fact("Both", "component.a", True), fact("Both", "component.b", True)], fixed=25)
    result, _ = assess(
        engine_of(*comps), reqs(constraints__monthly_budget=0, constraints__currency="USD"), [usd, inr, both]
    )
    assert result.budget is FeasibilityState.INFEASIBLE
    assert not any("None" in c for c in result.conflicts)


# CR10: de-duplication keeps the best-covered assignment of a bundle set
def test_cr10_same_bundle_set_keeps_fully_satisfied_assignment() -> None:
    def offer(p: str, storage_ok: bool) -> ProviderBundle:
        facts = [fact(p, "component.object_storage", True), fact(p, "component.relational_database", True)]
        return bundle(p, facts + ([fact(p, "object_storage.access_mode.private", True)] if storage_ok else []))

    storage = ComponentRequirement(
        component="object_storage", status=ComponentStatus.REQUIRED, spec={"access_mode": "private"}
    )
    db = ComponentRequirement(component="relational_database", status=ComponentStatus.REQUIRED)
    _, configs = assess(
        engine_of(storage, db),
        reqs(constraints__monthly_budget=10),
        [offer("A", storage_ok=False), offer("B", storage_ok=True)],
    )
    both = next(c for c in configs if set(c.bundles) == {"A svc", "B svc"})
    assert both.covers["object_storage"] == "B svc" and both.provider_state is FeasibilityState.FEASIBLE
