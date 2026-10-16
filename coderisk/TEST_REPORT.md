# CodeRisk Research V4 Seed Toolchain Test Report

## 结果图表与研究增量发布检查 - 2026-10-16（第二轮）

- 仅新增前端展示逻辑：全任务风险分布、当前页列表/图表、详情综合分与阈值同刻度图、Canonical−Raw展示差值、正负阈值调整条（含历史分布项）、移动端结果、证据筛选/长源码定位、源码布局和映射搜索。不更换生产公式、API、数据库结构或experimental权重。
- 本轮真实运行Python **591 passed / 1既有warning，14.98s**；Maven **19 tests / 0failure/error/skip，测试7.561s/总9.665s，BUILD SUCCESS，H2**。旧任务超时/恢复ERROR与WARN是测试覆盖，不是失败；MySQL未实库验证。
- 前端 **18项单测通过**，Windows开发脚本 **26项检查通过**；最终类型检查/Vite **1713模块，3.99s，成功**。没有新增npm依赖或改package-lock；旧PURE/大chunk警告保留。
- 真实浏览器自有题目/源码端到端 **41项通过**（创建→上传→分析→结果→证据→HTML），详情真实报告/筛选另 **5项通过**；新增图表/交互 **30项通过**，既有模拟状态 **7项通过**，共83项。图表/状态模拟只在临时浏览器，不写数据库或冒充算法结果。1440/768/390/320宽度包含任务图表、移动列表及详情检查。
- 额外按CI入口运行fair evaluation：**75行 synthetic development 结果**，JPlag显式SKIPPED；只验证离线流程，不覆盖历史实验、不改正式资格或声称真实检测增益。
- 保留失败：初次浏览器连接时服务未运行；首次完整流程测试对桌面/手机同文案的选择不唯一，已限定桌面范围；图表测试直接操作Element Plus隐藏原生checkbox超时，改操作可见label并验证isChecked后通过。详情复验误点被占位文字覆盖的select内部input并在另一轮导航时detach，改为可见wrapper并串行重跑5项通过。CLI错误可能仍exit0，按最终JSON检查checks/errors，不能只看退出码。
- 发布范围依用户本次授权包含此前研究代码、测试、文档和自有/汇总证据。原始数据池/数据库/凭据/本机任务书不发布，历史归档不修改；MIT只涵盖项目原创内容，第三方许可证限制不变。
- 暂存检查发现旧日志/JUnit的工具原生尾随空格与末尾空行；仅对冻结证据下log/xml声明`-whitespace`，保留原始字节及校验值。源码和普通文档不豁免空白检查。
- 本轮记录、命令、截图和限制见 [结果展示证据](experiment/evidence/result-review-20261016/README.md) 和 [阅读指南](../coderisk_docs/RESULT_PRESENTATION_GUIDE.md)。以下第一轮及更早记录保持原日期，不改成第二轮结果。

## 前端展示与开发启动流程 - 2026-10-16

- 本轮只改Vue/启动脚本/说明及CI的前端测试步骤，生产算法、后端API和数据库迁移源码不改。起始保留dirty工作区和暂存；保护清单见 `output/ui-refresh-20261016/baseline.json`，最终核验见 [前端证据包](experiment/evidence/ui-refresh-20261016/README.md)。未提交或推送。
- `python -m pytest -q -p no:cacheprovider`：**591 passed / 1既有warning，67.33s，exit0**。`mvn test`：**19 tests，0failure/error/skip，测试8.979s/总13.672s，BUILD SUCCESS**，仅H2。`npm test`：**12 passed**；脚本语法/端口/进程身份/路径等 **26 checks passed**。最终 `npm run build`：**1706模块，4.02s，成功**，原有PURE/chunk警告未隐瞒。
- Playwright/Chrome真实服务流程最终 **41检查通过**：题目、上传、静态分析任务、结果、证据选择/源码高亮、映射/阈值/背景标签页、HTML下载；七类页面×1440/768/390/320宽度无整页溢出。另 **7项拦截响应UI检查通过**：分页、后端不可用、内部错误不泄露、缺失值不假装0、parser fallback不伪造IR、实验指标零权重、终态读取先于结果请求。模拟响应不写入数据库，不能当算法证据。
- 使用隔离DataRoot，首次快照重启验证 **3题/6提交/3任务及结果不变**；最终再跑UI流程新增1题/2提交/1任务。均带UI_SELF_AUTHORED标记，不是人工独立或真实模型数据；没有执行上传源码。后端/前端/分析就绪、停止后6个相关端口释放、重复启动复用同一会话已验证。
- 初始失败保留：sandbox realpath/Chrome启动限制；工具VM缺URL全局、过严链接选择器、起始视口影响、API模拟误拦截前端模块；修正后对应最终JSON检查通过。首次幂等验证发现JSON日期转型导致误建第二组，补字符串/日期/指纹契约并按身份停止第二组；该组曾打开默认local库，未建题/提交/任务，不声明默认DB文件字节不变。真实业务测试与后续重启一直使用独立DataRoot。
- 默认JAVA_HOME实际为Temurin17，脚本自动选择本机已装21；不修改持久化机器配置。`-CheckOnly`不等于实库验证；MySQL、真实模型或教师效益NOT_RUN。证据、截图、命令及局限见 [前端与启动手册](../coderisk_docs/FRONTEND_AND_DEV_WORKFLOW.md)。以下日期化研究历史不覆盖。

