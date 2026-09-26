# Gates: Architecture Planner V1

OWNS: src/**, tests/**, docs/**, pyproject.toml, uv.lock, GATES.md, WALKTHROUGH.md, .python-version

Scope: PRD.md 9-step V1 build, each step's Verify line proven by its own test module, plus full quality gates, walkthrough log, anti-pattern pass and code review.

- [x] G0: every spec gap hit during the build is documented in docs/ before code relies on it (G-1..G-14 at start)
  EVIDENCE: docs updated before code: requirements-schema G-1..G-3, architecture-rules G-4..G-7, decision-resolution G-8..G-12 + G-15/G-16/G-17 (walkthrough regressions), SCHEMA G-13/G-14, ARCHITECTURE LLM backend + layout

- [x] G1: step 1 data contracts - SCHEMA.md YAML shapes round-trip into typed objects without validation errors
  CHECK: uv run pytest tests/unit/test_contracts.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=a2da1836c4f8026ca59c612136c48f574f0d642fb58fb38536888721a53bbd89; exit=0; EXPECT=matched; output-sha256=f6eb0cf76b0f186f01f5c994f7c4b1903b0c6bfeb59fd24c6d878a31e4ca87ea; output-bytes=339; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G2: step 2 extraction - hand-written description yields correctly tagged fields, nothing invented (fake LLM)
  CHECK: uv run pytest tests/unit/test_extraction.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=0e4500cdda43591953b2f6222ca0e279e45a2fce976e64b24b42635aa1ad9104; exit=0; EXPECT=matched; output-sha256=c7664d6feee996500129967df17221eb5bd4f702b7242d49473dd9b70561bc47; output-bytes=249; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G2L: step 2 extraction against the real claude CLI on the hand-written description
  CHECK: uv run pytest -m integration tests/integration/test_extraction_live.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=a9b15a44db53c4951187d3e1660e80f37997b26fade507cd2b6fd773b3df472f; exit=0; EXPECT=matched; output-sha256=f6c27cd122dfcf757173fdaac0350d5d141b4f0a52f7decf7b2d61af4bce8a37; output-bytes=150; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G3: step 3 CLI review - edited value persists with provenance USER; unconfirmed model rejected by rules
  CHECK: uv run pytest tests/unit/test_review.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=432fe7a1848cbc11792899b08037939ee575b5d2664f45e739a0d124b1de84ff; exit=0; EXPECT=matched; output-sha256=43cb72827e2e3493f4cdc3568659f7ae18509ca3850f4da8ad6491c10becda76; output-bytes=231; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G4: step 4 rule engine - TESTING.md rule-engine cases pass
  CHECK: uv run pytest tests/unit/test_rules.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=6c723a73a45bacd39bb3e4a68f525fab9b30f03ed0d5817e62c2a603c7801ec9; exit=0; EXPECT=matched; output-sha256=c7664d6feee996500129967df17221eb5bd4f702b7242d49473dd9b70561bc47; output-bytes=249; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G5: step 5 provider store - a seeded, sourced fact satisfies STORAGE-001's spec
  CHECK: uv run pytest tests/unit/test_providers.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=a1fe5d8387657cfaed803512f83db3e09795f63eb0ecc12c6801aadbbf866b84; exit=0; EXPECT=matched; output-sha256=ea4494dc7b0ceba4fcaf89ea3f8c6f8e19f255e77419a73c3a8515a1caa5bfa4; output-bytes=231; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G6: step 6 feasibility - six TESTING.md cases incl. bundle and INFEASIBLE, plus conflict-resolution cases
  CHECK: uv run pytest tests/unit/test_feasibility.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=32b4389bb372f1f5a2cd5714a78769f57a6be42e694e2c5cf5db90688d013e27; exit=0; EXPECT=matched; output-sha256=46518109505f0f3bfe85be94690f9223f0169750ddc15dc2dbaa9277b1f6297d; output-bytes=303; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G7: step 7 clarification - highest-impact field asked first, loop stops per documented conditions
  CHECK: uv run pytest tests/unit/test_clarification.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=4d8523d90382e24e488bba3b32b1ac4fdf7efb53fca8e14328a65d4ebc0ab1da; exit=0; EXPECT=matched; output-sha256=bf79cad455643fe97b01b5c2d265872cc9dd99dc220a5bef67e248a872485e34; output-bytes=240; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G8: step 8 outputs - brief, diagram data, agent prompt all trace to one model, nothing extra
  CHECK: uv run pytest tests/unit/test_output.py -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=f0e1ffdbecb9ea8cc334cfc76ef0685b77d4d27b4bebf342828bd232b9c1caa6; exit=0; EXPECT=matched; output-sha256=48618a1e133499db193dfba583d14459d67d3df369fd06dbf7b68e59fc412aef; output-bytes=240; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G9: step 9a author walkthrough run end-to-end with real LLM and logged in WALKTHROUGH.md
  EVIDENCE: WALKTHROUGH.md w0: real claude -p extraction, review, 1 clarification round, 0 invented values; 3 failures fixed with regression tests (G-15, G-16)

- [x] G10: step 9b 3-5 externally sourced beginner descriptions run and logged with the PRD metrics
  EVIDENCE: WALKTHROUGH.md e1-e5: 5 Stack Overflow beginner posts (URLs logged), all PRD metrics recorded; 0 invented numbers; failures 4-5 fixed (G-17, CLI stdout); DB-rule gap recorded not built

- [x] G11: full unit suite green
  CHECK: uv run pytest -q
  EXPECT: /\d+ passed/
  EVIDENCE: automatic-evidence=v1; definition-sha256=dde1b3fff49d825f5d394b33bab6a6223f9ddce8b78bce67d9433e8a397f852a; exit=0; EXPECT=matched; output-sha256=01b7e80647d06eaf6946757af5d00a9acc430f3dde945d827cac851aaf282ed6; output-bytes=1380; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G12: mypy strict clean
  CHECK: uv run mypy src
  EXPECT: Success: no issues found
  EVIDENCE: automatic-evidence=v1; definition-sha256=6d05dbb4ca8ccbbc774b00aac0a2274db88c77c5d5cf35bfd6a3e986214c1575; exit=0; EXPECT=matched; output-sha256=1435443c9c3292dcaf529643a6ff4511859ae84e1d81e467f113226dd0a9057d; output-bytes=58; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G13: ruff clean
  CHECK: uv run ruff check .
  EXPECT: All checks passed!
  EVIDENCE: automatic-evidence=v1; definition-sha256=304de969ad2d7b880ac1c92eac805b6231dcb383090814d38560ae64c3676104; exit=0; EXPECT=matched; output-sha256=5b196eb3a6acb50d3fa398d04ca284985cc1ffec870e940264b00780bfd2c971; output-bytes=30; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G14: package builds
  CHECK: uv build
  EXPECT: Successfully built
  EVIDENCE: automatic-evidence=v1; definition-sha256=efa5b7bd848b44bff501e96fd71cf22807e5290e63be307ec2204906381ef744; exit=0; EXPECT=matched; output-sha256=26dd65c4ae45a7245b939a4e580e675408585db367974cf6a8b15d0fa451a0ec; output-bytes=269; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Lenovo\Desktop\Code\2026\System-design; path=6032e8f9c2ae/69 entries

- [x] G15: python-anti-patterns pass done, findings fixed
  EVIDENCE: python-anti-patterns pass: A1 runtime asserts on seed data -> ProviderFact load-time validation (+tests), A2 untyped list[Any] -> list[ComponentRequirement], A3 claude_cli error paths now tested (tests/unit/test_llm.py)

- [x] G16: /code-review on full diff done, findings fixed
  EVIDENCE: /code-review high on full diff vs c622a6e: 10 findings (CR1-CR10), all reproduced by tests/unit/test_review_fixes.py (12 red) then fixed (125 green); docs updated first (requirements-schema G-3 1a/1b, SCHEMA numeric rule, decision-resolution G-9/G-10)
