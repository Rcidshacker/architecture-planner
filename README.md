# Architecture Planner (V1)

A provider-aware architecture planning tool for developers who can build applications with AI coding agents but need help converting an application idea into a practical, explainable, evidence-grounded system architecture.

It is **not** a system-design quiz. It's a traceable reasoning workflow — natural-language description → structured requirements → human review → architecture rules → provider mapping → feasibility → brief, diagram data, and coding-agent prompt — where every decision in the output can be traced back to something you said, a documented rule, a sourced provider fact, or an explicit "unknown."

V1 is a CLI. There is no web UI (a deliberate scope decision, see [docs/PRD.md](docs/PRD.md)).

## Quickstart

```bash
uv sync

# 1. Extract requirements from a description (calls the `claude` CLI)
uv run architect extract --description "A SaaS app where users upload resumes and get AI feedback" --out requirements.json

# 2. Review and edit what was extracted
uv run architect review requirements.json

# 3. Resolve architecture, feasibility, and write the outputs
uv run architect plan requirements.json --out-dir architecture
```

`plan` writes `architecture_brief.md`, `diagram.json`, `agent_prompt.md`, and `plan.json` to `--out-dir`.

## The core guarantee

Every requirement field carries a `state` (`KNOWN` / `UNKNOWN` / `INFERRED`) and a `provenance` (`USER` / `RULE` / `PROVIDER_FACT` / `INFERENCE` / `UNKNOWN`). A value is never presented as verified when it isn't. Numeric thresholds are never invented from a boolean capability — they come from what you stated, a documented rule, a sourced provider fact, or they stay `UNKNOWN`. Feasibility has four dimensions (architecture / provider / budget / compatibility); compatibility across providers is explicitly `DEFERRED` in V1, not claimed. When the tool doesn't know something, the output says `UNDETERMINED` or `UNVERIFIED` instead of guessing. Full rules in [docs/decision-resolution.md](docs/decision-resolution.md).

## What's built (V1 + V1.1)

- **Rules:** `STORAGE-001` (file uploads → object storage), `CACHE-DEFAULT-001` (no cache without evidence), `DATABASE-001` (persistent data → relational database) — see [docs/architecture-rules.md](docs/architecture-rules.md).
- **Provider facts:** hand-seeded, sourced records for Cloudflare R2 and Supabase (Free/Pro) — a bundle example and a point-solution example, used to test bundle-aware feasibility.
- **Verification:** 19 gates in [GATES.md](GATES.md), each backed by a real test command and its recorded evidence. 136 unit tests + 1 live-LLM integration test (`uv run pytest`, `uv run pytest -m integration`).
- **Walkthrough:** [WALKTHROUGH.md](WALKTHROUGH.md) — the author's own run plus 5 external beginner-style descriptions, logging extraction completeness, invented-value audits, and blocking unknowns per run.

## Explicitly deferred (not gaps — decisions)

Per [docs/PRD.md](docs/PRD.md)'s out-of-scope list: a web UI, a learned/ML classification component, live provider-documentation scraping, repository-wide architecture inference, cross-provider compatibility verification, automatic deployment. These stay out until walkthrough evidence justifies them — see PRD.md's build-sequence and success-criteria sections for how that bar is set.

## Docs

The full spec lives in [docs/](docs/): [PRD](docs/PRD.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [SCHEMA](docs/SCHEMA.md) · [TESTING](docs/TESTING.md) · [requirements-schema](docs/requirements-schema.md) · [architecture-rules](docs/architecture-rules.md) · [decision-resolution](docs/decision-resolution.md). [CLAUDE.md](CLAUDE.md) has the stack and command reference.

## Stack

Python 3.12+, [uv](https://docs.astral.sh/uv/), Pydantic v2, pytest, mypy (strict), ruff.

## License

No license file is present in this repository yet.
