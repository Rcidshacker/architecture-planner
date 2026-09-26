"""Step 2 verify against the real LLM: the hand-written description through `claude -p`."""

import pytest

from architect.extraction import claude_cli, extract
from architect.requirements import Provenance, RequirementState
from architect.requirements.fields import FIELD_PATHS, get_value

DESCRIPTION = (
    "I'm building PaperPal, a web app where students log in, upload their lecture PDFs, "
    "and get AI-generated summaries. I expect around 300 students. My budget is ₹1500 per month."
)
STATED_NUMBERS = {"workload.users": 300, "constraints.monthly_budget": 1500}


@pytest.mark.integration
def test_live_extraction_tags_stated_facts_and_invents_nothing() -> None:
    result = extract(DESCRIPTION, claude_cli)
    req = result.requirements
    print("issues:", result.issues)

    for path in ("capabilities.file_uploads", "capabilities.ai_inference", "capabilities.authentication"):
        rv = get_value(req, path)
        assert (rv.value, rv.state, rv.provenance) == (True, RequirementState.KNOWN, Provenance.USER), path
    for path, number in STATED_NUMBERS.items():
        rv = get_value(req, path)
        assert (rv.value, rv.state, rv.provenance) == (number, RequirementState.KNOWN, Provenance.USER), path

    # Nothing invented: the only numbers in the description are the stated ones, and nothing
    # unmentioned (payments, realtime, capacity...) may be KNOWN.
    for path in FIELD_PATHS:
        rv = get_value(req, path)
        if isinstance(rv.value, int | float) and not isinstance(rv.value, bool):
            assert path in STATED_NUMBERS, f"invented number at {path}: {rv.value}"
    for path in ("capabilities.payments", "capabilities.realtime", "storage.minimum_capacity_gb"):
        assert get_value(req, path).state is not RequirementState.KNOWN, path
