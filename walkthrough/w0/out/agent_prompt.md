You are implementing ResumeForge: ResumeForge: job seekers sign in with Google, upload their resume as a PDF and paste a job description, and an LLM rewrites the resume to fit the job. They download the tailored PDF a minute later. Around 200 users at launch, maybe 20 at the same time. I want to keep hosting under $10 a month.

Infrastructure components determined by this plan (do not add other infrastructure without asking the user):
- object_storage [REQUIRED]: access_mode=private, delivery=UNKNOWN, minimum_capacity=2.0

Provider options (ask the user to choose; do not choose for them):
- Cloudflare R2 (provider FEASIBLE, budget UNVERIFIED)
- Supabase Pro (provider UNVERIFIED, budget INFEASIBLE)

Rules:
- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that part; never fill it with a default.
- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.
- Do not add: cache (deliberately avoided; no requirement justifies it).

Unresolved items to ask the user about:
- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- capabilities.ai_inference=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage.delivery: UNKNOWN
- budget feasibility: UNVERIFIED
