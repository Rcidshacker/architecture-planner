You are implementing (unnamed application): For a web app that allows simple image uploads, how should I store the images? Confused about file system vs. cdn

Every search result says something about storing the images in the file system but store the paths in the database, but I'm not sure exactly what "file system" means. Would that mean you have something like: /public (assets) /js /css /img /app (frontend) /server (backend) and you'd upload directly to that /public/img directory? I remember trying something like that in the past with a Node.js app hosted on Heroku, and it wouldn't let me. I had to set up Amazon S3 and upload the images THERE, which leads to my confusion. Is using something like Amazon S3 the usual practice or do people upload directly to the /img directory (assuming this is the "file system"?) and it just happened to be the case that Heroku doesn't allow this but other hosts do?


Infrastructure components determined by this plan (do not add other infrastructure without asking the user):
- object_storage [REQUIRED]: access_mode=UNKNOWN, delivery=UNKNOWN, minimum_capacity=UNKNOWN

Provider options (ask the user to choose; do not choose for them):
- Cloudflare R2 (provider FEASIBLE, budget UNVERIFIED)
- Supabase Free (provider UNVERIFIED, budget UNVERIFIED)
- Supabase Pro (provider UNVERIFIED, budget UNVERIFIED)

Rules:
- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that part; never fill it with a default.
- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.
- Do not add: cache (deliberately avoided; no requirement justifies it).

Unresolved items to ask the user about:
- object_storage.access_mode: UNKNOWN
- object_storage.delivery: UNKNOWN
- object_storage.minimum_capacity: UNKNOWN
- budget feasibility: UNVERIFIED
