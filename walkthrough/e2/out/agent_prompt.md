You are implementing (unnamed application): Creating a scalable database for android app | cloud hosted

I am working to launch an app which in future will store huge number of users and there profile information. But I Wanted to start small to pre-test my app idea , so what will be the options for hosting database which are cost effective initially and scalable in future , and easy to integrate too. Many thanks for your inputs


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
