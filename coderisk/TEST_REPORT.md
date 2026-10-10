# CodeRisk Research V4 Seed Toolchain Test Report

## 研究阶段 5 混合实验门禁 - 2026-10-11

- 新测试 27 项通过。未知 selected pair 会悄悄改变分母的红测先失败后修复；fallback 不删、同分排序、validation-only 选 K、真实基线不得被 development 绕过均验证。
- 全工作树 Python 431 项通过、1 条既有 warning；数量包含其他未提交任务。隔离阶段源码验证与前后端最新回归见本阶段证据及下方最终记录，不冒充 MySQL 实库验证。
- 本轮实际回归 `mvn test`：H2 19 项通过；`npm run build`：vue-tsc 和 Vite 成功。首次 sandbox 分别阻碍 JDK attach 管道与 Vite realpath，解除限制重跑成功；保留既有依赖/大包 warning。不重跑浏览器，不声称 MySQL 已验证。
- 现 seed 实跑 mock/import 门禁：91 输入、75 分析、完整池 0，K=null、Recall@K=N/A，选中/真实响应/网络调用/费用 0。测试专用完整池的 6 对/18 请求仅是 mock 契约，不是有效关系数据。
- 正式混合评测尚被数据/授权/真实基线门禁阻断；没有模型收益结论，不改变生产评分/API/数据库。协议与实跑产物见 [混合说明](../coderisk_docs/research/HYBRID_DETECTION.md) 与 [证据](experiment/evidence/hybrid-review-20261011/README.md)。

## 研究阶段 4 离线 LLM 对照 - 2026-10-10

- 新测试 27 项；全工作树 404 项通过、1 条既有 warning。费用漏计及重复缓存写入红测先复现后修复；mock/伪响应不算模型准确率。
- 91 synthetic 输入/75 分析/16 排除，mock 与 dry-run 真正执行；LLM 分数 N/A，真实响应、正式资格、新网络调用与费用均 0。JPlag Java/Python exit 0、72 对 matched，同源码共同 test 38 对。详细结果见 [协议](../coderisk_docs/research/LLM_BASELINE.md) 及 [归档](experiment/evidence/llm-baseline-20261010/README.md)。
- API/DB/生产权重不改；本阶段未重跑未改动的后端/前端/浏览器，H2 历史验证不冒充 MySQL 实库验证。

## 研究阶段 3 独立解答统计校准 - 2026-10-10

- 新测试 40 项通过；包含上下尾并列/平滑契约、验证集独占选参、门禁不可豁免、真实文件/原始与文本 hash、CRLF、模板只影响资格、解析降级及跨 split/panel 身份隔离。MOCK_TEST_ONLY 人工声明只属于测试，未制造真人标签。
- 当前完整工作树 Python 377 项通过，1 条既有 Starlette/httpx warning；包含其他未提交任务，不能称为 clean HEAD 的测试数量。JUnit 原始输出已归档。
- 以 HEAD+本阶段补丁导出的最终隔离源码 tree `7b8c27a8d68e55dfdea3cb62b3a6f1c4ddb33928` 独立验证 40 项通过；其 seed metrics.csv 与工作树实跑逐字节相同（SHA-256 `9da7399cf99f87d973ff191cbce23b2e1691dd7c49476cfe150195d4af049ce4`）。没有把其他未提交实现当作本阶段依赖。
- 门禁红测先发现 registration 非对象及额外身份泄漏漏检；hash 红测 2 项失败复现了前缀/Windows 换行隔离缺口，随后修复。生产算法没有改动，初次新模块缺失的 collection error 不算生产算法失败。
- actual seed run：91 输入、75 分析（validation 35/test 40）、16 排除，trustedReferencePairs/calibratableQueries/formalEligiblePairs 均 0；alpha 未选，统计策略逐条规则回退。默认 formal 已由集成测试实际拒绝，输出目录未创建。CSV/JSON/Markdown 完整生成，但不支持真实统计改善结论。
- 本阶段 API/数据库/后端/前端不改，不重跑 mvn/npm/浏览器；上一批 H2 19 项/build 成功仅为历史验证，MySQL 实库仍待凭据。源码/命令/限制见 [研究说明](../coderisk_docs/research/NATURAL_SIMILARITY_CALIBRATION.md) 与[证据归档](experiment/evidence/natural-calibration-20261010/README.md)。

## 研究阶段 2 隔离消融 - 2026-10-10

- 新实验契约/真实 seed 集成测试 19 项通过；当前完整工作树 Python 337 项通过，1 条既有 Starlette/httpx warning。完整结果含其他未提交任务测试，不是 clean HEAD 的数量。
- 默认 formal run 实际被拒绝，未创建结果目录；显式 allow-development 实跑 91 输入/75 分析/68 共同可用，14 方法与完整 CSV/JSON/Markdown 生成成功，formalEligiblePairs=0。
- Recall@K 的候选遗漏测试先失败再修复；现在要求完整 query pool、实际数量匹配且保留不支持的候选。seed 的 Recall@K 全为 N/A。生产 FORMULA_SPEC/canonicalization/token_similarity 文件 hash 与上一批一致。
- 本轮未改后端/前端，不重跑 mvn/npm；上一批 H2 19 项与 build 通过仅作历史记录，MySQL 实库仍待验证。协议、命令、失败及证据见 [研究消融说明](../coderisk_docs/research/SIMILARITY_ABLATION.md)。

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
