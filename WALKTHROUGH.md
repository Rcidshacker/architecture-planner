# V1 Walkthrough Log (PRD.md build step 9)

Each run uses the real `claude -p` extractor and the hand-seeded provider facts. Artifacts are in `walkthrough/<id>/`
(`extracted.json` where kept, `requirements.json` after review/clarification, `out/` = brief, diagram data, agent
prompt, plan).

Metric definitions:

- **Extraction completeness**: fields KNOWN / INFERRED / UNKNOWN out of 29 requirement fields right after extraction (27
  original + 2 added by V1.1: `capabilities.data_persistence`, `database.minimum_capacity_gb`).
- **Invented/unsupported values**: values the extractor kept that the description does not support (manual audit of
  every non-UNKNOWN field against its quote), plus values the extractor refused (`extraction issue` lines).
- **Blocking unknowns**: open fields with `decision_impact >= 3` before clarification.

## w0: author walkthrough (ResumeForge)

Description (written by the builder, not externally sourced):

> ResumeForge: job seekers sign in with Google, upload their resume as a PDF and paste a job description, and an LLM
> rewrites the resume to fit the job. They download the tailored PDF a minute later. Around 200 users at launch, maybe
> 20 at the same time. I want to keep hosting under $10 a month.

| Metric | Result |
|---|---|
| Extraction completeness | 7 KNOWN, 2 INFERRED (`ai_request_duration=minutes` from "a minute later", `currency=USD` from "$10"), 18 UNKNOWN |
| Extraction issues (refused values) | 0 |
| Invented/unsupported values kept | 0: every kept value quotes the description; both inferences are labelled INFERRED |
| Review edits | `constraints.currency=USD` (author confirmed the inferred currency, now KNOWN/USER) |
| Blocking unknowns before clarification | 2 (`storage.access_mode`, `storage.minimum_capacity_gb`) |
| Clarification rounds | 1 (both asked together, priority 3); answers `private`, `2` GB; stop: `no_blocking_unknowns` |
| Final feasibility | architecture FEASIBLE, provider FEASIBLE, budget UNVERIFIED, compatibility DEFERRED |
| Unresolved components | 0 UNDETERMINED; `object_storage.delivery` UNKNOWN (impact 2, never asked) |
| Useful brief? | Partly. Object storage + Cloudflare R2 option is correct and sourced; Supabase Pro is correctly shown over budget. Auth and LLM calls are outside V1's rule set (see failures). |

Failures found and fixed (each with a regression test and a doc update, per TESTING.md):

1. **Capabilities without a V1 rule vanished** (`authentication`, `ai_inference`), and the agent prompt said "add no
   other infrastructure", which would have told a coding agent not to build login or LLM calls. Fixed: listed as
   unresolved "no V1 architecture rule" items; the prompt says to ask the user. Doc: `decision-resolution.md` G-15.
   Tests: `test_known_capability_without_a_v1_rule_is_surfaced_not_dropped`.
2. **Excluded offering unexplained**: Supabase Free was dropped (2 GB > its verified 1 GB cap) with no reason given.
   Fixed: the violated attribute and limit are now in the feasibility explanations. Doc: G-16. Test:
   `test_excluded_offering_is_explained`.
3. **Budget decision provenance omitted the currency's provenance** (an INFERRED currency could look user-stated).
   Fixed. Doc: G-16. Test: `test_budget_decision_provenance_includes_inferred_currency`.

Observations recorded, not changed (no walkthrough evidence yet that they need a rule):

- Budget stays UNVERIFIED for any usage-priced provider (R2) because V1 has no usage forecast; R2's 10 GB free tier
  would cover 2 GB of storage, but operation counts are unknown, so UNVERIFIED is the honest state.
- `operations.ai_request_duration=minutes` gates queue/worker decisions that have no V1 rule, so nothing uses it.
- Re-running `plan` on an already-clarified file reports 0 rounds; the round count is per run, not cumulative.

## External beginner descriptions (e1-e5)

