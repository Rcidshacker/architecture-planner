You are implementing Bicycle Management application: I am currently learning WPF (C#) and trying to build a small Bicycle Management application for practice. I understand the basics individually (WPF controls, simple classes, MySQL connections, etc.), but I am struggling to understand how these pieces should be connected together in a clean beginner-friendly structure. The application currently has these requirements: a Bicycle class with properties such as Brand, Type, Price and Color; temporarily storing them in a List or ObservableCollection; connecting to a MySQL database. I already have a working MySQL connection and basic INSERT / SELECT queries, but I am unsure where this logic should ideally be placed in a beginner WPF application. My main problem is understanding the overall structure of the application and how these concepts are usually connected together. Is Code-Behind acceptable for window navigation in a beginner project? I mainly want to understand how a simple WPF application with multiple windows and database CRUD operations should be organized while learning.


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
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- relational_database.minimum_capacity: UNKNOWN
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
