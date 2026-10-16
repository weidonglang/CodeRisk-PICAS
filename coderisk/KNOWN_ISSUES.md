# Known Issues

## 2026-10-16 描述性统计边界（第三轮）

- 新统计只覆盖当前页筛选结果；若当前覆盖全部已生成结果会明确说明，但共享提交的pair仍非独立样本。没有构造全任务推断、相关系数、回归或显著性。
- 各分量独立有效n；无效值不补0。箱线图n≥4只是保守展示门槛，须线为min/max，不做1.5IQR异常检测。不同分量不当作总和100%的贡献饼图。
- ECharts6.1.0按需分包约584KB/199KB gzip，旧主包仍较大；不隐藏体积警告。图表模块失败可保留数值并显式刷新恢复分析链接。
- 新增六份自编静态UI样例/15实际代码对只在隔离H2联调，不执行、不计入正式数据，不证明语义或关系。MySQL/真实LLM/正式标签仍未因此完成。
- 生产依赖audit更新后0，完整audit遭遇TLS失败，不能说完整依赖审计无风险；安全软件会向本机浏览器注入自己的请求，测试排除环境流量而非关闭防护。
- 项目版权署名魏语石，MIT正文和第三方许可边界保留；不是软著登记证明。[统计与署名说明](../coderisk_docs/STATISTICAL_VISUALIZATION.md)。

## 2026-10-16 结果图表边界（第二轮）

- 风险分布是全任务已生成summary；对比点仅是当前页筛选结果。未完成/失败代码对不计入分布，当前页搜索不是全库搜索。
- 缺失、不合法分量不画成0；风险分类、边际与最终阈值读取原API，不由图表重算。Canonical−Raw是展示差值，不能变成风险加分或识别效果结论。
- 阈值条保留正负调整及历史分布项，但不代替原公式/最终裁剪；跨语言IR/轻量摘要仍是experimental零生产权重。
- 新增图表不引入依赖，也没有解决旧Element Plus主包较大的警告。MySQL实库、真实模型和教师效益仍待验证。
- 截图用隔离H2的自有UI样例；不能当成真实学生案例或benchmark。详情“任务报告”包含所属任务全部成功代码对，不是单对报告。
- [结果阅读说明](../coderisk_docs/RESULT_PRESENTATION_GUIDE.md)与[本轮记录](experiment/evidence/result-review-20261016/README.md)保留测试工具失败和验证范围。

## 2026-10-16 前端与启动流程

- 新UI与真实服务在自有隔离H2完成浏览器回归；MySQL仍未实库验证。后端health只证明后端，分析地址和数据库类型不冒充探测结果。
- 题目/结果搜索明确只作用当前页，任务搜索作用最近任务；不把客户端过滤包装成全库搜索。宽表格保留内部横向滚动，窄屏证据另用逐条列表。
- 首次重复启动测试发现PowerShell JSON日期对象与字符串比较不一致，误建第二组备用端口服务；修复并补身份回归，已验证停止第二组及保留第一组。第二组曾打开默认local数据库，未写新题/提交/任务；不主张默认DB文件字节不变。
- 初次构建/Chrome被沙箱权限拦截，获许可本机执行后通过；浏览器工具VM/选择器/模拟请求范围失败留日志，不能把CLI返回0当作测试通过，须核最终JSON检查结果。
- 日志/会话元数据不可在服务存活时随意删除；开发启动器不是生产服务管理器，不支持多命令并发启动。已有PURE/chunk及Starlette/Mockito/H2警告保留。
- 详情见 [界面与启动手册](../coderisk_docs/FRONTEND_AND_DEV_WORKFLOW.md)。旧日期记录仅代表当轮状态。

## 2026-10-12 AI 时代价值验证限制

- 当前新增数据都是13自编artifacts/12 mock sessions/22 pairs，正式资格0；different model、same question、functional pass不认证来源独立性。公开候选规模不能弥补可信关系不足。
- canonical可用14/22，完整C相等7/14仅探针，不是真实跨模型趋同率；C不保证轨道单射或语义等价，Full含raw因而不是群不变量。固定/规则总分相同，阈值不同；规则Recall代价不能隐藏。
- native JPlag共同支持14对，未匹配/降级留在全量说明；当前无base-code排除，不宣称已验证去模板收益。test仅2连通组件，不能把pair作独立样本或给出正式区间/精度；分母不足为N/A。
- 出题前/交卷后卡是只读离线信息展示。有限ngram定位不支持完整maximal match-length分布；来源历史未知时不推AI使用，教师效益须真人盲走查。
- 真实调用/人审/功能执行/MySQL/本轮浏览器/Dolos均NOT_RUN；Gitignore不是ACL/加密，聚合导出不授权公开。正式试点依 [采集教程](../coderisk_docs/research/LIVE_GENERATION_PLAYBOOK.md)；[当前决策](../coderisk_docs/research/PICAS_GO_NO_GO_DECISION.md)是INSUFFICIENT_EVIDENCE/条件PIVOT，不是GO。

## 2026-10-11 S0—S5 新确认的研究限制

- Java brace绑定不能完整表示for/catch header生命周期；已识别同名可见绑定时保守`JAVA_HEADER_SHADOW_BINDING_UNSUPPORTED`回退，不能据mode或balanced tokens声称完全parse/type-resolved。普通非遮蔽header及其他高级形式未因此全部正确。
- 统一拼写G轨道不等于局部α关系；C可把不同G轨道合并。重复语句次数可在n-gram集合和融合中丢失，已有自有机制C不同/融合1实测；不是已修复判别缺陷或真实FPR。
- 独立gold相对生产oracle降低同源风险，但人工gold/有限stdlib交叉检查不是完备证明，Java6次javac不证明绑定语义。
- 正式前检91seed、evidence-ready0、formal0；可信独立参考0、全部q回退。公开候选/模板/同题提交不自动可信负例。补真实授权/双审/功能/冻结而非伪填字段。
- 本轮MySQL实库、真实LLM、浏览器E2E未运行；H2/API/前端build不替代。环境临时目录权限、图表缺依赖和pip索引截断失败均保留，最终重试通过不抹失败。
- 研究方法/结果与人工阻塞见 [开题研究包](../coderisk_docs/research/OPENING_RESEARCH_PACKAGE.md)。以下历史已知问题保留。

