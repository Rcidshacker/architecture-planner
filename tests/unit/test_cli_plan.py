"""`architect plan`: clarification loop on the terminal, then all three outputs from one plan."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from architect.cli import main
from architect.requirements import Application, Provenance, RequirementModel


def write_model(path: Path, confirmed: bool) -> None:
    model = RequirementModel(application=Application(description="Photo journal app"), confirmed=confirmed)
    path.write_text(model.model_dump_json(), encoding="utf-8")


def feed_input(monkeypatch: pytest.MonkeyPatch, lines: list[str]) -> list[str]:
    prompts: list[str] = []
    it: Iterator[str] = iter(lines)

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(it)

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


def test_plan_refuses_unconfirmed_requirements(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    req = tmp_path / "req.json"
    write_model(req, confirmed=False)
    assert main(["plan", str(req), "--out-dir", str(tmp_path / "out")]) == 2
    assert "architect review" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_plan_asks_clarifications_then_writes_three_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    req, out = tmp_path / "req.json", tmp_path / "out"
    write_model(req, confirmed=True)
    # round 1: file_uploads ("maybe" is invalid and re-asked), data_persistence (tied at impact 4);
    # round 2: access_mode, capacity, budget
    prompts = feed_input(monkeypatch, ["maybe", "true", "false", "private", "?", "0"])

    assert main(["plan", str(req), "--out-dir", str(out)]) == 0

    assert "file" in prompts[0].lower() and prompts[0] == prompts[1]  # invalid answer re-prompted
    saved = RequirementModel.model_validate_json(req.read_text(encoding="utf-8"))
    assert saved.capabilities.file_uploads.value is True
    assert saved.capabilities.file_uploads.provenance is Provenance.USER
    assert not saved.storage.minimum_capacity_gb.is_known  # "?" = don't know, stays UNKNOWN
    brief = (out / "architecture_brief.md").read_text(encoding="utf-8")
    diagram = json.loads((out / "diagram.json").read_text(encoding="utf-8"))
    prompt = (out / "agent_prompt.md").read_text(encoding="utf-8")
    assert "object_storage.minimum_capacity: UNKNOWN" in brief
    assert "blocking_unknowns_already_asked" in brief
    assert {n["id"] for n in diagram["nodes"]} == {"application", "object_storage"}
    assert prompt in brief  # the brief embeds the exact same prompt
