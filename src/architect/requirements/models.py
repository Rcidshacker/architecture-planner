"""Requirement model and provenance types (SCHEMA.md, requirements-schema.md)."""

import math
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator


class Provenance(StrEnum):
    USER = "USER"
    RULE = "RULE"
    PROVIDER_FACT = "PROVIDER_FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class RequirementState(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    INFERRED = "INFERRED"


# SCHEMA.md G-13: the only legal state/provenance pairings for a requirement value.
_ALLOWED_PROVENANCE = {
    RequirementState.KNOWN: {Provenance.USER, Provenance.RULE},
    RequirementState.INFERRED: {Provenance.INFERENCE},
    RequirementState.UNKNOWN: {Provenance.UNKNOWN},
}


class RequirementValue[T](BaseModel):
    """One requirement field: a typed value plus its state and provenance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: T | None = None
    state: RequirementState = RequirementState.UNKNOWN
    provenance: Provenance = Provenance.UNKNOWN
    confidence: float | None = None
    source_text: str | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.provenance not in _ALLOWED_PROVENANCE[self.state]:
            raise ValueError(f"state {self.state} cannot have provenance {self.provenance}")
        if (self.value is None) != (self.state is RequirementState.UNKNOWN):
            raise ValueError("value must be null exactly when state is UNKNOWN")
        v = self.value
        if isinstance(v, int | float) and not isinstance(v, bool) and not (math.isfinite(v) and v >= 0):
            raise ValueError(f"numeric requirement values must be finite and non-negative, got {v!r}")
        return self

    @property
    def is_known(self) -> bool:
        """True when the value is present (KNOWN or INFERRED)."""
        return self.state is not RequirementState.UNKNOWN


class _Section(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Application(_Section):
    name: RequirementValue[str] = RequirementValue()
    description: str


class Capabilities(_Section):
    authentication: RequirementValue[bool] = RequirementValue()
    file_uploads: RequirementValue[bool] = RequirementValue()
    ai_inference: RequirementValue[bool] = RequirementValue()
    realtime: RequirementValue[bool] = RequirementValue()
    payments: RequirementValue[bool] = RequirementValue()
    search: RequirementValue[bool] = RequirementValue()
    scheduled_jobs: RequirementValue[bool] = RequirementValue()
    notifications: RequirementValue[bool] = RequirementValue()
    data_persistence: RequirementValue[bool] = RequirementValue()


class Workload(_Section):
    users: RequirementValue[int] = RequirementValue()
    peak_concurrency: RequirementValue[int] = RequirementValue()
    read_write_ratio: RequirementValue[dict[str, float]] = RequirementValue()
    latency_target_ms: RequirementValue[float] = RequirementValue()
    request_burstiness: RequirementValue[Literal["low", "medium", "high"]] = RequirementValue()


class Operations(_Section):
    ai_request_mode: RequirementValue[Literal["synchronous", "asynchronous", "mixed"]] = RequirementValue()
    ai_request_duration: RequirementValue[Literal["fast", "seconds", "minutes"]] = RequirementValue()
    user_waits_for_completion: RequirementValue[bool] = RequirementValue()
    retryable_background_work: RequirementValue[bool] = RequirementValue()
    public_asset_delivery: RequirementValue[bool] = RequirementValue()


class Constraints(_Section):
    monthly_budget: RequirementValue[float] = RequirementValue()
    currency: RequirementValue[str] = RequirementValue()
    team_size: RequirementValue[int] = RequirementValue()
    provider_lock_in: RequirementValue[Literal["low", "medium", "high"]] = RequirementValue()
    region_requirements: RequirementValue[list[str]] = RequirementValue()


class Storage(_Section):
    access_mode: RequirementValue[Literal["private", "public"]] = RequirementValue()
    delivery: RequirementValue[Literal["signed_url", "direct"]] = RequirementValue()
    minimum_capacity_gb: RequirementValue[float] = RequirementValue()


class Database(_Section):
    """DATABASE-001 spec attributes (requirements-schema.md G-18), mirroring Storage."""

    minimum_capacity_gb: RequirementValue[float] = RequirementValue()


class RequirementModel(_Section):
    """The full requirement model. `confirmed` is set only by human review."""

    confirmed: bool = False
    application: Application
    capabilities: Capabilities = Capabilities()
    workload: Workload = Workload()
    operations: Operations = Operations()
    constraints: Constraints = Constraints()
    storage: Storage = Storage()
    database: Database = Database()
