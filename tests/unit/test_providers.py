"""Step 5 verify: a manually entered, sourced provider fact satisfies STORAGE-001's component spec."""

from typing import Any

import pytest

from architect.providers import MatchState, ProviderBundle, VerificationStatus, load_seed_bundles, match
from architect.rules import UNKNOWN, ComponentRequirement, ComponentStatus


def storage(**spec: Any) -> ComponentRequirement:
    full = {"access_mode": UNKNOWN, "delivery": UNKNOWN, "minimum_capacity": UNKNOWN, **spec}
    return ComponentRequirement(component="object_storage", status=ComponentStatus.REQUIRED, spec=full)


@pytest.fixture(scope="module")
def seed() -> dict[str, ProviderBundle]:
    return {b.name: b for b in load_seed_bundles()}


def test_seed_facts_carry_source_and_verification_metadata(seed: dict[str, ProviderBundle]) -> None:
    assert set(seed) == {"Cloudflare R2", "Supabase Free", "Supabase Pro"}
    for bundle in seed.values():
        for fact in bundle.evidence:
            assert fact.source_url.startswith("https://"), fact.ref
            assert fact.verified_at >= fact.retrieved_at, fact.ref
            assert fact.verification_status is VerificationStatus.VERIFIED, fact.ref


def test_seeded_r2_fact_satisfies_storage_001_spec_even_while_attributes_are_unknown(
    seed: dict[str, ProviderBundle],
) -> None:
    result = match(seed["Cloudflare R2"], storage())
    assert result is not None and result.state is MatchState.SATISFIED
    assert result.evidence  # the facts relied on are named


def test_seeded_r2_satisfies_a_fully_specified_spec(seed: dict[str, ProviderBundle]) -> None:
    result = match(seed["Cloudflare R2"], storage(access_mode="private", delivery="signed_url", minimum_capacity=50))
    assert result is not None and result.state is MatchState.SATISFIED


@pytest.mark.parametrize(
    ("capacity", "expected"),
    [(UNKNOWN, MatchState.UNVERIFIED), (0.5, MatchState.SATISFIED), (50, MatchState.VIOLATED)],
)
def test_capacity_cap_on_supabase_free(seed: dict[str, ProviderBundle], capacity: Any, expected: MatchState) -> None:
    result = match(seed["Supabase Free"], storage(minimum_capacity=capacity))
    assert result is not None and result.state is expected


def test_missing_limit_fact_is_unverified_not_assumed(seed: dict[str, ProviderBundle]) -> None:
    result = match(seed["Supabase Pro"], storage(minimum_capacity=50))
    assert result is not None and result.state is MatchState.UNVERIFIED
    assert any("max_capacity_gb" in item for item in result.missing_evidence)


def test_stale_fact_is_not_presented_as_current_verification(seed: dict[str, ProviderBundle]) -> None:
    r2 = seed["Cloudflare R2"]
    stale = [
        f.model_copy(update={"verification_status": VerificationStatus.STALE})
        if f.key == "object_storage.access_mode.public"
        else f
        for f in r2.evidence
    ]
    result = match(r2.model_copy(update={"evidence": stale}), storage(access_mode="public"))
    assert result is not None and result.state is MatchState.UNVERIFIED
    assert any("STALE" in item and "access_mode.public" in item for item in result.missing_evidence)
    assert all("access_mode.public" not in ref for ref in result.evidence)


def test_verified_unsupported_value_is_violated(seed: dict[str, ProviderBundle]) -> None:
    r2 = seed["Cloudflare R2"]
    no_public = [
        f.model_copy(update={"value": False}) if f.key == "object_storage.access_mode.public" else f
        for f in r2.evidence
    ]
    result = match(r2.model_copy(update={"evidence": no_public}), storage(access_mode="public"))
    assert result is not None and result.state is MatchState.VIOLATED


def test_mapping_does_not_invent_capabilities_absent_from_the_corpus(seed: dict[str, ProviderBundle]) -> None:
    search = ComponentRequirement(component="search_index", status=ComponentStatus.REQUIRED)
    assert all(match(bundle, search) is None for bundle in seed.values())
