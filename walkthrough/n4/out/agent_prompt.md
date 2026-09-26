You are implementing (unnamed application): I'm just starting to learn about mobile development, backend setup etc. I'm trying to create an Android app in Kotlin that uses one of OpenAI's language models. OpenAI's documentation says that for production apps, all API calls should be routed through a backend server, where the key can be set as an environment variable, to avoid exposing the API key in the app's code. I'm planning to use one of the pre-build backend services such AWS, Back4App or Firebase to store the necessary data for my app. However I'm not sure how to use those, if it is even possible, to route API requests from the app to OpenAI, that is what scripts would I have to run on the server, how to modify the code making the request in the app etc.


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
- capabilities.ai_inference=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- relational_database.minimum_capacity: UNKNOWN
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
