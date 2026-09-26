You are implementing (unnamed application): Want to build application like Skype or Whatsapp

I want to build an application on android platform with the features of video call and text messages over Internet, similar of VOIP which has video streaming function. Can any one help what are the requirements to build this project and where to start with? I have came up with many online solution which ask me to register to this sites and after that I can build an application using there source code and libraries but I have to pay a lot for using their service. I manage to build the protocol of this project to run on the local network using socket connection. Now I want to make it work for over Internet but their are many obstacles. First is the NAT which block my socket connection to particular ports. So I thing I have to use some this else other then Socket connection but I don't know what should I go for. Another is I tried to work on Openfire server which allows me to register users and maintains the user data on server sideand build client app which can handle chat and file transfer but cannot perform video call function. I want to build an application on android device which will allow user to login and chat/videocall/file transfer with the people who are added in their contact list. Thank you for reading my query I hope you understand my requirements, please do reply if you have any experience or idea for how should this project be build and what are the requirements.


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
- capabilities.authentication=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- capabilities.realtime=true: no V1 architecture rule; infrastructure for it is not determined by this tool
- object_storage.access_mode: UNKNOWN
- object_storage.delivery: UNKNOWN
- object_storage.minimum_capacity: UNKNOWN
- budget feasibility: UNVERIFIED
