# architecture-rules.md — V1 Architecture Rules

## Rule-system scope

V1 supports single-capability rules only.

A rule may inspect one principal capability/condition and produce one or more abstract component requirements plus their provider-checkable attributes.

Multi-capability interaction rules are deferred.

## Rule semantics

Every rule must declare:

- ID
- condition
- component output
- component status
- component specification
- rule category
- provenance
- conflict behavior
- blocking unknowns

## Rule categories

- `HARD_REQUIREMENT`: a component is required when its condition is satisfied.
- `PREFERENCE`: a simpler or cheaper architecture is preferred when requirements remain satisfied.
- `DEFAULT_AVOID`: do not introduce a component without evidence.

Direct user constraints are represented in the requirement model and feasibility layer, not as architecture rules that override feasibility.

## Example rule: file uploads

```yaml
id: STORAGE-001
category: HARD_REQUIREMENT
when:
  capabilities.file_uploads: true
then:
  component: object_storage
  status: REQUIRED
  spec:
    access_mode: UNKNOWN
    delivery: UNKNOWN
    minimum_capacity: UNKNOWN
  provenance:
    component: RULE
    spec: UNKNOWN
conflicts: []
blocking_unknowns:
  - access_mode
  - delivery
  - minimum_capacity
```

This deliberately does not invent numeric capacity or delivery semantics from `file_uploads=true` alone.

## Example rule: Redis avoidance

```yaml
id: CACHE-DEFAULT-001
category: DEFAULT_AVOID
when:
  no_explicit_cache_requirement: true
then:
  component: cache
  status: NOT_REQUIRED
```

This default cannot override a hard requirement established by another rule. If a stronger architecture requirement appears, feasibility and conflict semantics determine the next state; rule iteration order must never determine behavior.

## Example rule: shared coordination

A concrete Redis requirement should not be emitted until the schema contains an explicit signal for shared state/coordination and the V1 rule is written.

The rule should then specify the coordination capabilities required rather than hard-coding a provider.

## Component-spec requirement

A component output is incomplete if it contains only:

```text
component = object_storage
```

It must contain the provider-checkable attributes required for a provider match, even when some attributes remain `UNKNOWN`.

## Numeric attributes

The rule engine must not create arbitrary numbers. If a rule introduces a numeric threshold, the rule must include:

- threshold
- unit
- rationale
- provenance
- applicability

Until such a rule exists, the value remains `UNKNOWN`.

## Rule precedence

Rule precedence is not a substitute for feasibility.

The system must first identify whether the requirement set is feasible. Only after feasibility is established should precedence be used to choose among competing feasible architectural alternatives.

Default/avoid behavior is weaker than explicit architectural requirements.

Direct contradictions between user constraints and hard architectural requirements produce `INFEASIBLE`; neither side silently wins.

## V1 limitation

This file is intentionally incomplete by design. Additional rules must be added from actual external walkthrough failures or explicitly justified requirements, not from a desire to make the engine appear comprehensive.
