# decision-resolution.md — Decision Semantics

## Purpose

This document defines how the architecture planner handles uncertainty, conflicts, feasibility, provider evidence, clarification questions, and stopping conditions.

## Decision states

### Component state

- `REQUIRED`
- `RECOMMENDED`
- `OPTIONAL`
- `NOT_REQUIRED`
- `UNDETERMINED`

### Feasibility state

- `FEASIBLE`
- `INFEASIBLE`
- `UNVERIFIED`
- `DEFERRED`

## Resolution pipeline

```text
Requirement extraction
        ↓
Human confirmation
        ↓
Rule evaluation
        ↓
Component specifications
        ↓
Candidate provider configurations
        ↓
Feasibility analysis
        ↓
Precedence among feasible alternatives
        ↓
Architecture model
```

## Feasibility comes before precedence

Precedence must not be used to resolve an infeasible constraint set.

Example:

```text
User constraint: monthly budget = ₹0
Hard requirement: file uploads
Rule outcome: object storage required
Provider evidence: paid or otherwise non-zero-cost options only
```

Result:

```text
INFEASIBLE
```

The system must explain the conflict and show tradeoffs. It must not silently drop the storage requirement or silently violate the budget.

## Feasibility dimensions

### Architecture

Can the abstract architecture satisfy the confirmed requirements in principle?

Allowed states:

- `FEASIBLE`
- `INFEASIBLE`
- `UNVERIFIED`

### Provider

Can the abstract component specifications be mapped to current, verified provider offerings?

Allowed states:

- `FEASIBLE`
- `INFEASIBLE`
- `UNVERIFIED`

`UNVERIFIED` means the corpus lacks sufficient current evidence. It is not equivalent to either success or failure.

### Budget

Can a valid provider configuration satisfy the user's budget constraint using verified cost information?

Allowed states:

- `FEASIBLE`
- `INFEASIBLE`
- `UNVERIFIED`

### Compatibility

Cross-provider compatibility is explicitly deferred in V1.

State:

- `DEFERRED`

The product must not imply that a collection of individually verified services is an integration-verified system.

## Provider bundles

Feasibility must be evaluated against provider configurations and bundles, not by independently summing the minimum cost of every abstract component.

A candidate configuration can satisfy multiple component requirements through a bundled offering.

Example concept:

```text
Required components:
- relational database
- authentication
- object storage

Candidate A:
Supabase bundle covers all three.

Candidate B:
Database provider + separate auth + separate object storage.
```

Both configurations must be considered before declaring budget infeasibility.

## Unknown and unverified behavior

`UNDETERMINED` means the application requirements do not provide enough information to determine a component decision.

`UNVERIFIED` means the architecture requirement is known, but current provider evidence is insufficient to make a concrete provider claim.

Do not convert either state into a confident recommendation solely to complete generation.

## Precedence semantics

Precedence applies only when multiple feasible rules or architecture preferences provide competing valid alternatives.

Semantic hierarchy:

1. Hard architectural requirements.
2. Explicit architecture preferences.
3. Default/avoid rules.

User constraints participate in feasibility rather than simply overriding hard requirements.

If user constraints contradict hard requirements, emit `INFEASIBLE`.

## Clarification question priority

V1 uses a fully computable priority function:

```text
priority = uncertainty × decision_impact
```

`uncertainty` is binary in V1:

- `0` = known
- `1` = unresolved

`decision_impact` is statically assigned in the schema/rule metadata:

- `1` = low
- `2` = moderate
- `3` = high
- `4` = architecture-blocking

No hidden estimate of user knowledge is used.

## Clarification loop

Maximum rounds: `3` in V1.

Each round:

1. Identify unresolved fields.
2. Remove fields that no longer affect a downstream decision.
3. Rank remaining fields using `uncertainty × decision_impact`.
4. Ask the highest-priority question(s).
5. Update the requirement model.
6. Re-run decisions and feasibility.

## Stopping conditions

Stop before the maximum when:

- no blocking unknowns remain, or
- remaining unknowns do not prevent a useful architecture.

After three rounds:

- do not keep asking automatically.
- generate a partial/qualified architecture where possible.
- label unresolved areas as `UNDETERMINED`.
- preserve the unknowns in the final brief.

If feasibility is `INFEASIBLE`, stop treating clarification as the mechanism for silently resolving the conflict. Instead, expose the conflict and its available tradeoffs.

## Provenance discipline

Every consequential value or decision must be attributable to one of:

- `USER`
- `RULE`
- `PROVIDER_FACT`
- `INFERENCE`
- `UNKNOWN`

If no provenance can be assigned, the value remains `UNKNOWN`.

## Deferred items

The following are deliberately not solved in V1:

- multi-capability interaction rules
- cross-provider compatibility verification
- arbitrary architecture synthesis outside the documented rule/component vocabulary
- repository implementation drift detection
- a web UI (CLI only for V1)
- any learned/ML classification component in the decision path
- live provider-documentation scraping (Trawl integration)

These are scope boundaries, not implicit assumptions that they already work.
