# CLAUDE.md

## Project

This repository contains a provider-aware architecture planning tool for developers building software with AI coding agents.

The system turns an application description into a traceable chain:

User description → requirement extraction → human confirmation → architecture rules → abstract component requirements → provider mapping → feasibility analysis → architecture brief / diagram / implementation instructions.

The system must not silently convert missing information, unsupported assumptions, or unverifiable provider facts into confident architectural decisions.

## Stack

- Language: Python 3.12+
- Package manager: uv
- Data contracts / validation: Pydantic v2
- Testing: pytest
- Type checking: mypy
- Lint/format: ruff
- Interface: CLI only for V1. No web framework. The "human requirement review" step (see `docs/ARCHITECTURE.md`) is a terminal review/edit surface, not a web UI, until the reasoning engine is validated.

This stack was chosen for consistency with related local tooling (Trawl) and because V1's validation goal does not require a UI. If this changes, update this section before implementation proceeds.

## Source of truth

Read these documents before making implementation changes:

1. `docs/PRD.md` — product requirements, V1 scope, and build sequence.
2. `docs/ARCHITECTURE.md` — system structure and boundaries.
3. `docs/SCHEMA.md` — data contracts and state model.
4. `docs/TESTING.md` — verification requirements.
5. `docs/requirements-schema.md` — requirement extraction model.
6. `docs/architecture-rules.md` — auditable architecture rules.
7. `docs/decision-resolution.md` — conflict, feasibility, clarification, and stopping behavior.

Do not create competing interpretations of these documents in code. If implementation pressure exposes a genuine specification gap, document the gap and update the relevant source-of-truth document before relying on an invented behavior.

## Critical reasoning constraints

- LLMs extract and explain requirements. They do not directly invent the final architecture.
- Users must review the extracted requirement summary before architecture rules are applied.
- Architecture decisions must have explicit rule/evidence provenance.
- Unknown information remains `UNDETERMINED` rather than being guessed.
- Missing or stale provider evidence remains `UNVERIFIED`.
- Contradictory requirements or constraints can produce `INFEASIBLE`; do not resolve infeasibility by precedence.
- Provider feasibility is bundle-aware. Do not assume every component must be purchased from a separate provider.
- V1 supports single-capability architecture rules only. Multi-capability interaction rules are explicitly deferred.
- Cross-provider compatibility analysis is explicitly deferred in V1 and must not be presented as verified.
- Numeric thresholds must have explicit provenance. Never invent a capacity, QPS, latency, or cost threshold merely to complete a recommendation.
- Every important value used in a decision must be attributable to one of: `USER`, `RULE`, `PROVIDER_FACT`, `INFERENCE`, or `UNKNOWN`.
- Provider facts for V1 may be manually seeded (see `docs/PRD.md` build sequence). Do not build or wire a live scraping integration until the reasoning engine has passed its walkthrough validation.

## Implementation discipline

Before adding a new architectural rule:

1. Define its condition.
2. Define the component requirement it produces.
3. Define required component attributes/specification fields.
4. Define provenance.
5. Define precedence semantics, if applicable.
6. Define conflict behavior.
7. Define whether the result can be `UNDETERMINED`.
8. Add or update tests.

New rules must originate from an actual walkthrough failure or an explicitly justified, user-confirmed requirement — not from a desire to make the rule set look comprehensive.

Before adding a provider capability or pricing fact:

1. Store the source.
2. Store retrieval/verification timestamps.
3. Distinguish verified information from inferred information.
4. Do not silently substitute general LLM knowledge when verified provider information is missing.

## Git rules

- Do not rewrite shared history unless explicitly requested.
- Do not force-push unless explicitly requested.
- Keep commits focused on one logical change.
- Do not commit secrets, API keys, credentials, or local environment files.
- Do not modify generated or vendored files unless the project documentation says they are source-controlled artifacts.

## Commands

- Install dependencies: `uv sync`
- Development server: N/A — V1 is a CLI, not a running service. Entry point: `uv run architect`
- Unit tests: `uv run pytest`
- Integration tests: `uv run pytest -m integration`
- Type check: `uv run mypy src`
- Lint: `uv run ruff check .`
- Build: `uv build`

If the stack changes, update this section first — do not let implementation drift from what's documented here.

## Prohibited behavior

Do not:

- Add an architecture component solely because it is common in production systems.
- Add Redis, queues, Kubernetes, Kafka, microservices, or similar infrastructure without an explicit requirement/rule path.
- Treat provider marketing claims as verified provider facts without source evidence.
- Hide `UNDETERMINED`, `UNVERIFIED`, or `INFEASIBLE` states to make output look cleaner.
- Generate a provider recommendation when the provider corpus lacks verified evidence for the required capability unless the output explicitly marks it `UNVERIFIED`.
- Expand V1 into repository drift detection, arbitrary architecture synthesis, or multi-capability emergent rules.
- Add a learned/ML classification component (e.g., as a substitute for rule evaluation) before the walkthrough in `docs/PRD.md` has run and shown a concrete, evidenced need for it.
