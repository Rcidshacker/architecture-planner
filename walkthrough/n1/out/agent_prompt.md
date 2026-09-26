You are implementing (unnamed application): I'm trying to work out how to structure a database schema that allows me to have multiple authentication sources for the same end-user. For example, my web app would require users to sign in to utilize many of the functionality of features of the app. However, I do not want to be responsible for storing and authenticating user passwords. So I would still need a database table of users, but no column for a password. But I would still need to somehow associate my user with the identity providers user id. For example, if my user signs up with Google, I would store the users Google ID and associate this with my user. Meaning next time the user makes an attempt to login and is successfully authenticated at Google, I would make an attempt to find any user in my system that has this associated user id. The way I imagine it, it would allow me to associated multiple authentication sources for one app user. Meaning once I've signed up with Google, I can go to my settings and associate another account, for example, a Facebook account.


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
