"""Error paths of the claude CLI backend (anti-pattern pass A3). The subprocess is faked."""

import subprocess
from typing import Any

import pytest

from architect.extraction import ExtractionError, claude_cli


def test_missing_cli_is_an_extraction_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    with pytest.raises(ExtractionError, match="not found"):
        claude_cli("prompt")


def test_nonzero_exit_reports_stdout_when_stderr_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: "claude")
    done = subprocess.CompletedProcess(args=[], returncode=1, stdout="Usage limit reached", stderr="")
    monkeypatch.setattr("subprocess.run", lambda *_a, **_k: done)
    with pytest.raises(ExtractionError, match="Usage limit reached"):
        claude_cli("prompt")


def test_timeout_is_an_extraction_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(*_a: Any, **_k: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr("shutil.which", lambda _name: "claude")
    monkeypatch.setattr("subprocess.run", slow)
    with pytest.raises(ExtractionError, match="timed out"):
        claude_cli("prompt", timeout_s=1)


def test_success_returns_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: "claude")
    done = subprocess.CompletedProcess(args=[], returncode=0, stdout='{"a": 1}', stderr="")
    monkeypatch.setattr("subprocess.run", lambda *_a, **_k: done)
    assert claude_cli("prompt") == '{"a": 1}'
