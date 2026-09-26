You are implementing (unnamed application): Upload images to database

I am new i WPF but i make wpf application which have sql database server. My Database is only 20 mb because it's on "appharbor". In this app every user can upload image for avatar but i can't save this pictures for every user because my db is too small. Can you recommend me where to save these images and how to upload their urls in db so every user can see other users avatar picture.If anyone can give me other ideas how to upload images for every user to database tell please me. Also i don't have money to buy host because i am from Bulgaria and i am student 11-th grade. Thank you a lot.


Infrastructure components determined by this plan (do not add other infrastructure without asking the user):
- object_storage [REQUIRED]: access_mode=public, delivery=UNKNOWN, minimum_capacity=UNKNOWN

Provider options (ask the user to choose; do not choose for them):
- Cloudflare R2 (provider FEASIBLE, budget UNVERIFIED)
- Supabase Free (provider UNVERIFIED, budget UNVERIFIED)
- Supabase Pro (provider UNVERIFIED, budget UNVERIFIED)

Rules:
- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that part; never fill it with a default.
- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.
- Do not add: cache (deliberately avoided; no requirement justifies it).

Unresolved items to ask the user about:
- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage.delivery: UNKNOWN
- object_storage.minimum_capacity: UNKNOWN
- budget feasibility: UNVERIFIED
