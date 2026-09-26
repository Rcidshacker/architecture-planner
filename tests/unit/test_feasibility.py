"""Step 6 verify: the six TESTING.md feasibility cases plus conflict-resolution cases."""

from datetime import UTC, datetime
from typing import Any

import pytest

from architect.feasibility import FeasibilityState, assess
from architect.providers import ProviderBundle, load_seed_bundles
from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import with_value
from architect.rules import UNKNOWN, ComponentRequirement, ComponentStatus, EngineResult, evaluate

FEASIBLE, INFEASIBLE, UNVERIFIED, DEFERRED = (
    FeasibilityState.FEASIBLE,
    FeasibilityState.INFEASIBLE,
    FeasibilityState.UNVERIFIED,
    FeasibilityState.DEFERRED,
)
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
        "source_url": f"https://example.test/{provider}",
        "retrieved_at": NOW,
        "verified_at": NOW,
        "verification_status": status,
    }


def bundle(
    provider: str,
    components: list[str],
    fixed: float,
    usage_priced: bool = False,
    currency: str = "USD",
    extra: list[dict[str, Any]] | None = None,
    pricing_status: str = "VERIFIED",
) -> ProviderBundle:
    evidence = [fact(provider, f"component.{c}", True) for c in components]
    evidence += [
        fact(provider, k, v, "pricing", pricing_status)
        for k, v in (("currency", currency), ("fixed_monthly", fixed), ("usage_priced", usage_priced))
    ]
    return ProviderBundle.model_validate(
        {
            "provider": provider,
            "services": ["svc"],
            "included_capabilities": components,
            "cost_model": {"currency": currency, "fixed_monthly": fixed, "usage_priced": usage_priced},
            "evidence": evidence + (extra or []),
        }
    )


def full_storage_facts(provider: str, public: bool = True) -> list[dict[str, Any]]:
    return [
        fact(provider, "object_storage.access_mode.private", True),
        fact(provider, "object_storage.access_mode.public", public),
        fact(provider, "object_storage.delivery.signed_url", True),
        fact(provider, "object_storage.delivery.direct", True),
        fact(provider, "object_storage.max_capacity_gb", "unlimited", "limitation"),
    ]


def requirements(budget: float | None = None, currency: str | None = "USD") -> RequirementModel:
    m = RequirementModel(application=Application(description="t"), confirmed=True)
    for path, value in (("constraints.monthly_budget", budget), ("constraints.currency", currency)):
        if value is not None:
            m = with_value(
                m, path, RequirementValue[Any](value=value, state=RequirementState.KNOWN, provenance=Provenance.USER)
            )
    return m


def engine(*components: ComponentRequirement, conflicts: list[str] | None = None) -> EngineResult:
    return EngineResult(components=list(components), conflicts=conflicts or [], avoided=[], notes=[])


def required(name: str, **spec: Any) -> ComponentRequirement:
    return ComponentRequirement(component=name, status=ComponentStatus.REQUIRED, spec=spec)


STORAGE = required("object_storage", access_mode="private", delivery="signed_url", minimum_capacity=5)


# --- the six required TESTING.md cases -------------------------------------------------------------------------


def test_case1_architecture_provider_and_budget_feasible() -> None:
    store = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store"))
    result, configs = assess(engine(STORAGE), requirements(budget=10), [store])
    assert (result.architecture, result.provider, result.budget) == (FEASIBLE, FEASIBLE, FEASIBLE)
    assert [c.bundles for c in configs] == [["Store svc"]] and configs[0].budget_state is FEASIBLE


def test_case2_provider_unverified_when_evidence_is_missing() -> None:
    store = bundle("Store", ["object_storage"], fixed=5)  # offers storage, but no attribute facts
    result, _ = assess(engine(STORAGE), requirements(budget=10), [store])
    assert (result.architecture, result.provider) == (FEASIBLE, UNVERIFIED)
    assert result.budget is UNVERIFIED  # a configuration with an unverified match can at best be UNVERIFIED
    assert any("access_mode" in m for m in result.missing_evidence)


def test_case2b_no_seeded_provider_offers_the_component_is_unverified_not_infeasible() -> None:
    result, configs = assess(engine(required("search_index")), requirements(budget=10), [])
    assert (result.provider, result.budget) == (UNVERIFIED, UNVERIFIED) and configs == []


