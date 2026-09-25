# TESTING.md — Verification Guide

## Testing goal

Tests must verify not only that the system produces output, but that it preserves the project's core guarantee: unsupported assumptions must not become confident architecture decisions.

## Commands

See `CLAUDE.md` for the authoritative list. Summary:

- Unit + integration tests: `uv run pytest` (integration tests marked and run separately with `uv run pytest -m integration`)
- Type check: `uv run mypy src`
- Lint: `uv run ruff check .`
- Build: `uv build`

## Core unit-test areas

### Requirement extraction

Verify that:

- explicit user values are tagged `USER`.
- missing information remains `UNKNOWN`.
- inference is distinguished from explicit user input.
- invalid types are rejected or surfaced for correction.

### Human review contract

Verify that architecture rules cannot consume an unconfirmed extraction result when confirmation is mandatory.

### Rule engine

Verify that:

- each rule produces documented component states.
- each provider-checkable component includes a specification.
- unsupported numeric thresholds are not invented.
- rule provenance is retained.
- default/avoid rules do not override hard requirements incorrectly.

### Conflict resolution

Test at least:

- normal compatible rules.
- default versus hard requirement.
- direct user constraint versus hard requirement leading to `INFEASIBLE`.
- unresolved fields leading to `UNDETERMINED`.
- precedence applied only after feasibility checks.

### Provider mapping

Verify:

- verified provider facts can satisfy component specifications.
- missing evidence results in `UNVERIFIED`.
- stale provider facts are not presented as current verification.
- bundled provider offerings are evaluated as bundles.
- provider mapping does not invent capabilities absent from the corpus.

### Feasibility

Required cases:

1. Architecture feasible, provider feasible, budget feasible.
2. Architecture feasible, provider `UNVERIFIED`.
3. Architecture feasible, provider `INFEASIBLE`.
4. Provider bundle makes a configuration feasible even though independent component minima would appear too expensive.
5. Requirements contradict budget and produce `INFEASIBLE`.
6. Compatibility remains `DEFERRED` in V1.

### Clarification loop

Verify:

- question priority is computable from schema metadata.
- highest-impact unresolved fields are asked first.
- no hidden user-knowledge estimate is used.
- maximum clarification rounds are enforced.
- unresolved non-blocking questions do not prevent useful output.
- unresolved blocking questions produce explicit `UNDETERMINED` output after the limit.

## Provenance tests

Every important architecture decision should be traceable to one or more of:

- `USER`
- `RULE`
- `PROVIDER_FACT`
- `INFERENCE`
- `UNKNOWN`

A test should fail if the system emits a concrete threshold, capability, provider claim, cost claim, or architecture transition without provenance.

## External validation

Do not validate only with author-written examples.

Validation sequence:

1. Run one full walkthrough using an externally sourced beginner-style description.
2. Record every missing field, undocumented assumption, missing rule, provenance gap, and unresolved provider fact.
3. Fix concrete failures.
4. Repeat with at least 3–5 independent beginner-style descriptions from people or public posts with no knowledge of the schema.
5. Evaluate extraction quality, clarification burden, final state distribution, and usefulness of the generated architecture brief.

## V1 deferred compatibility testing

Cross-provider compatibility is not solved in V1. Tests may ensure that the system labels compatibility as `DEFERRED`, but must not claim successful compatibility verification.

## Regression rule

Every discovered production-like failure that reveals a missing requirement field, rule, component attribute, precedence behavior, feasibility state, or provenance path must get a regression test and a corresponding source-of-truth documentation update before being considered fixed.