Source: five Stack Overflow questions (CC BY-SA) written by beginners who had never seen this schema. Reddit was the
first choice but returns HTTP 403 to every fetcher. Each question's title and body were used verbatim
(`walkthrough/eN/description.txt`, URL and author in `source.txt`). The authors are not available to answer
questions, so, as agreed with the project author: extraction was confirmed without edits and every clarification
question was answered "don't know". That is the worst case. It measures clarification burden and how much stays
UNDETERMINED.

| | Source | Gist |
|---|---|---|
| e1 | [SO 32342260](https://stackoverflow.com/questions/32342260) | web app with simple image uploads; S3 vs file system confusion |
| e2 | [SO 30748431](https://stackoverflow.com/questions/30748431) | Android app, many users + profiles, cheap-to-start scalable DB |
| e3 | [SO 21470018](https://stackoverflow.com/questions/21470018) | university Android app, login + progress, DB on a Raspberry Pi, concurrency |
| e4 | [SO 21500165](https://stackoverflow.com/questions/21500165) | student WPF app, avatar uploads, 20 MB DB, "don't have money" |
| e5 | [SO 46934583](https://stackoverflow.com/questions/46934583) | Android chat + video call + file transfer between contacts |

| Metric | e1 | e2 | e3 | e4 | e5 |
|---|---|---|---|---|---|
| Extraction K / I / U (of 27) | 1 / 0 / 26 | 0 / 1 / 26 | 1 / 0 / 26 | 1 / 3 / 23 | 1 / 2 / 24 |
| Extraction issues (refused values) | 0 | 0 | 0 | 0 | 0 |
| Invented / unsupported values kept | 0 | 0 (1 weak inference) | 0 | 0 (1 weak inference) | 0 |
| Invented numbers | 0 | 0 | 0 | 0 | 0 |
| Blocking unknowns before clarification | 3 | 4 | 4 | 2 | 3 |
| Clarification rounds / questions | 1 / 3 | 2 / 4 | 2 / 4 | 1 / 2 | 1 / 3 |
| Stop reason | already asked | already asked | already asked | already asked | already asked |
| Feasibility A / P / B / C | F / F / U / D | F / U / U / D | F / U / U / D | F / F / U / D | F / F / U / D |
| UNDETERMINED components | 0 | 1 (object_storage) | 1 (object_storage) | 0 | 0 |
| Unresolved items (excl. compatibility) | 4 | 2 | 2 | 4 | 6 |
| Useful brief? | partly | no | no | partly | barely |

(F = FEASIBLE, U = UNVERIFIED, D = DEFERRED. e2/e3 feasibility shown after the G-17 fix below.)

Values kept, all quoting the description: e1 `file_uploads` (KNOWN); e2 `authentication` (INFERRED from "store huge
number of users and there profile information", a weak inference); e3 `authentication` (KNOWN, "record the user's
log-in details"); e4 `file_uploads` (KNOWN), `authentication` (INFERRED from avatar uploads, a weak inference),
`public_asset_delivery` and `storage.access_mode=public` (INFERRED, "every user can see other users avatar"); e5
`authentication` (KNOWN), `file_uploads` and `realtime` (INFERRED, arguably stated outright, so the extractor was
conservative here).

### Failures found and fixed

4. **Vacuous FEASIBLE with an UNDETERMINED component (e2, e3).** No component was REQUIRED, so provider and budget
   were reported FEASIBLE, budget included, even though the budget was unknown and object storage was undetermined.
   That is a confident claim with no support. Fixed: an UNDETERMINED component makes provider/budget UNVERIFIED.
   Doc: `decision-resolution.md` G-9 (G-17 note). Test: `test_undetermined_component_blocks_a_feasible_claim`.
5. **CLI failure detail lost.** `claude -p` exited 1 transiently on e3-e5 with an empty stderr; the error message
   dropped stdout, where the CLI reports its reason. Fixed in `extraction/llm.py`. Re-running succeeded. No
   regression test: the transient cause could not be reproduced on demand.

### Findings recorded, NOT implemented (need a product decision per CLAUDE.md rule discipline)

- **Missing capability: persistent data / database (e2, e3, e4).** The central need in three of five posts is "where
  do I store user data?", but the V1 schema has no persistence field and no rule, so the tool cannot see it.
  These three posts are the walkthrough evidence CLAUDE.md requires for a new rule (e.g. a `capabilities.data_persistence`
  field plus a `DATABASE-001` rule). Recommended as the first V1.1 rule.
  **Update (V1.1): built.** See "V1.1: DATABASE-001" below — `capabilities.data_persistence` and `DATABASE-001` exist
  now, using exactly this field name and rule shape. e2/e3/e4 rerun and confirmed fixed.
- **Capabilities without rules dominate unresolved output.** `authentication` (4/5) and `realtime` (e5) are now
  surfaced (G-15), but the brief can only say "not determined by this tool" for them.
- **Budget phrases without numbers.** e4's "I don't have money to buy host" stayed UNKNOWN. That is correct under the
  no-invented-numbers rule, but it cost a clarification question. A rule mapping explicit "no money/free only"
  statements to budget 0 would need its own documented transformation.
- **Low extraction coverage is honest, not a bug.** Beginner posts state 1-4 of 27 fields. The extractor refused
  nothing and invented nothing; most fields stay UNKNOWN because the posts are about infrastructure confusion, not
  requirements.

### What the walkthrough says about next design changes (PRD step 9)

- No evidence yet for a UI, Trawl integration, or a learned classifier. The bottleneck is **rule coverage**
  (persistence, auth, realtime), not extraction quality or provider data freshness.
- Clarification burden stayed small (2-4 questions, at most 2 rounds). The 3-round cap never bound.

## V1.1: `DATABASE-001` added (spec gap G-18)

Added `capabilities.data_persistence` (requirement field) and `DATABASE-001` (rule, component `relational_database`)
per the walkthrough finding above, on the user's explicit "build minimal now" decision. Mirrors `STORAGE-001`
exactly: one condition, one component, one spec attribute (`minimum_capacity`, GB) copied from a requirement field,
never derived from the boolean. No engine-type (relational vs document) or other attribute was added — `STORAGE-001`
has no equivalent for one, so V1.1 does not invent one either (`architecture-rules.md`, `requirements-schema.md`
G-18). Provider evidence: two new hand-seeded facts, `relational_database.max_capacity_gb` = 0.5 (Supabase Free)
and 8 (Supabase Pro), both freshly fetched from <https://supabase.com/pricing> (not carried over from the original
seeding pass), reusing the `component.relational_database` capability fact the original build session had already
seeded on both Supabase bundles but that no rule had ever consumed until now.

e2, e3, and e4 — the three posts that found the original gap — were rerun end-to-end with the real `claude -p`
extractor, confirmed as-is (no edits, matching the original run's methodology), and every clarification question
again answered "don't know" (artifacts in `walkthrough/eN/v1.1/`, mirroring the original `walkthrough/eN/` layout).

| | e2 | e3 | e4 |
|---|---|---|---|
| `data_persistence` extracted | KNOWN/USER, "store huge number of users and there profile information" | KNOWN/USER, "record the user's log-in details and other information regarding their progress with the app on a database hosted on the server" | KNOWN/USER, "wpf application which have sql database server" |
| `relational_database` status | **REQUIRED** (was invisible before V1.1) | **REQUIRED** (was invisible before V1.1) | **REQUIRED** (was invisible before V1.1) |
| Feasibility A / P / B / C | F / U / U / D | F / U / U / D | F / U / U / D |
| Clarification rounds | 2 | 2 | 1 |
| Unresolved items | 5 | 6 | 7 |

(F = FEASIBLE, U = UNVERIFIED, D = DEFERRED.) Provider stays `UNVERIFIED`, not `FEASIBLE`, in all three: none of the
posts states a database size, "don't know" is the answer to the capacity clarification question, and Supabase's
seeded capacity facts are not `"unlimited"`, so the honest state is unverified, not a guess in either direction —
exactly `decision-resolution.md`'s definition of `UNVERIFIED`. The fix is that `relational_database` is now visible
and `REQUIRED` at all; it was completely absent from every V1 output before this change.

e4 is a real unit-conversion regression case worth naming: its source text states "My Database is only 20 mb", and
the mechanical anti-invention check (`requirements-schema.md` G-3 rule 1b) correctly refuses a `0.02` GB value for
that quote, since "0.02" does not appear in "20 mb" — the number itself must come from the user, not from the tool
converting units on their behalf. `database.minimum_capacity_gb` stays `UNKNOWN` for e4, same as e2/e3.

No new bugs found in this rerun. Existing failures 1-5 stay fixed (auth/ai_inference surfaced, excluded-offering
explanations, undetermined-component feasibility, budget provenance, CLI error text).

## Round 2: auth / ai_inference / payments evidence probe (n1-n5)

**Hypothesis** (stated before sourcing any post, per the scientific-method discipline this probe used): independent,
schema-blind beginner descriptions need `authentication` and/or `ai_inference` infrastructure decisions often enough
to clear the same evidentiary bar `data_persistence` cleared for V1.1 (3/5 posts, round 1). **What would falsify it**:
fewer than roughly half of a fresh, independently sourced 3-5 post sample state or clearly imply one of these two
capabilities. This round does not build anything regardless of the result — per CLAUDE.md, a new rule needs its own
walkthrough evidence and an explicit product decision; this probe only gathers the evidence.

Source: five Stack Overflow questions (CC BY-SA 4.0), independent of e1-e5, none written for this project. Reddit
was tried again first (via a search API rather than direct fetch) and several genuine beginner auth threads were
found, but every candidate's page fetch returned HTTP 403 (`old.reddit.com` and `www.reddit.com` both), same
blocker as round 1 — Stack Overflow was used again as the fallback. Selection targeted posts plausibly touching
login/accounts or AI features (the two fields under test), while still being genuine unprompted questions, not
written to order; one MySQL-only post with neither was kept deliberately as a persistence-rule regression control.

| | Source | Gist |
|---|---|---|
| n1 | [SO 48249206](https://stackoverflow.com/questions/48249206/database-structure-for-multiple-authentication-sources-of-users-in-a-web-app) | web app, multi-provider (Google/Facebook) login, no local password storage |
| n2 | [SO 79911319](https://stackoverflow.com/questions/79911319/how-should-i-plan-and-structure-a-web-app-with-booking-and-payment-features-as-a) | booking + online payment feature for a friend's business |
| n3 | [SO 76416674](https://stackoverflow.com/questions/76416674/welcome-message-in-python-chatbot-using-gradio-and-openai-api) | Python/Gradio chatbot using the OpenAI API |
| n4 | [SO 76698818](https://stackoverflow.com/questions/76698818/routing-openai-api-requests-from-an-android-app-thorough-a-backend-server) | Android app calling an OpenAI language model through a backend |
| n5 | [SO 79945015](https://stackoverflow.com/questions/79945015/how-should-i-structure-a-beginner-wpf-bicycle-class-app-with-multiple-windows) | WPF practice app, MySQL CRUD — no auth/AI (persistence-rule control) |

Real pipeline, no simulation: `architect extract` (`claude -p`) → `architect review` (confirmed as-is, no edits,
same methodology as round 1) → `architect plan` (every clarification answered `?`/don't-know). Artifacts in
`walkthrough/n{1-5}/`.

| Metric | n1 | n2 | n3 | n4 | n5 |
|---|---|---|---|---|---|
| Extraction K / I / U (of 29) | 2 / 0 / 27 | 1 / 1 / 27 | 1 / 1 / 27 | 2 / 0 / 27 | 2 / 0 / 27 |
| Extraction issues (refused values) | 0 | 0 | 0 | 0 | 0 |
| Invented / unsupported values kept | 0 | 0 | 0 | 0 | 0 |
| Blocking unknowns before clarification | 4 | 4 | 5 | 4 | 4 |
| Clarification rounds | 2 | 2 | 2 | 2 | 2 |
| Stop reason | already asked | already asked | already asked | already asked | already asked |
| Feasibility A / P / B / C | F / U / U / D | F / U / U / D | F / U / U / D | F / U / U / D | F / U / U / D |
| Unresolved items (excl. compatibility) | 5 | 5 | 5 | 5 | 4 |
| Useful brief? | partly | partly | partly | partly | yes |

(F = FEASIBLE, U = UNVERIFIED, D = DEFERRED.)

Values kept, all quoting the description, manually audited against source text (0 invented): n1
`authentication` (KNOWN, "my web app would require users to sign in to utilize many of the functionality of
features of the app"), `data_persistence` (KNOWN, "I would still need a database table of users"); n2 `payments`
(KNOWN, "an online payment feature"), `data_persistence` (INFERRED, "a booking system" — a booking system implies
stored bookings, correctly not claimed KNOWN); n3 `ai_inference` (KNOWN, "the OpenAI API for a simple chatbot"),
`operations.user_waits_for_completion` (INFERRED, "a simple chatbot"); n4 `ai_inference` (KNOWN, "uses one of
OpenAI's language models"), `data_persistence` (KNOWN, "to store the necessary data for my app"); n5
`application.name`="Bicycle Management application" and `data_persistence` (KNOWN, "connecting to a MySQL
database").

### Auth / ai_inference / payments tally

| Post | `authentication` | `ai_inference` | `payments` | Downstream, with no V1 rule |
|---|---|---|---|---|
| n1 | true (KNOWN) | — | — | Surfaced: "no V1 architecture rule; infrastructure for it is not determined by this tool" — in the brief's Unresolved section, Major decisions, and the agent prompt's "ask the user about" list |
| n2 | — | — | true (KNOWN) | Same surfacing, for `payments` |
| n3 | — | true (KNOWN) | — | Same surfacing, for `ai_inference` |
| n4 | — | true (KNOWN) | — | Same surfacing, for `ai_inference` |
| n5 | — | — | — | N/A — no ruleless capability fired |

`authentication` fired in 1/5, `ai_inference` in 2/5, and — not part of the original hypothesis, found along the
way — `payments` in 1/5. All four ruleless-capability firings (auth ×1, ai_inference ×2, payments ×1) were
**correctly surfaced, not silently dropped**: the G-15 fix (round 1) holds in every new case checked directly
against each generated `architecture_brief.md` and `agent_prompt.md`, not just against a summary. No case implied
"add no other infrastructure" the way the pre-G-15 bug did.

### Findings recorded, NOT implemented (evidence only, per CLAUDE.md rule discipline)

- **`authentication`, `ai_inference`, and `payments` all have real, ruleless demand**, but at lower and more even
  frequency than `data_persistence` had (3/5) in round 1: `ai_inference` 2/5, `authentication` 1/5, `payments` 1/5,
  no single field crossing the 3/5 bar alone. Combined, 4 of 5 posts here hit at least one ruleless capability,
  which is a real gap, but the hypothesis as stated (either field individually matching round 1's bar) is **not
  confirmed** by this sample.
- **Small-sample sensitivity**: n=5 with 3 different ruleless fields under watch is a thin sample per field (1-2
  hits each). A single differently-sourced post could change any per-field count by a third. This round's honest
  read is "real signal, not yet at round-1's evidentiary bar for any one field" — not "no signal."
- **`object_storage` stays UNDETERMINED in all 5**, including n5 which never mentions files at all — this is
  existing, documented behavior (any HARD_REQUIREMENT rule whose triggering capability is UNKNOWN, not `false`,
  leaves the component UNDETERMINED rather than NOT_REQUIRED; matches e2/e3's identical pattern from round 1), not
  a new finding.
- **Doc staleness fixed as part of this round**: `WALKTHROUGH.md`'s field-count metric said "27" but V1.1 added 2
  fields (`capabilities.data_persistence`, `database.minimum_capacity_gb`), making it 29 — corrected above. This
  is a documentation accuracy fix, not a code change.

### Verdict

Honest read of the data, not a recommendation to act on it: **not yet** for a same-bar `AUTH-001` or `AI-001` — no
single field reached round 1's 3/5 threshold in this sample. But `authentication`, `ai_inference`, and `payments`
combined account for real, ruleless demand in 4 of 5 fresh posts, so the next evidence-gathering step (a larger
or differently sourced sample, or tracking these three fields across future rounds rather than treating this as
closed) seems more justified than treating the absence of a single 3/5 field as "no gap." That's a product
decision, not one this probe makes.