def test_case3_provider_infeasible_when_every_candidate_is_verified_unsuitable() -> None:
    private_only = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store", public=False))
    public = required("object_storage", access_mode="public", delivery="direct", minimum_capacity=5)
    result, configs = assess(engine(public), requirements(budget=10), [private_only])
    assert (result.architecture, result.provider) == (FEASIBLE, INFEASIBLE)
    assert configs == [] and result.budget is UNVERIFIED
    assert any("among seeded providers" in c for c in result.conflicts)


def test_case4_bundle_is_feasible_where_summed_component_minima_look_too_expensive() -> None:
    db, auth = required("relational_database"), required("authentication")
    separate = [
        bundle("DBCo", ["relational_database"], fixed=10),
        bundle("AuthCo", ["authentication"], fixed=10),
        bundle("StoreCo", ["object_storage"], fixed=10, extra=full_storage_facts("StoreCo")),
    ]
    all_in_one = bundle(
        "AllInOne",
        ["relational_database", "authentication", "object_storage"],
        fixed=15,
        extra=full_storage_facts("AllInOne"),
    )

    result, configs = assess(engine(db, auth, STORAGE), requirements(budget=20), [*separate, all_in_one])

    assert result.budget is FEASIBLE  # 10 + 10 + 10 = 30 > 20 separately, but the bundle costs 15 once
    by_bundles = {tuple(c.bundles): c for c in configs}
    assert by_bundles[("AllInOne svc",)].fixed_monthly == 15
    assert by_bundles[("AllInOne svc",)].budget_state is FEASIBLE
    assert by_bundles[("DBCo svc", "AuthCo svc", "StoreCo svc")].budget_state is INFEASIBLE


def test_case5_requirements_contradict_budget_and_produce_infeasible() -> None:
    reqs = requirements(budget=0, currency="INR")
    with_uploads = with_value(
        reqs,
        "capabilities.file_uploads",
        RequirementValue[bool](value=True, state=RequirementState.KNOWN, provenance=Provenance.USER),
    )
    rules = evaluate(with_uploads)
    paid = bundle("PaidStore", ["object_storage"], fixed=5, extra=full_storage_facts("PaidStore"))

    result, configs = assess(rules, with_uploads, [paid])

    assert result.budget is INFEASIBLE and result.is_infeasible
    assert any("budget" in c.lower() for c in result.conflicts)
    storage = next(c for c in rules.components if c.component == "object_storage")
    assert storage.status is ComponentStatus.REQUIRED  # the requirement is not silently dropped
    assert configs[0].fixed_monthly == 5  # the tradeoff is shown


@pytest.mark.parametrize("budget", [None, 0, 10_000])
def test_case6_compatibility_is_always_deferred(budget: float | None) -> None:
    store = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store"))
    result, _ = assess(engine(STORAGE), requirements(budget=budget), [store])
    assert result.compatibility is DEFERRED


# --- budget semantics (decision-resolution.md G-10) -------------------------------------------------------------


def test_unknown_budget_is_unverified() -> None:
    store = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store"))
    result, _ = assess(engine(STORAGE), requirements(), [store])
    assert result.budget is UNVERIFIED


def test_currency_mismatch_without_exchange_rate_is_unverified() -> None:
    store = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store"))
    result, _ = assess(engine(STORAGE), requirements(budget=2000, currency="INR"), [store])
    assert result.budget is UNVERIFIED


def test_usage_priced_bundle_within_fixed_cost_is_unverified() -> None:
    store = bundle("Store", ["object_storage"], fixed=0, usage_priced=True, extra=full_storage_facts("Store"))
    result, _ = assess(engine(STORAGE), requirements(budget=0), [store])
    assert result.budget is UNVERIFIED


def test_stale_pricing_is_not_used_for_budget() -> None:
    store = bundle("Store", ["object_storage"], fixed=5, extra=full_storage_facts("Store"), pricing_status="STALE")
    result, _ = assess(engine(STORAGE), requirements(budget=10), [store])
    assert result.budget is UNVERIFIED


# --- conflict resolution -----------------------------------------------------------------------------------------


def test_conflicting_hard_rules_make_architecture_infeasible() -> None:
    result, _ = assess(engine(conflicts=["object_storage: hard requirements disagree"]), requirements(budget=10), [])
    assert result.architecture is INFEASIBLE and "object_storage: hard requirements disagree" in result.conflicts


