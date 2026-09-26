"""Step 1 verify: SCHEMA.md YAML shapes round-trip into typed objects without validation errors."""

from typing import Any

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from architect.clarification import ClarificationQuestion
from architect.feasibility import FeasibilityResult
from architect.providers import ProviderBundle, ProviderFact
from architect.requirements import RequirementModel, RequirementValue
from architect.resolution import ArchitectureModel
from architect.rules import ComponentRequirement

REQUIREMENT_VALUE = """
value: true
state: KNOWN
provenance: USER
confidence: 0.9
source_text: users upload PDFs
"""


def _unknown() -> str:
    return "{value: null, state: UNKNOWN, provenance: UNKNOWN}"


REQUIREMENT_MODEL = f"""
confirmed: false
application:
  name: {{value: DocSummarizer, state: KNOWN, provenance: USER, source_text: DocSummarizer}}
  description: A tool where users upload PDFs and get AI summaries.
capabilities:
  authentication: {{value: true, state: INFERRED, provenance: INFERENCE, source_text: users}}
  file_uploads: {{value: true, state: KNOWN, provenance: USER, source_text: upload PDFs}}
  ai_inference: {{value: true, state: KNOWN, provenance: USER, source_text: AI summaries}}
  realtime: {_unknown()}
  payments: {_unknown()}
  search: {_unknown()}
  scheduled_jobs: {_unknown()}
  notifications: {_unknown()}
workload:
  users: {{value: 500, state: KNOWN, provenance: USER, source_text: 500 users}}
  peak_concurrency: {_unknown()}
  read_write_ratio: {{value: {{read: 0.8, write: 0.2}}, state: KNOWN, provenance: USER}}
  latency_target_ms: {_unknown()}
  request_burstiness: {{value: low, state: KNOWN, provenance: USER}}
operations:
  ai_request_mode: {{value: asynchronous, state: KNOWN, provenance: USER}}
  ai_request_duration: {{value: seconds, state: INFERRED, provenance: INFERENCE}}
  user_waits_for_completion: {_unknown()}
  retryable_background_work: {_unknown()}
  public_asset_delivery: {{value: false, state: KNOWN, provenance: USER}}
constraints:
  monthly_budget: {{value: 0, state: KNOWN, provenance: USER}}
  currency: {{value: INR, state: KNOWN, provenance: USER}}
  team_size: {{value: 1, state: KNOWN, provenance: USER}}
  provider_lock_in: {_unknown()}
  region_requirements: {{value: [ap-south-1], state: KNOWN, provenance: USER}}
storage:
  access_mode: {{value: private, state: KNOWN, provenance: USER}}
  delivery: {_unknown()}
  minimum_capacity_gb: {_unknown()}
"""

# ARCHITECTURE.md component example, plus SCHEMA.md's rules_triggered / blocking_unknowns fields.
COMPONENT_REQUIREMENT = """
component: object_storage
status: REQUIRED
spec:
  access_mode: private
  delivery: signed_url
  minimum_capacity: UNKNOWN
provenance: [USER, RULE]
rules_triggered: [STORAGE-001]
blocking_unknowns: [minimum_capacity]
"""

PROVIDER_FACT = """
provider: Cloudflare
service: R2
fact_type: pricing
key: fixed_monthly
value: 0
source_url: https://developers.cloudflare.com/r2/pricing/
retrieved_at: 2026-09-25T15:01:00Z
verified_at: 2026-09-25T15:01:00Z
verification_status: VERIFIED
"""

PROVIDER_BUNDLE = """
provider: Cloudflare
services: [R2]
included_capabilities: [object_storage]
cost_model: {currency: USD, fixed_monthly: 0, usage_priced: true}
constraints: []
evidence:
  - {provider: Cloudflare, service: R2, fact_type: capability, key: component.object_storage, value: true,
     source_url: "https://developers.cloudflare.com/r2/", retrieved_at: 2026-09-25T15:01:00Z,
     verified_at: 2026-09-25T15:01:00Z, verification_status: VERIFIED}
  - {provider: Cloudflare, service: R2, fact_type: pricing, key: currency, value: USD,
     source_url: "https://developers.cloudflare.com/r2/pricing/", retrieved_at: 2026-09-25T15:01:00Z,
     verified_at: 2026-09-25T15:01:00Z, verification_status: VERIFIED}
  - {provider: Cloudflare, service: R2, fact_type: pricing, key: fixed_monthly, value: 0,
     source_url: "https://developers.cloudflare.com/r2/pricing/", retrieved_at: 2026-09-25T15:01:00Z,
     verified_at: 2026-09-25T15:01:00Z, verification_status: VERIFIED}
  - {provider: Cloudflare, service: R2, fact_type: pricing, key: usage_priced, value: true,
     source_url: "https://developers.cloudflare.com/r2/pricing/", retrieved_at: 2026-09-25T15:01:00Z,
     verified_at: 2026-09-25T15:01:00Z, verification_status: VERIFIED}
"""