- 2026-10-10: PoolC adds 30,000 public-label Python pairs but its pinned metadata has no license/citation/homepage; quarantine until conditions are clarified, no redistribution/formal calibration. 1,319 selected sources fail Python 3 syntax parsing; labels and opaque groups do not establish independent authors or derived rewrites. XLCoST adds seven-language tokenized records, not runnable source; official problem maps are absent in the mirror. 30,893 exact-title candidates are unlabelled/unreviewed, and 23 language/text hashes repeat across upstream splits. All new formal eligibility remains zero. C has only 574 tokenized records; C++/JavaScript/C#/PHP are data reserves, not new service support. See [actual scope](../coderisk_docs/proposal/NONJAVA_PUBLIC_INTAKE.md).

- 2026-10-10: CodeXGLUE BCB now adds 30,000 distinct published Java function pairs, selected from train only. This release lacks coursework problem/author/project metadata. Full upstream audit finds 117 text-pair label conflicts and 1,723 cross-split repeated text pairs; formal eligibility remains zero. Function fragments are not automatically compatible with full-program upload/JPlag. See [intake evidence](../coderisk_docs/proposal/LARGE_PUBLIC_PAIR_INTAKE.md).

- 2026-10-10: 16 self-authored development probes reproduce declaration-order/scope-number sensitivity after inserting unused locals/functions. Pure Java/Python rename contracts pass, but insertion invariance is not supported; mapping=1 can occur for different operations with common structure. No production tuning or public test rescoring was done. See [diagnostics](../coderisk_docs/proposal/INTAKE_AND_FUSION_DIAGNOSTICS.md).
- 2026-10-10: Research V4 placeholder/AI intake gates and pre-append isolation checks are enforced. Verified same-language AI rows can enter JPlag alignment; old baseline rows without source hashes remain explicitly unverified. Workflow core eligibility is not formal double-human-review eligibility.

- 2026-10-09: Python scope normalization deliberately falls back for comprehensions, global/nonlocal, annotation/binding forms and dynamic class namespaces not modeled reliably. Warning reasons include source locations; canonical/mapping evidence is omitted and production scoring uses raw Token. This improves honesty of support coverage, not proven accuracy. See [boundaries and regression evidence](../coderisk_docs/proposal/AI_REVIEW_HARDENING.md).

2026-10-09: bounded asynchronous task execution and retry/restart recovery now support one backend instance. Multiple backends sharing a database, distributed leases, cancellation and hard interruption of analysis remain unsupported. V5 is tested in H2 only. IR-Plag has publisher-controlled relationships and known disputed negatives; it is not local double-reviewed formal evidence. See [current boundaries](../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md).

2026-10-08 C/HTML extension: both are experimental and require same-language tasks. C macro/typedef/extern/complex prototype normalization falls back to lexical analysis. HTML does not render pages or understand JavaScript/CSS behavior; its fixed threshold is uncalibrated. New CodeNet/MDN intake is unlabelled, upstream C has mixed-language files, and formal C/HTML baselines remain pending. See [coverage audit](../coderisk_docs/proposal/MULTILANGUAGE_PROGRESS.md). Tree-sitter is pinned to 0.25.2 after a local native crash with 0.26.0; the full audit succeeds with the pin. Flyway V3 is verified in H2 only; historical results without profile snapshots retain the legacy latest-profile fallback.

1. MySQL 8.0.42 is available locally, but passwordless `root` and the documented example `coderisk/coderisk` credential are rejected with error 1045. Live MySQL E2E still requires a valid local credential; persistent H2 verification is not presented as MySQL verification.
2. Research V4 now aggregates 91 pairs, but every row is synthetic seed data. Four AI_REWRITE rows are explicit placeholders excluded from core metrics. Reaching the numeric target does not make this a real benchmark.
3. The validator still reports real-source deficits: 20 manual, 8 verified ai_assisted, and 8 external pairs. AI-assisted samples cannot enter core metrics without model/prompt provenance, manual review, and functional verification.
4. Validation-only seed calibration selected an experimental dynamic-threshold offset of -0.08. On seed test data it improved F1 from 0.6667 to 0.8085 without changing NaturalSimilar FPR (0.5714). This validates split discipline only; the offset must not modify production coefficients.
5. JPlag 6.2.0 is manifest-aligned for 72 synthetic seed pairs and records 19 explicit exclusions. The test-only seed table does not support an external-baseline superiority claim. Dolos is reserved and not run.
6. The cross-language classification subset contains only 6 eligible test pairs, while 7 legacy cross-language cases still have non-preregistered split metadata. IR/control/composite FPR is 1.0 because the common-structure probe is over-scored; these synthetic exploratory metrics are too small and unstable for confirmatory claims.
7. Unsupported Java lambda/Python generator syntax loses summary coverage and under-scores a related probe. Full CFG, DFG, PDG, symbolic execution, semantic equivalence, and AI-generation detection remain unsupported.
8. Java AST remains a minimal structural sequence parser. All V4 IR/control/data metrics are experimental, have production weight 0, and do not enter PICAS_STANDARD.
9. Vite reports a non-blocking bundle-size warning. FastAPI tests emit one third-party Starlette/httpx deprecation warning.