def test_no_components_needing_providers_is_vacuously_feasible_with_explanation() -> None:
    not_needed = ComponentRequirement(component="object_storage", status=ComponentStatus.NOT_REQUIRED)
    result, _ = assess(engine(not_needed), requirements(budget=0), [])
    assert (result.provider, result.budget) == (FEASIBLE, FEASIBLE)
    assert any("no REQUIRED" in e for e in result.explanations)


def test_undetermined_component_blocks_a_feasible_claim() -> None:
    """Walkthrough e2/e3 regression (decision-resolution.md G-17): nothing REQUIRED yet, but storage undetermined."""
    undetermined = ComponentRequirement(
        component="object_storage", status=ComponentStatus.UNDETERMINED, spec={"access_mode": UNKNOWN}
    )
    result, _ = assess(engine(undetermined), requirements(), [])
    assert (result.provider, result.budget) == (UNVERIFIED, UNVERIFIED)
    assert any("UNDETERMINED" in e and "object_storage" in e for e in result.explanations)


def test_seeded_corpus_zero_rupee_budget_with_uploads_is_unverified_not_infeasible() -> None:
    """Real seed data: R2's free tier is usage-priced, so ₹0 cannot be proven infeasible or feasible."""
    reqs = with_value(
        requirements(budget=0, currency="INR"),
        "capabilities.file_uploads",
        RequirementValue[bool](value=True, state=RequirementState.KNOWN, provenance=Provenance.USER),
    )
    result, configs = assess(evaluate(reqs), reqs, load_seed_bundles())
    assert (result.provider, result.budget) == (FEASIBLE, UNVERIFIED)
    assert {tuple(c.bundles) for c in configs} == {("Cloudflare R2",), ("Supabase Free",), ("Supabase Pro",)}


def test_excluded_offering_is_explained() -> None:
    """Walkthrough 0 regression (decision-resolution.md G-16): say why a seeded plan is not an option."""
    reqs = requirements(budget=10)
    two_gb = required("object_storage", access_mode="private", delivery=UNKNOWN, minimum_capacity=2)
    result, configs = assess(engine(two_gb), reqs, load_seed_bundles())
    assert "Supabase Free" not in {b for c in configs for b in c.bundles}
    assert any("Supabase Free" in e and "VIOLATED" in e and "limit 1" in e for e in result.explanations)


# --- DATABASE-001 real-seed feasibility (V1.1, spec gap G-18; walkthrough evidence WALKTHROUGH.md e2/e3/e4) --------

DATABASE_UNKNOWN_CAPACITY = required("relational_database", minimum_capacity=UNKNOWN)
DATABASE_SMALL = required("relational_database", minimum_capacity=0.02)  # e4: "20 MB DB"
DATABASE_LARGE = required("relational_database", minimum_capacity=10)
SMALL_STORAGE = required("object_storage", access_mode="private", delivery="signed_url", minimum_capacity=0.5)


def test_database_unverified_against_real_seed_when_capacity_unknown() -> None:
    result, configs = assess(engine(DATABASE_UNKNOWN_CAPACITY), requirements(budget=25), load_seed_bundles())
    assert result.provider is UNVERIFIED
    assert {"Supabase Free", "Supabase Pro"} <= {b for c in configs for b in c.bundles}


def test_database_satisfied_when_stated_capacity_fits_the_free_tier() -> None:
    result, configs = assess(engine(DATABASE_SMALL), requirements(budget=25), load_seed_bundles())
    assert result.provider is FEASIBLE
    free = next(c for c in configs if c.bundles == ["Supabase Free"])
    assert free.provider_state is FEASIBLE


def test_database_infeasible_when_stated_capacity_exceeds_every_seeded_limit() -> None:
    result, configs = assess(engine(DATABASE_LARGE), requirements(budget=25), load_seed_bundles())
    assert result.provider is INFEASIBLE
    assert configs == []


def test_database_and_object_storage_covered_by_one_seeded_supabase_bundle() -> None:
    """Bundle-awareness (decision-resolution.md G-10) applies to DATABASE-001 too, not just STORAGE-001."""
    result, configs = assess(engine(DATABASE_SMALL, SMALL_STORAGE), requirements(budget=25), load_seed_bundles())
    covers = next(c for c in configs if c.bundles == ["Supabase Free"]).covers
    assert covers == {"relational_database": "Supabase Free", "object_storage": "Supabase Free"}
    assert result.provider is FEASIBLE
