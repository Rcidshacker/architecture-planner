# Architecture Brief: (unnamed application)

## Application summary

Database for a server application

I want to start an android project for a module at university and I plan to make an online application that will communicate with a server. The app will have to record the user's log-in details and other information regarding their progress with the app on a database hosted on the server. My idea is to set up a database on my raspberry pi which will act as a web server. The only problem is that I have limited experience with databases and I was wondering what will be the best one to use. I have only used Oracle and it was very tedious to set it up, especially on Linux. From a lot of googling I reached the conclusion that MySQL will be the best choice. SQLite looks good too because it's easy to use, but I heard that it doesn't cope so well with concurrency. What do you guys think? More info: The app will be a project for uni so it won't have huge amounts of data (but I plan to make it available on the store if I receive good feedback) The database will have to work properly when data is requested simultaneously by multiple users this will be a server application can handle crashes


## Confirmed requirements (stated by the user)

- `capabilities.authentication` = true (USER) — "The app will have to record the user's log-in details"
- `capabilities.data_persistence` = true (USER) — "record the user's log-in details and other information regarding their progress with the app on a database hosted on the server"

## Assumptions and provenance (INFERRED — not verified)

- none

## Abstract architecture

| Component | Status | Spec | Provenance | Rules |
|---|---|---|---|---|
| cache | NOT_REQUIRED | — | RULE | CACHE-DEFAULT-001 |
| object_storage | UNDETERMINED | access_mode=UNKNOWN, delivery=UNKNOWN, minimum_capacity=UNKNOWN | UNKNOWN, RULE | STORAGE-001 |
| relational_database | REQUIRED | minimum_capacity=UNKNOWN | USER, RULE, UNKNOWN | DATABASE-001 |

## Provider options (from seeded, sourced facts; the tool does not pick one)

- Supabase Free: provider UNVERIFIED, budget UNVERIFIED (0.0 USD/month fixed; monthly budget is unknown)
- Supabase Pro: provider UNVERIFIED, budget UNVERIFIED (25.0 USD/month fixed; monthly budget is unknown)
- Compatibility between providers: DEFERRED (not verified in V1)

## Feasibility

- architecture: FEASIBLE
- provider: UNVERIFIED
- budget: UNVERIFIED
- compatibility: DEFERRED
- provider: relational_database: seeded offerings lack the verified facts needed to confirm the spec {'minimum_capacity': 'UNKNOWN'}
- budget: no configuration can be verified within budget

## Unresolved / UNDETERMINED decisions

- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- relational_database.minimum_capacity: UNKNOWN
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
- compatibility: DEFERRED (cross-provider integration is not verified in V1)
- clarification stopped after 2 round(s): blocking_unknowns_already_asked

## Scaling triggers

- none: no documented scaling rule exists in V1

## Items deliberately avoided

- cache: NOT_REQUIRED (default-avoid rule; no requirement justifies it)

## Major decisions

- **cache** → NOT_REQUIRED [RULE; CACHE-DEFAULT-001]: NOT_REQUIRED per CACHE-DEFAULT-001
- **object_storage** → UNDETERMINED [UNKNOWN, RULE; STORAGE-001]: UNDETERMINED per STORAGE-001; blocked by capabilities.file_uploads
- **relational_database** → REQUIRED [USER, RULE, UNKNOWN; DATABASE-001]: REQUIRED per DATABASE-001; blocked by minimum_capacity
- **feasibility.architecture** → FEASIBLE [RULE; architecture-rules.md G-7]: no rule conflicts
- **feasibility.provider** → UNVERIFIED [PROVIDER_FACT; seeded provider facts]: provider: relational_database: seeded offerings lack the verified facts needed to confirm the spec {'minimum_capacity': 'UNKNOWN'}
- **feasibility.budget** → UNVERIFIED [UNKNOWN, PROVIDER_FACT; constraints.monthly_budget, constraints.currency, seeded pricing facts]: budget: no configuration can be verified within budget
- **feasibility.compatibility** → DEFERRED [UNKNOWN; decision-resolution.md: compatibility deferred in V1]: cross-provider compatibility is not verified in V1

## Architecture diagram

```mermaid
flowchart LR
  application["(unnamed application)"]
  object_storage["object_storage (UNDETERMINED)<br/>no verified provider"]
  relational_database["relational_database (REQUIRED)<br/>Supabase Free, Supabase Pro"]
  application -.-> object_storage
  application --> relational_database
```

## Implementation instructions for your coding agent

You are implementing (unnamed application): Database for a server application

I want to start an android project for a module at university and I plan to make an online application that will communicate with a server. The app will have to record the user's log-in details and other information regarding their progress with the app on a database hosted on the server. My idea is to set up a database on my raspberry pi which will act as a web server. The only problem is that I have limited experience with databases and I was wondering what will be the best one to use. I have only used Oracle and it was very tedious to set it up, especially on Linux. From a lot of googling I reached the conclusion that MySQL will be the best choice. SQLite looks good too because it's easy to use, but I heard that it doesn't cope so well with concurrency. What do you guys think? More info: The app will be a project for uni so it won't have huge amounts of data (but I plan to make it available on the store if I receive good feedback) The database will have to work properly when data is requested simultaneously by multiple users this will be a server application can handle crashes


Infrastructure components determined by this plan (do not add other infrastructure without asking the user):
- object_storage [UNDETERMINED]: access_mode=UNKNOWN, delivery=UNKNOWN, minimum_capacity=UNKNOWN
- relational_database [REQUIRED]: minimum_capacity=UNKNOWN

Provider options (ask the user to choose; do not choose for them):
- Supabase Free (provider UNVERIFIED, budget UNVERIFIED)
- Supabase Pro (provider UNVERIFIED, budget UNVERIFIED)

Rules:
- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that part; never fill it with a default.
- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.
- Do not add: cache (deliberately avoided; no requirement justifies it).

Unresolved items to ask the user about:
- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- relational_database.minimum_capacity: UNKNOWN
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
