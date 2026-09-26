# ARCHITECTURE.md — System Design

## System boundary

The product is a decision-support system that transforms application requirements into an auditable architecture model and maps that model to currently verified provider capabilities.

## Logical layers

```text
User
  ↓
Application Description
  ↓
Requirement Extraction
  ↓
Human Requirement Review
  ↓
Requirement Model
  ↓
Architecture Rule Engine
  ↓
Abstract Component Requirements
  ↓
Provider Knowledge / Mapping
  ↓
Feasibility Analysis
  ↓
Architecture Resolution
  ↓
Architecture Brief / Diagram / Agent Instructions
```

## Responsibilities

### Requirement extraction
Converts natural-language descriptions into the structured requirement model. This layer may use an LLM.

It must preserve provenance and uncertainty rather than fabricate missing fields.

V1 LLM backend (decided with the project author during the V1 build): the `claude` CLI invoked as a subprocess (`claude -p`), using the author's existing login. The extractor depends only on a `prompt -> text` callable, so tests use a fake and the backend is swappable. The LLM's output is untrusted input: it is validated against the requirement model and the anti-invention checks in `requirements-schema.md` before anything downstream sees it.

### Human requirement review
Presents extracted requirements in a human-readable form via the CLI. The user can accept, correct, or complete values before architecture rules execute. This is a terminal-based review surface for V1; it is not a web UI.

### Requirement model
Stores capabilities, workload characteristics, constraints, operational requirements, and provenance.

### Architecture rule engine
Maps requirements to abstract infrastructure components. V1 supports single-capability rules only.

The rule engine must not directly select commercial providers.

### Abstract component specification
Describes not only that a component is required, but what capabilities the component must provide.

Example shape:

```yaml
component: object_storage
status: REQUIRED
spec:
  access_mode: private
  delivery: signed_url
  minimum_capacity: UNKNOWN
provenance:
  - USER
  - RULE
```

Numeric thresholds must not be invented. They require explicit rule provenance, provider facts, or remain `UNKNOWN`.

### Provider knowledge layer
Stores current provider capabilities, constraints, pricing facts, and source metadata.

Provider information must include:

- provider
- service
- capability/fact
- source URL
- retrieved timestamp
- verified timestamp
- evidence/status

For V1, provider facts are manually seeded (see `docs/PRD.md` build sequence) — hand-entered records for a small number of providers relevant to the walkthrough examples. Trawl is the planned upstream source for provider documentation and structured provider facts once the reasoning engine is validated; it is not a V1 dependency.

### Provider mapping
Matches abstract component specifications to concrete provider services.

Provider mapping is not equivalent to feasibility. A provider can partially match a component and still leave the overall architecture unresolved.

### Feasibility engine
Evaluates:

1. Architecture feasibility.
2. Provider feasibility.
3. Budget feasibility.
4. Compatibility feasibility is explicitly deferred in V1.

Provider feasibility must support bundled offerings. It must evaluate candidate provider configurations rather than simply summing independent minimum prices per abstract component.

### Decision resolution
Applies feasibility checks before precedence semantics. Precedence cannot turn an infeasible set of constraints into a feasible architecture.

### Output generation
All outputs must derive from one resolved architecture model. The diagram, written explanation, and coding-agent prompt must not independently invent architecture.

## Data flow

```text
Natural language
    ↓
Extraction result
    ↓
Requirement review
    ↓
Confirmed requirements
    ↓
Rules
    ↓
Component requirements
    ↓
Provider candidates
    ↓
Feasibility states
    ↓
Resolved / partial architecture
    ↓
Presentation formats
```

## Project layout

```text
project/
├── CLAUDE.md
├── pyproject.toml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PRD.md
│   ├── SCHEMA.md
│   ├── TESTING.md
│   ├── requirements-schema.md
│   ├── architecture-rules.md
│   └── decision-resolution.md
├── src/
│   └── architect/
│       ├── __init__.py
│       ├── cli.py            # entrypoint; human review surface for V1
│       ├── extraction/       # natural language -> requirement model
│       ├── requirements/     # requirement model + provenance types (Pydantic)
│       ├── rules/            # rule engine + rule definitions
│       ├── providers/        # provider fact schema; manually seeded for V1
│       ├── feasibility/      # architecture / provider / budget dimensions
│       ├── clarification/    # question ranking + stopping loop
│       ├── resolution.py     # rules + feasibility -> one ArchitectureModel / ResolvedPlan
│       └── output/           # architecture brief, diagram data, agent prompt (rendered from ResolvedPlan)
└── tests/
    ├── unit/
    └── integration/
```

The stack is Python (see `CLAUDE.md`). Do not change this layout without updating this document first.

## Architectural invariants

- Requirement extraction and architecture decision-making are separate responsibilities.
- Provider mapping and architecture synthesis are separate responsibilities.
- The user can inspect what was extracted before it becomes architectural input.
- Unknown provider facts do not become verified facts through LLM fallback.
- Feasibility is not inferred from the existence of a polished final diagram.
- V1 does not claim cross-provider compatibility verification.