## AI 时代价值验证 V0—V5 - 2026-10-12

- 本轮重跑，不借用旧结果：关机前Python **590 passed，1既有Starlette/httpx warning，46.24s，exit0**；恢复后初跑589pass/1fail，63.25s，因隐私测试把allowed output内的basetemp当成非法路径。仅隔离测试根并新增允许/逃逸契约，2项定向通过，最终全量 **591 passed / 1 warning，61.37s，exit0**，相对523基线新增68测试。原门禁/生产代码未改；新日志/JUnit在 `output/ai-era-value-20261012/resume-validation/`。H2 Maven **19 tests / 0 failure/error/skip，BUILD SUCCESS，总16.356s**；vue-tsc/Vite **1699 modules，5.11s**，旧PURE/chunk警告保留。
- 新离线协议/来源关系/泄漏/正式门禁/只读上下文/隐私/直接CLI等覆盖见 [本轮测试摘要](../coderisk_docs/research/TEST_AND_EVIDENCE_SUMMARY.md)。初始GBK、CRLF字节hash、模式/告警、stdlib同名及raw输出门禁失败均保留，不抹红测。
- mock13 artifacts/12会话/22对；JPlag6.2.0本地Java/Python实际运行、19对匹配，六方法共同14；正式指标N/A。1728合法性质探针再次通过，另10尝试状态保留，6个自有Java编译但不执行。ConPlag两view各911只读重核，不重评分/拟合，Full低于NoCanon保留。
- 真实模型/学生新增/真人审核/教师效益/功能执行/MySQL实库/当前浏览器E2E/Dolos均NOT_RUN；formal预期exit2。API、数据库和生产源码无本轮改动；起始197 dirty、129生产文件、1492历史文件及暂存/HEAD核对见 [证据与保护检查](experiment/evidence/ai-era-value-20261012/README.md)。最新完整本地输出是 `output/ai-era-value-20261012/analysis-release/`，不是early analysis-final。历史日期化记录如下保留。

## S0—S5 开题研究收口 - 2026-10-11

