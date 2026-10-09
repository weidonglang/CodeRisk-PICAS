# CodeRisk Research V4 Seed Toolchain Test Report

## IR-Plag intake, fusion diagnosis and asynchronous tasks — 2026-10-09

- Python: 134 tests passed. Eight additional cases check pinned hashes, unsafe ZIP headers including Windows backslashes, publisher labels versus disputed/local labels, and exact fusion decomposition. One existing third-party warning remains.
- Backend: 16 integration tests passed with H2 and Flyway V1–V5. Four new tests cover asynchronous idempotent start, capacity rejection, partial retries and preserved results, failure history, restart recovery from stale counters, partial-report disclosure, invalid task sizes/duplicate IDs, and per-attempt time budgets. AnalysisClient is stubbed in these integration tests.
- Frontend: type check and production build passed; existing chunk-size warning remains. Result view adds polling cleanup, progress, retry, failure history and pagination. Report and detail view describe the risk display score as non-probabilistic.
- Real services: isolated persistent H2 + actual FastAPI, self-authored synthetic Python only. Recorded 10/20/50-submission runs and a missing-file partial/retry check with the original successful result ID retained. No student/downloaded code was executed. These are execution checks, not accuracy tests or MySQL verification.
- Data: all 467 IR-Plag source hashes verified; 453 byte-unique files, 355 published derivation pairs and 105 independent-creation reference pairs. Ten known disputed negatives quarantined, 52 score-blind review items prepared, actual local human reviews and formal eligibility remain zero. Archive pins and metadata retained, raw sources ignored.
- Diagnosis: 911 frozen pilot rows per view decomposed into canonical/mapping contributions, original validation-selected thresholds reused, cases/CSV/PNG saved. No new fitting or public-data scoring; no evidence of improved production accuracy claimed.

See [deliverables and limits](../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md). Historical validation below remains tied to its earlier implementation.

## Version and shared-template review context — 2026-10-09

- Python: 126 tests passed; 15 new cases cover version declarations, Python 2/3 syntax and division cues, short-code notices, exact template matching, literal/embedded-script marker boundaries, overlapping spans, null residual diagnostics and API validation. One third-party deprecation warning remains.
- Backend: 12 integration tests passed with Flyway V1–V4 and H2. Two new tests cover input rejection, persistence, request propagation, saved review metadata and HTML report escaping. AnalysisClient is stubbed in this suite.
- Frontend: TypeScript check and Vite production build succeeded. Existing third-party annotation and chunk-size warnings remain.
- Eight synthetic development cases across Java/Python/C/HTML confirmed that added review context leaves every production score and threshold unchanged. All eight have UNCERTAIN relationship labels and zero formal-metric eligibility.
- Separate live E2E: real Spring Boot and Python services, isolated transient H2 memory database and synthetic Java calculator submissions. Declared versions 8/17 and multiline starter context reached the actual analyzer and saved/exported result. Score remained 1.0; each side had 7 non-template tokens, and the result displayed INSUFFICIENT_DISTINGUISHING_EVIDENCE. No uploaded source was executed.
- Playwright/Chrome: created a synthetic question through the UI and visually checked the actual result page, including the 100% score, insufficient-evidence banner, declared versions, 68% template coverage, original-line ranges and diagnostic caveats. This does not claim a complete browser upload-flow test or live MySQL migration verification.
- Rules 40/120 tokens, natural-risk trigger 0.60 and template-dominance trigger 0.50 remain uncalibrated. There is no automatic semantic conversion, compiler-validated version or demonstrated reduction in real-data false positives. Historical ConPlag results are unchanged.

See [implementation boundaries](../coderisk_docs/proposal/VERSION_AND_NATURAL_SIMILARITY.md) and [archived synthetic checks](experiment/evidence/review-context-20261009/README.md).
## Public data review and ConPlag pilot — 2026-10-09

