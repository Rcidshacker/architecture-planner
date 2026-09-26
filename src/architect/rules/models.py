"""Component requirement and rule contracts (SCHEMA.md, architecture-rules.md)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from architect.requirements import Provenance

UNKNOWN = "UNKNOWN"
"""Spec attribute sentinel: the attribute's value is not known (never guessed)."""

type SpecValue = str | int | float | bool

# Provider-checkable attribute domains (architecture-rules.md G-5).
ENUM_DOMAINS: dict[tuple[str, str], tuple[str, ...]] = {
    ("object_storage", "access_mode"): ("private", "public"),
    ("object_storage", "delivery"): ("signed_url", "direct"),
}
MIN_QUANTITY_LIMITS: dict[tuple[str, str], str] = {
    ("object_storage", "minimum_capacity"): "object_storage.max_capacity_gb",  # GB
}
"""minimum-quantity attribute -> the provider limitation fact key it is compared against"""


class ComponentStatus(StrEnum):
    REQUIRED = "REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNDETERMINED = "UNDETERMINED"


class RuleCategory(StrEnum):
    HARD_REQUIREMENT = "HARD_REQUIREMENT"
    PREFERENCE = "PREFERENCE"
    DEFAULT_AVOID = "DEFAULT_AVOID"


class ComponentRequirement(BaseModel):
    """An abstract component with provider-checkable spec attributes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component: str
    status: ComponentStatus
    spec: dict[str, SpecValue] = {}
    provenance: list[Provenance] = []
    rules_triggered: list[str] = []
    blocking_unknowns: list[str] = []
