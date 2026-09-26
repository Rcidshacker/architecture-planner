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

## V1 evaluation semantics (spec-gap resolutions made during the V1 build)

### G-4: condition outcomes

A single-capability condition reads one requirement field and has three outcomes:

| Trigger field | `HARD_REQUIREMENT` output |
|---|---|
| equals the `when` value | the rule's `then` status (`REQUIRED` for `STORAGE-001`) |
| known and different | `NOT_REQUIRED`, provenance = trigger provenance + `RULE` |
| `UNKNOWN` | `UNDETERMINED`, `blocking_unknowns` = the trigger field |

An `INFERRED` trigger counts as a value, but its `INFERENCE` provenance is carried onto the component so it is never presented as user-confirmed. Component provenance is the trigger field's provenance plus `RULE` (e.g. `[USER, RULE]`).

### G-5: `STORAGE-001` spec population

`STORAGE-001`'s spec attributes are copied from the `storage.*` requirement fields (`requirements-schema.md`) when those are known (attribute provenance follows the field, e.g. `USER`); otherwise they stay `UNKNOWN`. This is a copy of a user statement, not a derivation from `file_uploads=true`, so it does not violate the numeric-threshold prohibition. `blocking_unknowns` lists only the attributes still `UNKNOWN`.

Attribute domains (used by provider matching):

| Attribute | Kind | Domain / unit | Requirement field |
|---|---|---|---|
| `access_mode` | enum | `private`, `public` | `storage.access_mode` |
| `delivery` | enum | `signed_url`, `direct` | `storage.delivery` |
| `minimum_capacity` | minimum quantity | GB | `storage.minimum_capacity_gb` |

### G-6: `CACHE-DEFAULT-001` condition

The V1 schema contains no field that expresses an explicit cache requirement, and no V1 rule emits a cache requirement. `no_explicit_cache_requirement` is therefore true for every V1 requirement model, and `cache` is always `NOT_REQUIRED` and listed as a deliberately avoided item. Conceptual grounding (not a provider fact): caching pays off for read-heavy data that is not frequently updated (ByteByteGo, "Things to Consider When Using Cache"); nothing in the V1 schema establishes those properties, so introducing a cache would be unsupported.

### G-7: combining outputs for one component

1. Collect every rule output per component. Iteration order never matters.
2. If `HARD_REQUIREMENT` outputs for one component disagree (e.g. one `REQUIRED`, one `NOT_REQUIRED`), that is an architecture conflict: architecture feasibility is `INFEASIBLE`, the component is `UNDETERMINED`, and both outputs are reported. Precedence is not applied to it.
3. Only when there is no conflict is precedence applied: the output of the strongest category present wins (`HARD_REQUIREMENT` > `PREFERENCE` > `DEFAULT_AVOID`). A `DEFAULT_AVOID` that loses is recorded in the decision's explanation, not silently dropped.

## V1 limitation

This file is intentionally incomplete by design. Additional rules must be added from actual external walkthrough failures or explicitly justified requirements, not from a desire to make the engine appear comprehensive.
