# SCHEMA.md — Data Contracts

This document defines the conceptual contracts. Implement these as Pydantic v2 models in `src/architect/` per `ARCHITECTURE.md`.

## Provenance

Every value that can influence an architecture decision must carry provenance when it is not self-evident from the containing record.

Allowed provenance values:

- `USER`
- `RULE`
- `PROVIDER_FACT`
- `INFERENCE`
- `UNKNOWN`

A value must never be presented as verified when its provenance is `INFERENCE` or `UNKNOWN`.

## Requirement value

```yaml
value: <typed value or null>
state: KNOWN | UNKNOWN | INFERRED
provenance: USER | RULE | INFERENCE | UNKNOWN
confidence: optional implementation field
source_text: optional excerpt/reference to original user statement
```

## Requirement model

The exact field set is intentionally constrained to fields that have a downstream decision purpose. New fields require a documented rule or decision dependency.

### Application

```yaml
application:
  name: string
  description: string
```

### Capabilities

```yaml
capabilities:
  authentication: boolean | UNKNOWN
  file_uploads: boolean | UNKNOWN
  ai_inference: boolean | UNKNOWN
  realtime: boolean | UNKNOWN
  payments: boolean | UNKNOWN
  search: boolean | UNKNOWN
  scheduled_jobs: boolean | UNKNOWN
  notifications: boolean | UNKNOWN
```

### Workload

```yaml
workload:
  users: number | UNKNOWN
  peak_concurrency: number | UNKNOWN
  read_write_ratio: object | UNKNOWN
  latency_target_ms: number | UNKNOWN
  request_burstiness: low | medium | high | UNKNOWN
```

### Operation characteristics

```yaml
operations:
  ai_request_mode: synchronous | asynchronous | mixed | UNKNOWN
  ai_request_duration: fast | seconds | minutes | UNKNOWN
  user_waits_for_completion: boolean | UNKNOWN
  retryable_background_work: boolean | UNKNOWN
  public_asset_delivery: boolean | UNKNOWN
```

### Constraints

```yaml
constraints:
  monthly_budget: number | UNKNOWN
  currency: string | UNKNOWN
  team_size: number | UNKNOWN
  provider_lock_in: low | medium | high | UNKNOWN
  region_requirements: string[] | UNKNOWN
```

### Storage (added in the V1 build, see `requirements-schema.md` G-1)

```yaml
storage:
  access_mode: private | public | UNKNOWN
  delivery: signed_url | direct | UNKNOWN
  minimum_capacity_gb: number | UNKNOWN
```

### Review status (spec gap G-13)

```yaml
confirmed: boolean   # false after extraction; true only after human review confirms
```

Every field above is stored as a requirement value (value/state/provenance). State and provenance must pair: `KNOWN` ↔ `USER` or `RULE`, `INFERRED` ↔ `INFERENCE`, `UNKNOWN` ↔ `UNKNOWN` with a null value. The rule engine refuses a model with `confirmed: false`. Every numeric requirement value must be finite and non-negative (no `NaN`, `Infinity`, or negative budgets/capacities/counts), whether it comes from extraction, review, or clarification.

The presence of a field does not mean that the system may infer it without evidence.

## Requirement-to-decision dependency

Each schema field must identify which downstream decisions it can affect. This is required for clarification-question ranking.

Example:

```yaml
field: operations.ai_request_duration
decision_impact:
  - queue
  - worker_pool
  - timeout_strategy
  - retry_strategy
priority_weight: 4
```

`priority_weight` must be statically defined in the schema or rule metadata. It must not depend on an unmeasured estimate of user knowledge.

## Component requirement

```yaml
component: string
status: REQUIRED | RECOMMENDED | OPTIONAL | NOT_REQUIRED | UNDETERMINED
spec: {}
provenance: []
rules_triggered: []
blocking_unknowns: []
```

A component name alone is insufficient for provider feasibility.

## Component specification

Component specifications contain provider-checkable attributes.

Example:

```yaml
component: object_storage
spec:
  access_mode: private | public | UNKNOWN
  delivery: signed_url | direct | UNKNOWN
  minimum_capacity: number | UNKNOWN
  expected_read_volume: UNKNOWN
  expected_write_volume: UNKNOWN
```

This is a schema example, not a claim that those values are automatically derivable from `file_uploads=true`.

## Provider fact

```yaml
provider: string
service: string
fact_type: capability | limitation | pricing | free_tier | region | integration
key: string
value: <typed value>
source_url: string
retrieved_at: datetime
verified_at: datetime
verification_status: VERIFIED | STALE | UNKNOWN
```

For V1, provider facts are manually entered records, not scraped. `source_url` and the timestamps are still required — manual entry does not exempt a fact from carrying evidence.

## Provider bundle

Bundles are first-class because one provider configuration can satisfy multiple component requirements.

```yaml
provider_bundle:
  provider: string
  services: []
  included_capabilities: []
  cost_model: {}
  constraints: []
  evidence: []
```

V1 concrete shapes (spec gap G-14):

- `evidence` is the list of provider facts backing the bundle. `included_capabilities` and `cost_model` are derived from `evidence`, never asserted independently; a bundle whose declared capability or cost has no backing fact fails validation.
- Fact key conventions: `component.<component>` (capability, `true`), `<component>.<attribute>.<value>` (capability, boolean: whether that enum value is supported; one fact per value so each carries its own source), `object_storage.max_capacity_gb` (limitation, number or `"unlimited"`, only when the source states it), and pricing facts `currency`, `fixed_monthly`, `usage_priced`.
- Seed data lives in `src/architect/providers/seed_facts.json` (inside the package so it ships with the build); every fact is hand-entered from the cited page. A limit the source does not state is left out (it becomes missing evidence), never filled from general knowledge.
- `cost_model: {currency: string, fixed_monthly: number, usage_priced: boolean}`.
- A bundle is one plan of one provider (e.g. Supabase Free and Supabase Pro are separate bundles), because limits and prices differ per plan.
- Component `spec` values are scalars or the literal `UNKNOWN`.

## Feasibility result

```yaml
feasibility:
  architecture: FEASIBLE | INFEASIBLE | UNVERIFIED
  provider: FEASIBLE | INFEASIBLE | UNVERIFIED
  budget: FEASIBLE | INFEASIBLE | UNVERIFIED
  compatibility: DEFERRED
  explanations: []
  conflicts: []
  missing_evidence: []
```

## Clarification question

```yaml
question:
  field: string
  prompt: string
  decision_impact: 1 | 2 | 3 | 4
  uncertainty: 0 | 1
  priority: number
  blocking_decisions: []
```

V1 priority is derived from:

`priority = uncertainty × decision_impact`

## Architecture model

```yaml
architecture:
  components: []
  provider_candidates: []
  feasibility: {}
  decisions: []
  unresolved_items: []
  avoided_items: []
  scaling_triggers: []
```

Every decision must reference the relevant requirement, rule, provider fact, inference, or unknown state.