- Python: 111 tests passed (14 new regressions). Cached Java scoring agrees with the production API; tests cover validation-only calibration, template-free hash leakage, source path/hash checks, review identity/schema/timestamp checks, transitive split groups and safe source embedding.
- Blind-review UI: Playwright/Chrome verified missing-input rejection, HTML filter (4 pairs), save and reviewer ID lock, previous/next restoration, and JSON export with the correct manifest/source hashes. HTML source displays as text (two pre elements, zero rendered child elements). UI_TEST_ONLY exports remain ignored and are not annotations. Only browser console error was a missing favicon.
- Intake inventory: 5,575 files verified; 3,865 logical source versions inspected, no downloaded source executed. CodeNet metadata remains unavailable in the local prefix intake.
- ConPlag: 911 published pairs, 284 validation / 627 test, two paired views. 42 JPlag processes exited successfully. Native coverage 911/911 original and 909/911 template-free; missing comparisons kept unknown.
- Archive: all 36 reported confusion tables recomputed from pair scores and equal; PNG/SVG/PDF plotted from saved results, PNG visually checked. The protocol was committed and pushed before dataset scores were calculated.
- No backend, frontend or production formula changes in this increment; earlier integration checks below remain historical. Formal evaluation gates were not relaxed. See [review workflow](../coderisk_docs/proposal/DATA_REVIEW_WORKBENCH.md) and [honest pilot results](../coderisk_docs/proposal/CONPLAG_PILOT_RESULTS.md).

## C/HTML and public-source coverage verification — 2026-10-08

- Python: 97 tests passed, including C binding boundaries, HTML normalization, source locations, real analysis API responses, empty/comment-only inputs, invalid HTML thresholds and intake integrity fixtures.
- Backend: 10 integration tests passed with H2 and Flyway V1/V2/V3. New cases cover upload language mapping, mixed-domain rejection, HTML task/result metadata and fixed-threshold report export. AnalysisClient is stubbed in backend integration tests.
- Frontend: TypeScript check and Vite build succeeded. Existing bundle-size warning remains.
- Public intake: 382 inventory files verified; offline re-import has an identical inventory. All 366 new sources audited without running code or scoring pairs.
- Parser audit: Java 106/107, Python 84/102, C 72/111, HTML 46/46 structurally accepted. C normalization covers 39/111; upstream language labels are not individually verified, including C++ contamination in the C folder.
- Python 3.12.14 / Tree-sitter 0.25.2 / C grammar 0.24.2 / HTML grammar 0.23.2. Java 21 tests used a preloaded Byte Buddy agent to avoid the local sandbox attach restriction.

Details and immutable audit files: [multilanguage progress](../coderisk_docs/proposal/MULTILANGUAGE_PROGRESS.md). These are engineering/coverage checks, not a formal detection benchmark. The older sections below retain their historical counts.

## GitHub preparation verification — 2026-10-08

- Python regression: 38 passed; one third-party deprecation warning.
- Backend regression: 8 passed with H2 and Flyway V1/V2; Maven build succeeded.
- Frontend: TypeScript check and Vite production build succeeded; existing bundle-size warnings remain.
- Startup scripts now derive repository paths and preserve configured environment overrides; analysis/test scripts prefer the local virtualenv.
- The local H2 profile uses a relative path from the backend working directory. PowerShell scripts passed syntax parsing.
- GitHub Actions checks Python, backend, and frontend separately. Runtime data, databases, logs, caches, build outputs, and downloaded JPlag binaries are excluded from source control.
- This verification does not claim a fresh live MySQL E2E run or a new research benchmark.

- Version: Research V4 seed toolchain ready
- Test date: 2026-06-24
- Environment: Windows 11, Python 3.13.14, Java 21.0.11, Node/Vite local toolchain
- Production formula: FORMULA_SPEC_V1 (unchanged)
- Production algorithm: picas-v2-rule-1.0
- Experimental algorithm: picas-v4-xl-ir0.1-sum0.2-exp
- Research run: PICAS-RESEARCH-V4-SEED-20260624-R2

## Automated Verification

- `python -m pytest -q -p no:cacheprovider`: 38 passed; one third-party Starlette/httpx deprecation warning.
- `mvn test`: 8 passed; Flyway V1/V2 applied on H2 MySQL compatibility mode.
- `npm run build`: passed; Vite reported only third-party PURE-comment and large-chunk warnings.
- Research tests cover aggregation, source/hash metadata, problem/source leakage rejection, unverified AI rewrite rejection, entry-helper hashing, JPlag alignment/exclusions, validation-only calibration, and unified paper-table generation.

## Dataset Gate

