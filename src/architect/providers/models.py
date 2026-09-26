"""Provider fact and bundle contracts (SCHEMA.md G-14)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

type FactValue = str | int | float | bool | list[str]


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ProviderFact(BaseModel):
    """One hand-seeded provider fact. Source and timestamps are mandatory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    service: str
    fact_type: Literal["capability", "limitation", "pricing", "free_tier", "region", "integration"]
    key: str
    value: FactValue
    source_url: str
    retrieved_at: datetime
    verified_at: datetime
    verification_status: VerificationStatus

    @property
    def is_verified(self) -> bool:
        return self.verification_status is VerificationStatus.VERIFIED

    @model_validator(mode="after")
    def _value_type_matches_key(self) -> Self:
        """Typed fact keys (SCHEMA.md G-14) are checked here so bad seed data fails at load."""
        v = self.value
        is_number = isinstance(v, int | float) and not isinstance(v, bool)
        if self.key == "fixed_monthly" and not is_number:
            raise ValueError(f"{self.ref}: fixed_monthly must be a number")
        if self.key == "usage_priced" and not isinstance(v, bool):
            raise ValueError(f"{self.ref}: usage_priced must be a boolean")
        if self.key == "currency" and not isinstance(v, str):
            raise ValueError(f"{self.ref}: currency must be a string")
        if self.key.endswith(".max_capacity_gb") and not (is_number or v == "unlimited"):
            raise ValueError(f"{self.ref}: max_capacity_gb must be a number or 'unlimited'")
        return self

    @property
    def ref(self) -> str:
        return f"{self.provider}/{self.service} {self.key}"


class CostModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    currency: str
    fixed_monthly: float
    usage_priced: bool


class ProviderBundle(BaseModel):
    """One plan of one provider. Capabilities and cost must be backed by `evidence` facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    services: list[str]
    included_capabilities: list[str]
    cost_model: CostModel | None = None
    constraints: list[str] = []
    evidence: list[ProviderFact]

    @property
    def name(self) -> str:
        return f"{self.provider} {'+'.join(self.services)}"

    def fact(self, key: str) -> ProviderFact | None:
        """Return the evidence fact with this key, if any."""
        return next((f for f in self.evidence if f.key == key), None)

    @model_validator(mode="after")
    def _claims_are_backed_by_evidence(self) -> Self:
        for capability in self.included_capabilities:
            fact = self.fact(f"component.{capability}")
            if fact is None or fact.value is not True:
                raise ValueError(f"capability {capability!r} has no backing component.{capability} fact")
        if self.cost_model is not None:
            for key, declared in self.cost_model.model_dump().items():
                fact = self.fact(key)
                if fact is None or fact.fact_type != "pricing" or fact.value != declared:
                    raise ValueError(f"cost_model.{key}={declared!r} has no matching pricing fact")
        return self
