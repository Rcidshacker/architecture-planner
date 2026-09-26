"""Step 2 verify: a hand-written description extracts correctly tagged output with nothing invented.

The LLM is faked at the `prompt -> text` seam; the canned responses are what a model could plausibly
return, including invented values the extractor must refuse.
"""

import json
from typing import Any

import pytest

from architect.extraction import ExtractionError, extract
from architect.requirements import Provenance, RequirementState
from architect.requirements.fields import FIELD_PATHS, get_value

DESCRIPTION = (
    "I'm building PaperPal, a web app where students log in, upload their lecture PDFs, "
    "and get AI-generated summaries. I expect around 300 students. My budget is ₹1500 per month."
)

HONEST_RESPONSE: dict[str, dict[str, Any]] = {
    "application.name": {"value": "PaperPal", "state": "KNOWN", "provenance": "USER", "source_text": "PaperPal"},
    "capabilities.authentication": {
        "value": True,
        "state": "KNOWN",
        "provenance": "USER",
        "source_text": "students log in",
    },
    "capabilities.file_uploads": {
        "value": True,
        "state": "KNOWN",
        "provenance": "USER",
        "source_text": "upload their lecture PDFs",
    },
    "capabilities.ai_inference": {
        "value": True,
        "state": "KNOWN",
        "provenance": "USER",
        "source_text": "AI-generated summaries",
    },
    "operations.ai_request_mode": {
        "value": "asynchronous",
        "state": "INFERRED",
        "provenance": "INFERENCE",
        "source_text": "get AI-generated summaries",
    },
    "workload.users": {"value": 300, "state": "KNOWN", "provenance": "USER", "source_text": "around 300 students"},
    "constraints.monthly_budget": {
        "value": 1500,
        "state": "KNOWN",
        "provenance": "USER",
        "source_text": "₹1500 per month",
    },
    "constraints.currency": {"value": "INR", "state": "KNOWN", "provenance": "USER", "source_text": "₹1500"},
    "capabilities.realtime": {"value": None, "state": "UNKNOWN", "provenance": "UNKNOWN"},
}

EXPECTED_TAGS = {
    "application.name": ("PaperPal", RequirementState.KNOWN, Provenance.USER),
    "capabilities.authentication": (True, RequirementState.KNOWN, Provenance.USER),
    "capabilities.file_uploads": (True, RequirementState.KNOWN, Provenance.USER),
    "capabilities.ai_inference": (True, RequirementState.KNOWN, Provenance.USER),
    "operations.ai_request_mode": ("asynchronous", RequirementState.INFERRED, Provenance.INFERENCE),
    "workload.users": (300, RequirementState.KNOWN, Provenance.USER),
    "constraints.monthly_budget": (1500, RequirementState.KNOWN, Provenance.USER),
    "constraints.currency": ("INR", RequirementState.KNOWN, Provenance.USER),
}


def fake_llm(response: dict[str, Any] | str) -> Any:
    prompts: list[str] = []

    def llm(prompt: str) -> str:
        prompts.append(prompt)
        return response if isinstance(response, str) else "Here you go:\n```json\n" + json.dumps(response) + "\n```"

    llm.prompts = prompts  # type: ignore[attr-defined]
    return llm


def test_hand_written_description_is_tagged_correctly_and_nothing_else_is_filled() -> None:
    result = extract(DESCRIPTION, fake_llm(HONEST_RESPONSE))

    assert result.issues == []
    assert result.requirements.confirmed is False
    assert result.requirements.application.description == DESCRIPTION
    for path in FIELD_PATHS:
        rv = get_value(result.requirements, path)
        if path in EXPECTED_TAGS:
            assert (rv.value, rv.state, rv.provenance) == EXPECTED_TAGS[path], path
        else:
            assert (rv.value, rv.state, rv.provenance) == (None, RequirementState.UNKNOWN, Provenance.UNKNOWN), path


def test_prompt_carries_description_and_every_field() -> None:
    llm = fake_llm(HONEST_RESPONSE)
    extract(DESCRIPTION, llm)
    prompt = llm.prompts[0]
    assert DESCRIPTION in prompt
    for path in FIELD_PATHS:
        assert path in prompt


@pytest.mark.parametrize(
    ("path", "entry", "issue_fragment"),
    [
        # invented number: quote not in the description
        (
            "storage.minimum_capacity_gb",
            {"value": 100, "state": "KNOWN", "provenance": "USER", "source_text": "100 GB of PDFs"},
            "not found",
        ),
        # numbers may never be INFERRED, even with a real quote
        (
            "workload.peak_concurrency",
            {"value": 30, "state": "INFERRED", "provenance": "INFERENCE", "source_text": "around 300 students"},
            "numeric",
        ),
        # a KNOWN value with no quote at all
        ("capabilities.payments", {"value": True, "state": "KNOWN", "provenance": "USER"}, "not found"),
        # RULE provenance cannot come from extraction
        (
            "capabilities.search",
            {"value": False, "state": "KNOWN", "provenance": "RULE", "source_text": "PaperPal"},
            "provenance",
        ),
        # wrong type
        (
            "capabilities.notifications",
            {"value": "maybe", "state": "KNOWN", "provenance": "USER", "source_text": "PaperPal"},
            "invalid",
        ),
        # state/provenance mismatch
        (
            "capabilities.scheduled_jobs",
            {"value": True, "state": "KNOWN", "provenance": "INFERENCE", "source_text": "PaperPal"},
            "invalid",
        ),
    ],
)
def test_unsupported_values_are_discarded_to_unknown_with_an_issue(
    path: str, entry: dict[str, Any], issue_fragment: str
) -> None:
    result = extract(DESCRIPTION, fake_llm({**HONEST_RESPONSE, path: entry}))

    rv = get_value(result.requirements, path)
    assert (rv.value, rv.state, rv.provenance) == (None, RequirementState.UNKNOWN, Provenance.UNKNOWN)
    assert len(result.issues) == 1
    assert path in result.issues[0] and issue_fragment in result.issues[0]


def test_source_text_match_ignores_case_and_whitespace() -> None:
    entry = {"value": True, "state": "KNOWN", "provenance": "USER", "source_text": "Students   LOG in"}
    result = extract(DESCRIPTION, fake_llm({**HONEST_RESPONSE, "capabilities.authentication": entry}))
    assert result.issues == []
    assert result.requirements.capabilities.authentication.value is True


def test_unknown_field_names_are_reported_not_applied() -> None:
    result = extract(DESCRIPTION, fake_llm({**HONEST_RESPONSE, "capabilities.blockchain": {"value": True}}))
    assert len(result.issues) == 1 and "capabilities.blockchain" in result.issues[0]


def test_non_json_response_is_an_extraction_error() -> None:
    with pytest.raises(ExtractionError):
        extract(DESCRIPTION, fake_llm("Sorry, I can't help with that."))


def test_empty_description_is_rejected_before_calling_the_llm() -> None:
    llm = fake_llm(HONEST_RESPONSE)
    with pytest.raises(ValueError):
        extract("   ", llm)
    assert llm.prompts == []
