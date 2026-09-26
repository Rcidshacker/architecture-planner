"""Dotted-path access to requirement fields (e.g. `capabilities.file_uploads`)."""

import json
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from architect.requirements.models import Provenance, RequirementModel, RequirementState, RequirementValue

_SECTIONS = ("application", "capabilities", "workload", "operations", "constraints", "storage")


def _section_type(section: str) -> type[BaseModel]:
    annotation = RequirementModel.model_fields[section].annotation
    assert isinstance(annotation, type) and issubclass(annotation, BaseModel)
    return annotation


FIELD_PATHS: tuple[str, ...] = tuple(
    f"{section}.{name}"
    for section in _SECTIONS
    for name in _section_type(section).model_fields
    if (section, name) != ("application", "description")  # the input itself, not an extracted field
)
"""Every requirement-value field, in schema order."""


def _split(path: str) -> tuple[str, str]:
    if path not in FIELD_PATHS:
        raise KeyError(f"unknown requirement field {path!r}")
    section, name = path.split(".")
    return section, name


def get_value(model: RequirementModel, path: str) -> RequirementValue[Any]:
    section, name = _split(path)
    value: RequirementValue[Any] = getattr(getattr(model, section), name)
    return value


def value_adapter(path: str) -> TypeAdapter[RequirementValue[Any]]:
    """Validator for the typed RequirementValue at `path`."""
    section, name = _split(path)
    return TypeAdapter(_section_type(section).model_fields[name].annotation)


def parse_user_value(path: str, raw: str, source: str) -> RequirementValue[Any]:
    """Parse text the user typed into a KNOWN/USER value for `path`; `?` means UNKNOWN.

    Raises:
        KeyError: `path` is not a requirement field.
        ValueError: `raw` is not a valid value for the field.
    """
    adapter = value_adapter(path)
    text = raw.strip()
    if text == "?":
        return RequirementValue()
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError:
        parsed = text
    entry = {"state": RequirementState.KNOWN, "provenance": Provenance.USER, "source_text": f"{source}: {text}"}
    try:
        return adapter.validate_python({**entry, "value": parsed})
    except ValidationError as e:
        try:  # e.g. a name typed as "2048": keep the literal text
            return adapter.validate_python({**entry, "value": text})
        except ValidationError:
            raise ValueError(f"invalid value {raw!r} for {path}: {e.errors()[0]['msg']}") from e


def with_value(model: RequirementModel, path: str, value: RequirementValue[Any]) -> RequirementModel:
    """Return a copy of `model` with `path` replaced by `value`, re-validated against the field type."""
    section, name = _split(path)
    checked = value_adapter(path).validate_python(value.model_dump())
    new_section = getattr(model, section).model_copy(update={name: checked})
    return model.model_copy(update={section: new_section})
