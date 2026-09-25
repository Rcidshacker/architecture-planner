# PRD.md — Architecture Planner V1

## Product statement

Build a provider-aware architecture planning tool for developers who can build applications with AI coding agents but need help converting an application idea into a practical, explainable, and evidence-grounded system architecture.

The tool is not primarily a system-design quiz. The core product is a traceable reasoning workflow from application requirements to infrastructure decisions.

## Target user

V1 targets individual developers and early-stage builders who can describe what they want to build but may not know how to translate requirements into infrastructure choices.

The first validation users should be people similar to the project author: developers building small SaaS, AI/LLM, and CRUD-heavy applications.

## Core workflow

1. User describes an application in natural language.
2. The system extracts structured requirements.
3. The user reviews and edits the extracted requirements.
4. The decision engine applies V1 architecture rules.
5. The system identifies unresolved decision blockers.
6. The clarification loop asks only high-impact missing questions.
7. Feasibility is evaluated across architecture, provider, and budget dimensions. Cross-provider compatibility is explicitly deferred in V1.
8. The system produces an architecture model.
9. The architecture model generates an architecture brief, diagram data, and implementation instructions/prompts.

## Product principles

### Traceability
Every important architecture decision must be explainable through an explicit rule, user requirement, provider fact, inference, or unknown state.

### Honesty over completeness
A partial but correctly qualified architecture is preferable to an apparently complete architecture containing invented assumptions.

### Human confirmation
The extracted requirement model must be reviewed before architecture decisions are finalized.

### Provider separation
The architecture engine operates on abstract component requirements. Provider mapping is a separate layer using current, sourced provider facts.

### Simplicity first
Infrastructure should be introduced only when a requirement or explicit architecture rule justifies it. This principle applies to the product being built and to the tool's own implementation: do not add components (a UI, a learned classifier, a live scraping integration) before the reasoning engine has been validated to need them.

## V1 scope

### In scope

- Natural-language application description.
- Structured requirement extraction.
- Human-readable requirement review/editing (CLI).
- Requirement provenance.
- Base capabilities and workload/constraint fields defined in `requirements-schema.md`.
- Single-capability architecture rules.
- Abstract component requirements with attribute-level specifications.
- Explicit rule evidence.
- `REQUIRED`, `RECOMMENDED`, `OPTIONAL`, `NOT_REQUIRED`, and `UNDETERMINED` component states.
- Manually seeded provider facts with verification metadata.
- Provider feasibility states including `FEASIBLE`, `INFEASIBLE`, and `UNVERIFIED`.
- Bundle-aware provider feasibility.
- Budget feasibility analysis using verified pricing/facts where available.
- Explicit `INFEASIBLE` handling for conflicting requirements and constraints.
- Clarification-question prioritization based on computable decision impact and uncertainty.
- Maximum clarification rounds.
- Architecture brief generation.
- Diagram data generation.
- AI coding-agent implementation prompt generation.
- Provenance in the final output.

### Explicitly out of scope for V1

- A web UI. The human review step is CLI-based until the reasoning engine is validated.
- A learned/ML classification model in the decision path. Any such addition requires a walkthrough-evidenced need first.
- Live provider-documentation scraping (Trawl integration). V1 uses manually seeded provider facts.
- Repository-wide architecture inference.
- Architecture drift detection.
- Automatic codebase remediation.
- Arbitrary multi-capability interaction rules.
- Cross-provider compatibility verification.
- Full production cost forecasting under arbitrary traffic curves.
- Automatic deployment.
- Autonomous infrastructure provisioning.
- Treating system-design interview MCQs as the main product workflow.

## Build sequence (V1)

Work in this order. Do not start a step until the previous step's verification passes.

1. **Data contracts.** Implement the Pydantic models for the requirement model, component requirement, provider fact, and feasibility result per `SCHEMA.md`.
   Verify: example YAML shapes from `SCHEMA.md` round-trip into typed objects without validation errors.

