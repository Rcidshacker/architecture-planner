# requirements-schema.md — Requirement Extraction Model

## Purpose

This document defines the structured information the extraction layer must produce before architecture decisions are made.

The extraction layer may use an LLM, but it is not allowed to invent unknown values.

## Extraction contract

For each relevant field, return:

- value
- state: `KNOWN`, `UNKNOWN`, or `INFERRED`
- provenance: `USER`, `INFERENCE`, or `UNKNOWN`
- optional source text

`RULE` and `PROVIDER_FACT` are not valid provenance for raw user requirements because those arise downstream.

## V1 fields

The initial schema is deliberately small. A field should be added only when it gates a documented architecture decision.

| Field | Required? | Default | Why it exists |
|---|---|---|---|
| `application.name` | optional | unknown | output identity |
| `application.description` | required | none | primary extraction input |
| `capabilities.authentication` | conditional | unknown | auth component decision |
| `capabilities.file_uploads` | conditional | unknown | object storage decision |
| `capabilities.ai_inference` | conditional | unknown | AI provider/processing decisions |
| `capabilities.realtime` | conditional | unknown | realtime transport/coordination decisions |
| `capabilities.payments` | optional | unknown | payment integration decisions |
| `capabilities.search` | optional | unknown | search service decision |
| `capabilities.scheduled_jobs` | optional | unknown | scheduler decision |
| `capabilities.notifications` | optional | unknown | notification workflow decision |
| `capabilities.data_persistence` | conditional | unknown | `DATABASE-001` component decision |
| `workload.users` | required when stated | unknown | scale/cost context |
| `workload.peak_concurrency` | optional | unknown | capacity/scaling decisions |
| `workload.read_write_ratio` | optional | unknown | storage/cache decisions |
| `workload.latency_target_ms` | optional | unknown | performance requirements |
| `workload.request_burstiness` | optional | unknown | capacity/async decisions |
| `operations.ai_request_mode` | conditional | unknown | sync/async decision |
| `operations.ai_request_duration` | conditional | unknown | queue/worker/timeout decisions |
| `operations.user_waits_for_completion` | conditional | unknown | sync/async decision |
| `operations.retryable_background_work` | optional | unknown | queue/retry decisions |
| `operations.public_asset_delivery` | optional | unknown | CDN/delivery decisions |
| `constraints.monthly_budget` | optional | unknown | feasibility/cost |
| `constraints.currency` | conditional | unknown | feasibility/cost |
| `constraints.team_size` | optional | unknown | operational complexity decisions |
| `constraints.provider_lock_in` | optional | unknown | provider strategy |
| `constraints.region_requirements` | optional | unknown | provider eligibility |
| `storage.access_mode` | conditional | unknown | `STORAGE-001` spec attribute `access_mode` |
| `storage.delivery` | conditional | unknown | `STORAGE-001` spec attribute `delivery` |
| `storage.minimum_capacity_gb` | conditional | unknown | `STORAGE-001` spec attribute `minimum_capacity` (unit: GB) |
| `database.minimum_capacity_gb` | conditional | unknown | `DATABASE-001` spec attribute `minimum_capacity` (unit: GB) |

The three `storage.*` fields were added during the V1 build (spec gap G-1): `STORAGE-001` lists `access_mode`, `delivery`, and `minimum_capacity` as blocking unknowns, but no requirement field could ever resolve them, so clarification had nothing to ask and they could only stay `UNKNOWN` forever. Their decision dependency is `STORAGE-001` (see `architecture-rules.md`). Allowed values: `access_mode: private | public`, `delivery: signed_url | direct`, `minimum_capacity_gb: number`.

