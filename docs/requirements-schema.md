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
