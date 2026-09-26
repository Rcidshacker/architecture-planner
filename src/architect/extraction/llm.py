"""The V1 LLM backend: the `claude` CLI as a subprocess (ARCHITECTURE.md)."""

import shutil
import subprocess

from architect.extraction.extract import ExtractionError


def claude_cli(prompt: str, timeout_s: float = 300) -> str:
    """Send `prompt` to `claude -p` and return its text response.

    Raises:
        ExtractionError: the CLI is missing, fails, or times out.
    """
    exe = shutil.which("claude")
    if exe is None:
        raise ExtractionError("the 'claude' CLI was not found on PATH")
    try:
        done = subprocess.run(
            [exe, "-p", "--output-format", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise ExtractionError(f"claude CLI timed out after {timeout_s}s") from e
    if done.returncode != 0:
        detail = (done.stderr.strip() or done.stdout.strip())[:500]  # the CLI reports some errors on stdout
        raise ExtractionError(f"claude CLI exited {done.returncode}: {detail}")
    return done.stdout
