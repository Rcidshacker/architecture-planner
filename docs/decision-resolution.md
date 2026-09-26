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

## V1 implementation semantics (spec-gap resolutions made during the V1 build)

### G-8: architecture feasibility

- `INFEASIBLE` when hard rule outputs for one component conflict (`architecture-rules.md` G-7).
- `FEASIBLE` otherwise. `UNDETERMINED` components do not make the architecture infeasible in principle; they are reported as unresolved items. `UNVERIFIED` is not used for this dimension in V1 because no V1 rule depends on external evidence.

### G-9: provider matching

Only `REQUIRED` components are mapped to providers. Each spec attribute is checked against the provider's facts and yields `SATISFIED`, `VIOLATED`, or `UNVERIFIED`:

- Only facts with `verification_status: VERIFIED` count. A `STALE` or `UNKNOWN` fact is treated as missing evidence and is reported in `missing_evidence`; it is never shown as current verification. Staleness is taken from `verification_status`; V1 does not invent an age threshold.
- Enum attribute, known value `v`: `SATISFIED` if the verified fact `<component>.<attribute>.v` is `true`, `VIOLATED` if it is `false`, `UNVERIFIED` if there is no verified fact.
- Enum attribute, `UNKNOWN` value: evaluate every value in the attribute's domain as above. `SATISFIED` only if all are satisfied (whatever the user later answers, the provider fits); `UNVERIFIED` otherwise. It is never `VIOLATED`, because the user may still choose a supported value. This is how an `UNKNOWN` spec can still be matched without inventing a value.
- Minimum-quantity attribute (`minimum_capacity`, GB) against the provider's `max_capacity_gb` fact (`"unlimited"` or a number): unlimited → `SATISFIED`; known requirement ≤ cap → `SATISFIED`; known requirement > cap → `VIOLATED`; unknown requirement with a finite cap → `UNVERIFIED`.
- A bundle matches a component only if it has a verified `component.<name>` capability fact. If that fact exists but is `STALE`/`UNKNOWN`, the bundle is an `UNVERIFIED` candidate and the stale fact is listed in `missing_evidence` (it can therefore never be silently ignored while other offerings make the component look `INFEASIBLE`). A bundle's match for a component is `VIOLATED` if any attribute is violated, else `UNVERIFIED` if any is unverified, else `SATISFIED`.

Per `REQUIRED` component: `FEASIBLE` if some bundle `SATISFIED` it; `INFEASIBLE` if at least one seeded bundle offers the component and every such bundle is `VIOLATED`; otherwise `UNVERIFIED` (including when no seeded bundle offers it — absence from a hand-seeded corpus is missing evidence, not proof of impossibility). `INFEASIBLE` explanations always say "among seeded providers".

The provider dimension is the worst component state (`INFEASIBLE` > `UNVERIFIED` > `FEASIBLE`). With no `REQUIRED` components it is `FEASIBLE` with the explanation "no REQUIRED provider-backed components" only when no component is `UNDETERMINED`. If any component is `UNDETERMINED`, provider and budget are `UNVERIFIED` ("cannot evaluate while <components> are UNDETERMINED"): an undetermined component may still need a paid provider, so claiming feasibility would be unsupported (walkthrough e2/e3 regression, G-17).

### G-10: configurations and budget

- A **configuration** is a set of bundles in which every `REQUIRED` component is covered by a bundle whose match is not `VIOLATED`. Configurations are enumerated by choosing one covering bundle per component and de-duplicating by bundle set, keeping the assignment with the most `SATISFIED` matches; a bundle covering several components appears once and its cost is counted once (bundle-aware — never a sum of per-component minima).
- A bundle's cost model comes from its verified pricing facts: `currency`, `fixed_monthly` (the minimum charge regardless of usage), `usage_priced` (whether cost grows with usage). V1 has no usage forecast, so the usage-priced portion is never estimated.
- Per configuration, against `constraints.monthly_budget`:
  - budget `UNKNOWN` → `UNVERIFIED`.
  - any bundle lacks verified pricing facts → `UNVERIFIED`.
  - currency codes are compared case-insensitively; a bundle's pricing currency differs from the budget currency (or the budget currency is `UNKNOWN`) and the budget is non-zero → `UNVERIFIED` (V1 has no verified exchange-rate fact). A budget of `0` compares in any currency.
  - total `fixed_monthly` > budget → over budget (certain).
  - total `fixed_monthly` ≤ budget and some bundle is `usage_priced` → `UNVERIFIED` (usage unknown).
  - total `fixed_monthly` ≤ budget and nothing is usage-priced → within budget.
  - a configuration containing an `UNVERIFIED` component match can at best be `UNVERIFIED`.
- Budget dimension: `FEASIBLE` if some configuration is within budget and fully `SATISFIED`; `INFEASIBLE` if at least one configuration exists and every configuration is certainly over budget (the budget-versus-hard-requirement conflict); otherwise `UNVERIFIED`. If the provider dimension is `INFEASIBLE`, no configuration exists and budget is `UNVERIFIED` (the provider conflict is the reported cause). With no `REQUIRED` components, budget is `FEASIBLE` with that explanation.
- `INFEASIBLE` never removes or downgrades a `REQUIRED` component; the conflict and each configuration's fixed cost are reported as the tradeoff.

### G-11: precedence among feasible alternatives

V1 has no `PREFERENCE` rules, so there is no documented basis for ranking provider configurations. All feasible and `UNVERIFIED` configurations are listed as options, in seed-file order, with their states. The tool does not pick one.

### G-12: clarification loop mechanics

- Candidate questions are fields that are unresolved (`UNKNOWN`), relevant (their `Relevant when` condition in `requirements-schema.md` holds), have a non-empty V1 `blocks` list, and have not already been asked.
- The loop runs a round only while at least one candidate is a blocking unknown (`decision_impact >= 3`), fewer than 3 rounds have run, and no feasibility dimension is `INFEASIBLE`. Non-blocking candidates therefore never trigger a round on their own.
- Each round asks every candidate that shares the highest priority value (ties grouped, ordered by metadata row order).
- An answer of "don't know" leaves the field `UNKNOWN` with provenance `UNKNOWN`; the field is not asked again. A given answer is stored `KNOWN` / `USER`.
- The stop reason is recorded: `no_blocking_unknowns`, `max_rounds`, `infeasible`, or `blocking_unknowns_already_asked` (blocking unknowns remain, but the user already answered "don't know" to each).
- Whatever remains unresolved after the loop stays `UNKNOWN`, its components stay `UNDETERMINED` or keep `UNKNOWN` spec attributes, and all of it is listed in the brief's unresolved section.

### G-15: capabilities with no V1 rule (walkthrough 0 regression)

A capability that is known `true` (e.g. `authentication`, `ai_inference`) but has no implemented V1 rule produces no component. It must not disappear silently: each one is listed in `unresolved_items` as `capabilities.<name>=true: no V1 architecture rule; infrastructure for it is not determined by this tool`, and the agent prompt tells the agent to ask the user how to implement it instead of forbidding or inventing infrastructure. No component, status, or provider is emitted for it.

### G-16: explaining excluded provider offerings

When a bundle offers a component but is verified not to meet its spec (`VIOLATED`), the violated attribute and limit are added to the feasibility explanations so the brief says why that offering is not an option.

The budget decision's provenance includes the provenance of both `constraints.monthly_budget` and `constraints.currency`.

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