- 实际基线main/HEAD `892e7ef4a0d2f016cc8b0713fc7b347bd9e1717f`，预存88修改/未跟踪文件；新测试不冒充clean HEAD的能力。本轮未commit/push/发布/改历史。
- Python初跑8 failed/423 passed：sandbox标准TEMP权限问题；工作区TEMP/TMP后431 passed。Java header遮蔽红测2 failed/17 passed保留；最小raw降级后54通过，后续扩充最终**523 passed，1既有Starlette/httpx warning，43.77秒**。相比基线新增**92项**。完整JUnit/日志在`output/opening-research-20261011/s0/python-final-r2.*`；第一次最终521项是在最后两项契约增加前的中间运行。
- 环境差异复核：旧复用环境Tree-sitter 0.26.0，项目声明0.25.2；隔离安装0.25.2并记录真实导入路径后，全量仍**523 passed，1 warning，32.47秒**。日志`python-pinned-parser.*`，没有改旧环境或生产依赖声明。
- 最终实际`mvn test`：**19 passed，0 failure/error/skip，BUILD SUCCESS，11.437秒**，H2/Flyway5迁移；超时/失败重试ERROR/WARN是既有测试覆盖，不是test失败。Mockito/H2警告保留。没有MySQL实库验证。
- 最终实际`npm --prefix coderisk/frontend-vue run build`：vue-tsc/Vite成功，1699modules，bundle build5.06秒；既有PURE/大chunk warning保留。本轮不重跑浏览器、不将build当E2E。
- 独立性质12自有gold（三seed×48置换）**1,728/1,728接受检查通过**，总尝试1,738：拒绝5、parser失败2、非法捕获1、oracle不确定2不计成功。6次自有Java编译通过且未执行。唯一源码/稳定子统计单列，次数不是独立数据规模。
- 14方法新seed消融：91输入/75分析/共同68（validation32/test36）；canonical降级7保留。公开ConPlag只读分解重新运行，读取两view各911、0重评分/拟合；历史负结果未更改。统计参考0、q可用0，全规则回退；正式preflight输出FORMAL_BLOCKED并按require-ready退出2。
- 图表首次缺matplotlib；pip首次临时目录权限、第二次索引JSON截断，均记录；设置可写TEMP并使用既有实验requirements/legacy resolver重试安装成功，最终只读图表/manifest成功，图已查看，无新算法/依赖规格修改。
- 生产公式/API/DB不改；规范化已知Java header遮蔽改为explicit fallback，可影响这类pair的既有融合分但不是新权重或提高效果。最终历史/暂存/源码保护及链接见新verification.json。详见 [S0审计](../coderisk_docs/research/OPENING_BASELINE_AUDIT.md)、[双维报告](../coderisk_docs/research/INVARIANCE_DISCRIMINABILITY_REPORT.md)、[研究包](../coderisk_docs/research/OPENING_RESEARCH_PACKAGE.md) 与 [精选证据](experiment/evidence/opening-research-20261011/README.md)。

下面保留之前阶段的真实状态与数字，不覆盖历史。

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

## Python and seven-language intake - 2026-10-10

- Actual pinned PoolC first train shard: 598,736 published rows audited; 30,000 distinct balanced pairs selected, referencing 29,280 different Python source texts. 27,961 parse under Python 3.12.14; 1,319 fail and remain explicitly unsupported/possibly Python 2. No code execution or syntax conversion.
- Actual pinned XLCoST mirror: 57,661 tokenized program records across Python/C/C++/JavaScript/C#/PHP/Java. 30,893 unlabelled title-aligned cross-language candidates, including 20,713 without Java. These are not verified official parallel pairs or raw source files.
- All fixed sizes and LFS SHA-256/Git blob pins verified. Both intakes pass full offline reconstruction. Title ambiguity and split/hash reuse exclusions are recorded; unknown author/problem identity is not invented. PoolC license is unspecified and quarantined; all new pairs are noneligible, external, non-synthetic and locally UNCERTAIN.
- Python full regression: **263 passed**, one existing third-party warning, no failures/skips. Includes 24 new fixture tests for pins, quotas, conflict/content deduplication, title ambiguity, split leakage, immutable output, syntax-failure disclosure, tamper rejection and honest summary counting. JUnit: `../output/nonjava-all-tests-20261010-r2.xml`.
- Production algorithms/weights, backend/frontend and supported languages were not changed by this increment. Maven/build/JPlag/MySQL/E2E were not rerun.

Evidence and commands: [data card](../coderisk_docs/proposal/NONJAVA_PUBLIC_INTAKE.md) and [verification](experiment/evidence/nonjava-intake-20261010/verification.json).

## Large pinned public code-pair intake - 2026-10-10

- Actual CodeXGLUE BCB intake downloads eight pinned upstream files, verifies Git blob identities/byte lengths and records SHA-256. All 1,731,860 published pair rows resolve to 9,126 Java function records.
- Selected development pool: 30,000 distinct nonidentical text pairs from upstream train, 15,000 per published label. All are external, non-synthetic and locally UNCERTAIN/noneligible. No new synthetic pairs, code execution or detector scoring.
- Audit: 117 contradictory text-pair labels excluded from selection; 1,723 text pairs repeat across upstream splits. Function IDs do not overlap splits, but text hashes do (94/76/26); problem/author isolation remains unknown.
- Offline verification independently reconstructs selected identities, labels and source metadata from fixed inputs and checks every saved function. It passes for 30,000 pairs. Byte hashes have zero intersection with the previous 3,865-record public and 467-record IR-Plag registries.
- Python full regression: **239 passed**, no failures/skips, one existing third-party warning. Fifteen new self-authored intake tests cover pin verification, missing references, deterministic balance, reverse/content deduplication, conflicts, overlap disclosure, unavailable quotas, immutable output and offline tamper rejection.
- Existing production scoring, backend and frontend were unchanged; no new Maven/build/MySQL/browser E2E verification in this data-only increment. No new formal effect claim is supported.