FEASIBILITY_RESULT = """
architecture: FEASIBLE
provider: UNVERIFIED
budget: INFEASIBLE
compatibility: DEFERRED
explanations: [object_storage has no verified provider among seeded providers]
conflicts: [monthly_budget 0 INR below every configuration's fixed cost]
missing_evidence: [Cloudflare/R2 object_storage.max_capacity_gb]
"""

CLARIFICATION_QUESTION = """
field: operations.ai_request_duration
prompt: How long does one AI request take?
decision_impact: 4
uncertainty: 1
priority: 4
blocking_decisions: [queue, worker_pool, timeout_strategy, retry_strategy]
"""

ARCHITECTURE_MODEL = "\n".join(
    [
        "components:",
        "  - " + COMPONENT_REQUIREMENT.strip().replace("\n", "\n    "),
        "provider_candidates: []",
        "feasibility:",
        "  " + FEASIBILITY_RESULT.strip().replace("\n", "\n  "),
        "decisions: []",
        "unresolved_items: [object_storage.minimum_capacity]",
        "avoided_items: [cache]",
        "scaling_triggers: []",
    ]
)

CASES: list[tuple[type[BaseModel], str]] = [
    (RequirementValue, REQUIREMENT_VALUE),
    (RequirementModel, REQUIREMENT_MODEL),
    (ComponentRequirement, COMPONENT_REQUIREMENT),
    (ProviderFact, PROVIDER_FACT),
    (ProviderBundle, PROVIDER_BUNDLE),
    (FeasibilityResult, FEASIBILITY_RESULT),
    (ClarificationQuestion, CLARIFICATION_QUESTION),
    (ArchitectureModel, ARCHITECTURE_MODEL),
]


@pytest.mark.parametrize(("model", "text"), CASES, ids=[c[0].__name__ for c in CASES])
def test_schema_shape_round_trips(model: type[BaseModel], text: str) -> None:
    data: dict[str, Any] = yaml.safe_load(text)
    obj = model.model_validate(data)
    dumped = obj.model_dump(mode="json", exclude_unset=True)
    assert model.model_validate(dumped) == obj


@pytest.mark.parametrize(
    "bad",
    [
        {"value": True, "state": "UNKNOWN", "provenance": "UNKNOWN"},  # UNKNOWN must carry no value
        {"value": True, "state": "KNOWN", "provenance": "INFERENCE"},  # inference cannot be KNOWN
        {"value": True, "state": "INFERRED", "provenance": "USER"},
        {"value": None, "state": "KNOWN", "provenance": "USER"},
        {"value": True, "state": "KNOWN", "provenance": "PROVIDER_FACT"},  # not valid for requirements
    ],
)
def test_requirement_value_rejects_inconsistent_state_and_provenance(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        RequirementValue[bool].model_validate(bad)


def test_requirement_field_types_are_enforced() -> None:
    data = yaml.safe_load(REQUIREMENT_MODEL)
    data["operations"]["ai_request_duration"]["value"] = "hours"  # not in fast|seconds|minutes
    with pytest.raises(ValidationError):
        RequirementModel.model_validate(data)


def test_compatibility_can_only_be_deferred() -> None:
    data = yaml.safe_load(FEASIBILITY_RESULT)
    data["compatibility"] = "FEASIBLE"
    with pytest.raises(ValidationError):
        FeasibilityResult.model_validate(data)


def test_bundle_capability_without_backing_fact_is_rejected() -> None:
    data = yaml.safe_load(PROVIDER_BUNDLE)
    data["included_capabilities"].append("relational_database")
    with pytest.raises(ValidationError):
        ProviderBundle.model_validate(data)


def test_bundle_cost_model_must_match_pricing_facts() -> None:
    data = yaml.safe_load(PROVIDER_BUNDLE)
    data["cost_model"]["fixed_monthly"] = 5
    with pytest.raises(ValidationError):
        ProviderBundle.model_validate(data)


def test_provider_fact_requires_source_evidence() -> None:
    data = yaml.safe_load(PROVIDER_FACT)
    del data["source_url"]
    with pytest.raises(ValidationError):
        ProviderFact.model_validate(data)


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [("fixed_monthly", "25"), ("usage_priced", "yes"), ("currency", 840)],
)
def test_pricing_fact_types_are_validated_at_load(key: str, bad_value: Any) -> None:
    """Anti-pattern pass A1: bad seed types fail at the boundary, not deep in feasibility."""
    data = yaml.safe_load(PROVIDER_BUNDLE)
    data.pop("cost_model")
    for fact in data["evidence"]:
        if fact["key"] == key:
            fact["value"] = bad_value
    with pytest.raises(ValidationError):
        ProviderBundle.model_validate(data)


def test_capacity_limit_fact_must_be_number_or_unlimited() -> None:
    data = yaml.safe_load(PROVIDER_BUNDLE)
    data["evidence"].append(
        {**data["evidence"][0], "fact_type": "limitation", "key": "object_storage.max_capacity_gb", "value": "lots"}
    )
    with pytest.raises(ValidationError):
        ProviderBundle.model_validate(data)