- Aggregate pairs: 91, all synthetic seed; 85 eligible for core metrics.
- Source types: 87 synthetic and 4 explicit placeholders. Placeholders are not eligible.
- Validation/Test pairs: 41/50; problem counts: 15/18.
- Same-language/Cross-language pairs: 80/11.
- Problem overlap: 0; source overlap: 0; exact-code hash overlap: 0.
- Non-preregistered split cases: 7 legacy cross-language cases.
- Missing problem/case categories for seed workflow: none.
- Real-source deficits: 20 manual, 8 verified ai_assisted, and 8 external pairs.

## Threshold Calibration

- Candidate offsets: -0.08, -0.04, 0, 0.04, 0.08.
- Selection used validation only and chose -0.08; `testSetUsedForSelection=false`.
- Seed test production dynamic: precision 0.7778, recall 0.5833, F1 0.6667, FPR 0.25, NaturalSimilar FPR 0.5714, Suspicious Recall 0.4286.
- Seed test validation-calibrated: precision 0.8261, recall 0.7917, F1 0.8085, FPR 0.25, NaturalSimilar FPR 0.5714, Suspicious Recall 0.7143.
- This is experiment-only workflow evidence; `productionFormulaChanged=false`.

## Same-language and V4 Experimental Results

- Rename seed cases: mean raw/canonical token similarity 0.250836/1.0.
- Same-language failure/borderline/parser-fallback rows: 15/16/1.
- Cross-language eligible test pairs: 6.
- Raw token, language-specific AST, canonical token F1: 0/0/0.
- Experimental IR/control/data/composite F1: 0.6667/0.8/0.5714/0.6667.
- IR/control/composite FPR remains 1.0 because common structure is over-scored.
- Unsupported syntax remains a false-negative risk. All V4 metrics retain production weight 0.

## JPlag Alignment

- JPlag 6.2.0 ran successfully with Java 21 for Java and Python seed inputs.
- 72 Research V4 pairs were requested and all 72 mapped back to `pair_id`.
- 19 exclusions are recorded: 11 cross-language, 4 placeholders, 3 parser/unsupported-syntax cases, and 1 other non-eligible case.
- Test-only synthetic seed table: JPlag fixed 0.70 F1 0.7826; PICAS dynamic F1 0.6667.
- These values validate alignment and reporting only; no real-data superiority claim is supported. Dolos remains not run.

## V0-V3 Regression

- Backend `/actuator/health`, analysis `/internal/health`, and frontend returned HTTP 200 on 2026-06-24.
- The retained live E2E record is question 2 -> submissions 4/3 -> PICAS_STANDARD task 6 -> result 5 -> evidence -> HTML report 7.
- It uses FORMULA_SPEC_V1 and picas-v2-rule-1.0, contains the four production metrics and zero CROSSLANG metrics, and keeps manual-review wording without prohibited conclusions.
- Record: `data/artifacts/e2e-research-v4-v0-v3.json`.

## MySQL Boundary

MySQL80 remains installed/running, but no valid project credential is available; the documented example credential returns error 1045. Live MySQL E2E is not claimed. Persistent H2 local fallback and Flyway regression are verified.

## Conclusion

The repository reaches `Research V4 seed toolchain ready`: schema, deterministic seed data, isolation/hash validation, entry assistance, validation-only calibration, manifest-aligned JPlag, unified experiments, failure/borderline analysis, and paper tables are reproducible. It is not a formal benchmark; real manual, verified AI-assisted, and external data remain mandatory before paper-effect claims.

## Documentation Handoff Update

- Date: 2026-07-05.
- Scope: Research V4 data collection, runbook, result interpretation, paper-material generation, templates, and checklist only.
- Added runbooks: `experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md`, `experiment/RUN_RESEARCH_V4.md`, `experiment/RESULT_INTERPRETATION_GUIDE.md`, `experiment/PAPER_MATERIALS_GUIDE.md`, and `experiment/RESEARCH_V4_CHECKLIST.md`.
- Added sample folders and templates for `manual`, `ai_assisted`, `external`, `synthetic`, and `placeholder` data.
- Verification: Research V4 validator remains `valid=true`; JSON templates parse successfully; `analysis-service-python/tests/test_research_v4_dataset.py` and `analysis-service-python/tests/test_research_v4_toolchain.py` passed, 7 tests total.
- Boundaries unchanged: no core similarity algorithm changes, no V4 experimental production weight changes, no MySQL live verification claim.