Evidence: [verification record](experiment/evidence/codexglue-bcb-intake-20261010/verification.json) and [data card](../coderisk_docs/proposal/LARGE_PUBLIC_PAIR_INTAKE.md).

## Research intake and development fusion diagnostics - 2026-10-10

- Python full regression: **224 passed**, one existing Starlette/httpx deprecation warning. Uses Python 3.12.14 from `.tmp/language-venv`; JUnit record is `../output/intake-fusion-tests-20261010-r2.xml`.
- Added 36 tests: 33 intake/alignment checks and 3 development-diagnostic checks. Placeholder core exclusion, AI source/case-type gates, blank and timezone fields, pre-append nonmutation on split/hash/version failures, and prediction source-identity validation are covered.
- Existing Research V4 seed remains 91 pairs / 85 workflow-eligible, 41 validation / 50 test, zero problem/source/source-family/hash overlap. New 16 development probes are separate, synthetic and excluded from core metrics. Seven rename/format/fallback contracts pass; nine probes are descriptive only.
- JPlag preparation smoke: 72 requested pairs, 19 documented exclusions, status PREPARED. No new native JPlag execution or real verified AI sample is claimed; AI admission is tested with explicitly self-authored unit fixtures.
- Diagnostic outputs preserve source/fingerprint/Git metadata and immutable directories. Public ConPlag test scores were not rerun or tuned; algorithm service and production weights/thresholds were unchanged.
- Environment failures were resolved before the successful run: old project venv could not launch its Store Python; sandbox default temporary paths caused fixture permission failures. Tests use the valid local Python 3.12 environment and workspace TEMP/TMP plus a fresh pytest basetemp. No tests were skipped.
- Backend, frontend, browser E2E and live MySQL checks were not rerun in this experiment-tool-only increment. Previous verification remains historical.

Scope, commands and observed limitations: [intake and fusion development notes](../coderisk_docs/proposal/INTAKE_AND_FUSION_DIAGNOSTICS.md).

## AI technical review and correctness hardening — 2026-10-09

- Python: **188 passed**, one existing Starlette/httpx warning. The new Python scope file has 39 self-authored cases; API checks cover explicit fallback reasons and zero mapping/canonical weights. Review identity has six checks, and IR intake has thirteen, including immutable output protection.
- Backend: **19 passed**, no failures/errors/skips. H2 MySQL mode only, AnalysisClient stubbed. Tests cover huge page numbers, early size/duplicate validation, the stored-result/unresolved-failure crash window, and two independent transactions serializing first feature writes for one question.
- Frontend: type check/production build succeeded. Browser controlled terminal-transition race confirms final results are fetched after terminal state and shown; AI context rejection, locked identity and downloaded v2 JSON verified. UI_TEST_ONLY fixtures are not dataset annotations.
- Real isolated Spring Boot/FastAPI/H2: 10/20/50 self-authored Python submissions complete 45/190/1225 pairs. Missing-file partial/retry preserves successful result ID and resolves failure history. Initial incorrect local URL environment variable was corrected and the run repeated; this setup failure remains disclosed.
- Offline provenance: actual 467 IR-Plag sources and 460 relationships verified against pinned archive reconstruction; new 52-pair packet uses global ordering and A/B swaps. No new source acquisition, public-data scoring or substantive local human annotation in this increment.
- No production weights/thresholds retuned. Unsupported Python scope constructs now explicitly fall back, changing coverage rather than proving accuracy improvement. Three subagents are AI technical reviewers, not human annotators.

See [frozen engineering records](experiment/evidence/review-hardening-20261009/README.md) and [support boundaries](../coderisk_docs/proposal/AI_REVIEW_HARDENING.md). Earlier sections retain their original version-specific counts.

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