2. **Requirement extraction.** LLM-backed extraction into the requirement model, tagging each field `KNOWN` / `UNKNOWN` / `INFERRED` with provenance.
   Verify: a hand-written test description produces correctly tagged output, and no field is silently invented.

3. **CLI human review.** Terminal surface to display extracted requirements and accept edits.
   Verify: an edited value is persisted with `provenance: USER`, overwriting the extraction result.

4. **Rule engine.** Load and evaluate the two seeded rules in `architecture-rules.md` (`STORAGE-001`, `CACHE-DEFAULT-001`).
   Verify: the rule-engine test cases in `TESTING.md` pass.

5. **Provider fact store (manual).** Hand-enter provider facts for a small set of providers relevant to the walkthrough (e.g., one object-storage provider, one database provider).
   Verify: a manually entered fact can satisfy `STORAGE-001`'s component spec.

6. **Feasibility engine.** Architecture, provider, and budget dimensions; compatibility hardcoded to `DEFERRED`.
   Verify: the six required feasibility cases in `TESTING.md` pass, including the bundle case and the `INFEASIBLE` case.

7. **Clarification loop.** Priority ranking (`uncertainty × decision_impact`), 3-round cap, stopping conditions.
   Verify: on a synthetic requirement set with multiple unresolved fields, the highest-impact field is asked first and the loop stops per the documented conditions.

8. **Output generation.** Architecture brief, diagram data, and coding-agent prompt, all derived from one resolved architecture model.
   Verify: all three outputs trace back to the same model; no output contains architecture content absent from the model.

9. **Walkthrough validation.** Run one complete end-to-end walkthrough (the author's own application description), then 3–5 independent externally sourced beginner-style descriptions, per the Success criteria below.
   Trawl integration, a web UI, and any learned classification component remain out of scope until this step's results say otherwise.

## V1 decision states

Requirement states:

- `KNOWN`
- `UNKNOWN`
- `INFERRED`

Component states:

- `REQUIRED`
- `RECOMMENDED`
- `OPTIONAL`
- `NOT_REQUIRED`
- `UNDETERMINED`

Feasibility states:

- `FEASIBLE`
- `INFEASIBLE`
- `UNVERIFIED`
- `DEFERRED`

New states must not be added casually. Update `SCHEMA.md` and `decision-resolution.md` first.

## Clarification workflow

The system may ask clarification questions when an unresolved field materially affects downstream architecture decisions.

Priority is based on computable properties only:

`question_priority = uncertainty × decision_impact`

The system does not use an unmeasured assumption such as whether the user is likely to know the answer.

V1 uses a maximum of three clarification rounds. If blocking unknowns remain after the limit, the system generates a qualified architecture with explicit `UNDETERMINED` sections unless the state is `INFEASIBLE`.

## Output

The primary output is an Architecture Brief containing:

- application summary
- confirmed requirements
- assumptions and provenance
- abstract architecture
- concrete provider options where verified
- feasibility states
- unresolved/undetermined decisions
- scaling triggers where a documented rule exists
- items deliberately avoided
- explanation of major decisions
- architecture diagram representation
- implementation instructions for the user's selected coding agent

## Success criteria for V1 validation

Do not define success from a single happy-path example.

Run at least one complete end-to-end walkthrough first. Then test 3–5 independent beginner-style descriptions written without knowledge of the requirement schema.

For each description record:

- extraction completeness
- number of clarification rounds
- number of blocking unknowns
- number of invented/unsupported values encountered
- final feasibility states
- number of unresolved components
- whether a useful architecture brief can be generated

The walkthrough results, not assumptions about them, determine the next design changes — including whether Trawl integration, a UI, or any learned classification component is actually justified.

## Business model placeholder

Pricing is deliberately not a V1 architecture dependency. Candidate models include project credits and recurring team/agency features. Do not encode pricing assumptions into the reasoning engine.
