"""Natural language -> requirement model, with mechanical anti-invention checks (requirements-schema.md G-3)."""

import json
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from architect.requirements import Application, Provenance, RequirementModel, RequirementState
from architect.requirements.fields import FIELD_PATHS, value_adapter, with_value

type LLM = Callable[[str], str]
"""Any `prompt -> response text` callable."""


class ExtractionError(Exception):
    """The LLM response could not be interpreted at all; no requirement model was produced."""


class ExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    requirements: RequirementModel
    issues: list[str]
    """Values the extractor refused; shown to the user in review."""


_PROMPT = """You extract software requirements from an application description.

Return ONLY a JSON object. Keys are field paths from the list below. Each value is an object:
  {{"value": <typed value or null>, "state": "KNOWN" | "INFERRED" | "UNKNOWN",
    "provenance": "USER" | "INFERENCE" | "UNKNOWN", "source_text": <exact quote from the description or null>}}

Rules:
- KNOWN + USER: the description states it explicitly. source_text must be copied verbatim from the description.
- INFERRED + INFERENCE: strongly implied but not stated. source_text must quote the words it is inferred from.
- UNKNOWN + UNKNOWN with value null: anything not stated or clearly implied. When unsure, use UNKNOWN.
- Never invent numbers. Numeric fields are KNOWN only if the number appears in the description; never INFERRED.
- Do not guess to fill a field; UNKNOWN is always acceptable.

Fields (path: type):
{fields}

Description:
\"\"\"{description}\"\"\"
"""

_FIELD_TYPES = {
    "application.name": "string",
    "workload.users": "integer",
    "workload.peak_concurrency": "integer",
    "workload.read_write_ratio": 'object like {"read": 0.8, "write": 0.2}',
    "workload.latency_target_ms": "number",
    "workload.request_burstiness": "low | medium | high",
    "operations.ai_request_mode": "synchronous | asynchronous | mixed",
    "operations.ai_request_duration": "fast | seconds | minutes",
    "constraints.monthly_budget": "number (amount per month)",
    "constraints.currency": "ISO 4217 code, e.g. USD, INR",
    "constraints.team_size": "integer",
    "constraints.provider_lock_in": "low | medium | high (tolerance for lock-in)",
    "constraints.region_requirements": "list of strings",
    "storage.access_mode": "private | public (who may read uploaded files)",
    "storage.delivery": "signed_url | direct (how files are served)",
    "storage.minimum_capacity_gb": "number (GB of file storage needed)",
    "database.minimum_capacity_gb": "number (GB of database storage needed)",
}


def build_prompt(description: str) -> str:
    fields = "\n".join(f"- {path}: {_FIELD_TYPES.get(path, 'boolean')}" for path in FIELD_PATHS)
    return _PROMPT.format(fields=fields, description=description)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _number_text(value: float) -> str:
    """How a stated number is written: `300`, `10` (not `10.0`), `2.5`."""
    return str(int(value)) if float(value).is_integer() else str(value)


def _parse_json_object(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ExtractionError(f"LLM response contains no JSON object: {text[:200]!r}")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise ExtractionError(f"LLM response is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ExtractionError("LLM response JSON is not an object")
    return data


def _refusal(path: str, entry: Any, description: str) -> str | None:
    """Return why `entry` must be discarded, or None if it may be kept."""
    try:
        rv = value_adapter(path).validate_python(entry)
    except ValidationError as e:
        return f"{path}: invalid value discarded ({e.errors()[0]['msg']})"
    if rv.provenance not in (Provenance.USER, Provenance.INFERENCE, Provenance.UNKNOWN):
        return f"{path}: provenance {rv.provenance} is not allowed for extracted requirements; discarded"
    if rv.state is RequirementState.UNKNOWN:
        return None
    quote = _normalize(rv.source_text or "")
    if not quote or quote not in _normalize(description):
        return f"{path}: value {rv.value!r} discarded, its source text was not found in the description"
    is_number = isinstance(rv.value, int | float) and not isinstance(rv.value, bool)
    if is_number and rv.state is RequirementState.INFERRED:
        return f"{path}: inferred numeric value {rv.value!r} discarded; numbers must be stated by the user"
    if isinstance(rv.value, int | float) and is_number and _number_text(rv.value) not in quote.replace(",", ""):
        return f"{path}: value {rv.value!r} discarded, the number does not appear in its source text"
    return None


def extract(description: str, llm: LLM) -> ExtractionResult:
    """Extract a requirement model from `description` using `llm`.

    Raises:
        ValueError: `description` is blank.
        ExtractionError: the LLM response is not a JSON object.
    """
    if not description.strip():
        raise ValueError("'description' is required")
    data = _parse_json_object(llm(build_prompt(description)))

    model = RequirementModel(application=Application(description=description))
    issues = [f"{key}: not a requirement field; ignored" for key in data if key not in FIELD_PATHS]
    for path in FIELD_PATHS:
        if path not in data:
            continue
        refusal = _refusal(path, data[path], description)
        if refusal:
            issues.append(refusal)
        else:
            model = with_value(model, path, value_adapter(path).validate_python(data[path]))
    return ExtractionResult(requirements=model, issues=issues)