`capabilities.data_persistence` and `database.minimum_capacity_gb` are V1.1 (spec gap G-18), added from external walkthrough evidence: `WALKTHROUGH.md` e2/e3/e4 are three of five beginner posts whose central need was "where do I store user data?", and V1 had no field or rule that could see it. `database.minimum_capacity_gb` mirrors the `storage.minimum_capacity_gb` pattern exactly — a blocking unknown for `DATABASE-001`, resolved only by clarification, since a capacity number can never be invented from the boolean alone. Decision dependency: `DATABASE-001` (see `architecture-rules.md`). Unlike `storage.*`, no `access_mode`/`delivery`-equivalent attributes are defined: those STORAGE-001 attributes describe file-access semantics with no faithful analog for a database, so V1.1 does not invent one (`architecture-rules.md`'s numeric/attribute-invention prohibition applies to spec surface, not just numbers).

## Explicit prohibition

Do not derive numeric thresholds from a feature boolean unless an explicit rule defines the transformation and gives it provenance.

For example, this is not automatically valid:

`file_uploads=true → minimum_capacity=100 MB`

A number can only be emitted if it comes from a user statement, explicit architecture policy, verified provider fact, or remains `UNKNOWN`.

## Dependency metadata

Every field must specify which decisions it can influence. This powers clarification ranking.

Example:

```yaml
field: operations.ai_request_duration
uncertainty: binary
impact_weight: 4
blocks:
  - queue
  - worker_pool
  - timeout_strategy
  - retry_strategy
```

The schema must not depend on a latent estimate of user knowledge.

### V1 dependency metadata (spec gap G-2)

The docs required metadata for every field but only gave one example. V1 values:

A field **blocks** a decision only if an implemented V1 rule or feasibility dimension consumes it. Fields whose decisions have no implemented V1 rule (queue, worker pool, CDN, auth component, ...) have `blocks: []` and are never asked, because loop step 2 removes fields that do not affect a downstream decision. Their impact weight is recorded for when those rules exist.

| Field | decision_impact | V1 blocks | Relevant when |
|---|---|---|---|
| `capabilities.file_uploads` | 4 | `object_storage` (`STORAGE-001`) | always |
| `storage.access_mode` | 3 | `object_storage.spec.access_mode`, provider | `file_uploads` is not `false` |
| `storage.minimum_capacity_gb` | 3 | `object_storage.spec.minimum_capacity`, provider, budget | `file_uploads` is not `false` |
| `storage.delivery` | 2 | `object_storage.spec.delivery`, provider | `file_uploads` is not `false` |
| `capabilities.data_persistence` | 4 | `relational_database` (`DATABASE-001`) | always |
| `database.minimum_capacity_gb` | 3 | `relational_database.spec.minimum_capacity`, provider, budget | `data_persistence` is not `false` |
| `constraints.monthly_budget` | 3 | budget feasibility | always |
| `constraints.currency` | 3 | budget feasibility | `monthly_budget` is known and non-zero |
| `operations.ai_request_duration` | 4 | none in V1 (queue, worker_pool, timeout_strategy, retry_strategy) | — |
| every other field | 1 | none in V1 | — |

Rationale: `file_uploads` decides whether a component exists at all (architecture-blocking). `access_mode` and `minimum_capacity_gb` can each disqualify a seeded provider plan (a plan capped at 1 GB, a plan without public buckets). `delivery` is `2` because every seeded object-storage provider supports both values, so it rarely changes a provider outcome.

Rules used by the clarification loop (`decision-resolution.md`):

- A **blocking unknown** is a relevant, unresolved field with `decision_impact >= 3`.
- Ties in priority are broken by the row order of this table (deterministic, no hidden estimate).

### Extraction anti-invention checks (spec gap G-3)

The extraction layer enforces, mechanically, after the LLM responds:

1. A `KNOWN` or `INFERRED` value must carry `source_text` that appears verbatim (case- and whitespace-insensitive) in the description. Otherwise the value is discarded, the field is set `UNKNOWN`, and an extraction issue is recorded and shown in review.
1a. A `source_text` that is empty or whitespace-only does not count as a quote (code review fix).
1b. A `KNOWN` numeric value must appear in its own quote (digits compared after removing thousands separators, e.g. `1500` matches "₹1,500"). A quote that does not contain the number is treated as no quote, so a number like "10k" is discarded rather than interpreted.
2. Numeric fields (`workload.users`, `workload.peak_concurrency`, `workload.latency_target_ms`, `constraints.monthly_budget`, `constraints.team_size`, `storage.minimum_capacity_gb`, `database.minimum_capacity_gb`) may not be `INFERRED` (see Explicit prohibition). An inferred number is discarded the same way.
3. A field entry that does not validate (wrong type, unknown enum value, `RULE`/`PROVIDER_FACT` provenance, state/provenance mismatch) is rejected: the field is set `UNKNOWN` and an extraction issue names it for correction in review. Nothing is guessed in its place.
4. A response that is not a JSON object at all is an extraction error; no requirement model is produced.

Every surviving value keeps the provenance the extractor assigned (`USER` for `KNOWN`, `INFERENCE` for `INFERRED`, `UNKNOWN` for `UNKNOWN`); these pairings are enforced by the data contract.
