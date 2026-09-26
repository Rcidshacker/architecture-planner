You are implementing (unnamed application): I want to build a web application for my friend's business that includes a booking system and an online payment feature. However, I'm feeling overwhelmed about how to properly plan and start the project. Specifically, I'm unsure about: How to break down the project into components (frontend, backend, database, etc.). How to design and organize API endpoints for booking and payments. What the typical workflow should look like (user booking, payment, confirmation, etc.). Best practices for structuring the application as a beginner. Basic secure coding practices I should follow, especially for handling payments and user data. I'm not asking for a full solution, but rather guidance on how to approach the planning phase and structure the development process properly.


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
- capabilities.payments=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- relational_database.minimum_capacity: UNKNOWN
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
