"""Step 3 verify: an edited value is persisted with provenance USER, overwriting the extraction result."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from architect.cli import apply_edit, main
from architect.requirements import Application, Provenance, RequirementModel, RequirementState, RequirementValue
from architect.requirements.fields import with_value


def extracted_model() -> RequirementModel:
    model = RequirementModel(application=Application(description="students upload PDFs for AI summaries"))
    inferred = RequirementValue[str](
        value="asynchronous",
        state=RequirementState.INFERRED,
        provenance=Provenance.INFERENCE,
        source_text="AI summaries",
    )
    return with_value(model, "operations.ai_request_mode", inferred)


def feed_input(monkeypatch: pytest.MonkeyPatch, lines: list[str]) -> None:
    it: Iterator[str] = iter(lines)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(it))


def test_apply_edit_overwrites_extraction_with_user_provenance() -> None:
    edited = apply_edit(extracted_model(), "operations.ai_request_mode", "synchronous")
    rv = edited.operations.ai_request_mode
    assert (rv.value, rv.state, rv.provenance) == ("synchronous", RequirementState.KNOWN, Provenance.USER)


@pytest.mark.parametrize(
    ("path", "raw", "expected"),
    [
        ("workload.users", "300", 300),
        ("capabilities.file_uploads", "true", True),
        ("constraints.region_requirements", '["ap-south-1"]', ["ap-south-1"]),
        ("constraints.currency", "INR", "INR"),
    ],
)
def test_apply_edit_parses_the_field_type(path: str, raw: str, expected: object) -> None:
    edited = apply_edit(extracted_model(), path, raw)
    assert getattr(getattr(edited, path.split(".")[0]), path.split(".")[1]).value == expected


def test_apply_edit_question_mark_marks_field_unknown() -> None:
    rv = apply_edit(extracted_model(), "operations.ai_request_mode", "?").operations.ai_request_mode
    assert (rv.value, rv.state, rv.provenance) == (None, RequirementState.UNKNOWN, Provenance.UNKNOWN)


def test_apply_edit_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        apply_edit(extracted_model(), "operations.ai_request_mode", "whenever")
    with pytest.raises(KeyError):
        apply_edit(extracted_model(), "capabilities.blockchain", "true")


def test_review_command_persists_edit_as_user_and_confirms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "requirements.json"
    path.write_text(extracted_model().model_dump_json(), encoding="utf-8")
    feed_input(
        monkeypatch, ["operations.ai_request_mode=whenever", "operations.ai_request_mode=synchronous", "confirm"]
    )

    assert main(["review", str(path)]) == 0

    saved = RequirementModel.model_validate_json(path.read_text(encoding="utf-8"))
    rv = saved.operations.ai_request_mode
    assert (rv.value, rv.state, rv.provenance) == ("synchronous", RequirementState.KNOWN, Provenance.USER)
    assert saved.confirmed is True
    out = capsys.readouterr().out
    assert "INFERRED" in out and "INFERENCE" in out  # the extraction was shown before editing
    assert "invalid" in out.lower()  # the bad edit was surfaced, not applied


def test_review_quit_saves_edits_unconfirmed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "requirements.json"
    path.write_text(extracted_model().model_dump_json(), encoding="utf-8")
    feed_input(monkeypatch, ["workload.users=50", "quit"])

    assert main(["review", str(path)]) == 0

    saved = RequirementModel.model_validate_json(path.read_text(encoding="utf-8"))
    assert saved.workload.users.value == 50 and saved.workload.users.provenance is Provenance.USER
    assert saved.confirmed is False


def test_edit_after_confirmation_requires_reconfirmation() -> None:
    confirmed = extracted_model().model_copy(update={"confirmed": True})
    assert apply_edit(confirmed, "workload.users", "10").confirmed is False
