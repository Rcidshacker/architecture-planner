"""Feasibility result contract (SCHEMA.md, decision-resolution.md)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FeasibilityState(StrEnum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNVERIFIED = "UNVERIFIED"
    DEFERRED = "DEFERRED"


type Dimension = Literal[FeasibilityState.FEASIBLE, FeasibilityState.INFEASIBLE, FeasibilityState.UNVERIFIED]


class ProviderConfiguration(BaseModel):
    """A set of bundles covering every REQUIRED component (decision-resolution.md G-10)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundles: list[str]
    covers: dict[str, str]
    """component -> bundle name"""
    provider_state: Dimension
    budget_state: Dimension
    fixed_monthly: float | None = None
    currency: str | None = None
    explanations: list[str] = []


class FeasibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    architecture: Dimension
    provider: Dimension
    budget: Dimension
    compatibility: Literal[FeasibilityState.DEFERRED] = FeasibilityState.DEFERRED
    explanations: list[str] = []
    conflicts: list[str] = []
    missing_evidence: list[str] = []

    @property
    def is_infeasible(self) -> bool:
        """True when any dimension is INFEASIBLE."""
        return FeasibilityState.INFEASIBLE in (self.architecture, self.provider, self.budget)
