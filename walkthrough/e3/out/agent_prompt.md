You are implementing (unnamed application): Database for a server application

I want to start an android project for a module at university and I plan to make an online application that will communicate with a server. The app will have to record the user's log-in details and other information regarding their progress with the app on a database hosted on the server. My idea is to set up a database on my raspberry pi which will act as a web server. The only problem is that I have limited experience with databases and I was wondering what will be the best one to use. I have only used Oracle and it was very tedious to set it up, especially on Linux. From a lot of googling I reached the conclusion that MySQL will be the best choice. SQLite looks good too because it's easy to use, but I heard that it doesn't cope so well with concurrency. What do you guys think? More info: The app will be a project for uni so it won't have huge amounts of data (but I plan to make it available on the store if I receive good feedback) The database will have to work properly when data is requested simultaneously by multiple users this will be a server application can handle crashes


Infrastructure components determined by this plan (do not add other infrastructure without asking the user):
- object_storage [UNDETERMINED]: access_mode=UNKNOWN, delivery=UNKNOWN, minimum_capacity=UNKNOWN

Rules:
- Any value marked UNKNOWN or UNDETERMINED is unresolved: ask the user before implementing that part; never fill it with a default.
- Cross-provider compatibility is DEFERRED (unverified); verify integrations yourself before relying on them.
- Do not add: cache (deliberately avoided; no requirement justifies it).

Unresolved items to ask the user about:
- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage: UNDETERMINED (blocked by capabilities.file_uploads)
- provider feasibility: UNVERIFIED
- budget feasibility: UNVERIFIED
