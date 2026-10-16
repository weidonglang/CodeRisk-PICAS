# AI 时代价值验证 V0—V5：本轮交付报告

日期：2026-10-12。当前状态为**可自动实施的离线工具、测试、证据和研究材料已收口；正式效果验证依然受阻**。不是正式 benchmark，也不是项目生产版本升级。

总入口：[证据包](../../coderisk/experiment/evidence/ai-era-value-20261012/README.md)、[Windows 复现手册](REPRODUCE_AI_CONVERGENCE.md)、[真实采集步骤](LIVE_GENERATION_PLAYBOOK.md)。以下是依据当前 dirty 工作树的结果，不能仅凭 clean HEAD 重现。

## 0. HEAD、工作区保护与源码哈希

- `main` / HEAD `892e7ef4a0d2f016cc8b0713fc7b347bd9e1717f` 未改变，未提交、推送、发布、重写历史或清理用户修改。
- 起始 197 个 dirty/untracked 文件保留；其中 12 份已有说明文档进行有意增量同步，其余保持原始字节。
- 129 个生产保护文件、1,492 个历史产物的字节 SHA-256 均不变。Git index 字节和暂存条目也与基线一致。
- 最新实验 43 份源码指纹、45 份输入文件字节指纹核验一致，冻结配置语义一致，当前 JPlag 原生结果和数据 manifest 哈希一致。
- 对照及范围见 [verification.json](../../coderisk/experiment/evidence/ai-era-value-20261012/verification.json)、[改动/源码清单](../../coderisk/experiment/evidence/ai-era-value-20261012/source_and_change_inventory.json)。Markdown 链接检查仅核本地目标存在，不冒充远程 URL/锚点验证。

## 1. V0—V5 阶段状态

| 阶段 | 状态 | 已完成与受阻 |
| --- | --- | --- |
| V0 | DONE | 四场景、合理替代方案、可证伪价值矩阵、两世界反例、文献支持范围 |
| V1 | DONE（离线） | schema、本地导入、构对、来源/政策分离、字节hash、会话和连通泄漏门禁 |
| V2 | PARTIAL | 六方法/当前JPlag/逐对分布/缺失/组件统计可运行；只有mock，正式效果无法估计 |
| V3 | DONE（离线原型） | 出题前预检及交卷后只读上下文报告；不改分、不推断来源；用户收益NOT_RUN |
| V4 | BLOCKED | 复用人审工作台/空表/正式门禁；真实授权、会话、功能、人审、受试者未具备 |
| V5 | DONE（材料/决策） | README、开题附录、复现/测试/失败记录、INSUFFICIENT_EVIDENCE及条件PIVOT |

各阶段 STATUS 存于证据包 V0—V5 子目录；DONE 不等于真实模型效果或正式学术结论已经完成。

## 2. 文件改动及业务影响

新增 [ai_convergence 离线包](../../coderisk/experiment/ai_convergence/README.md)：13个Python模块/入口、冻结示例配置、6个schema、预算空表。核心入口包括 protocol、validate、ingest、build_pairs、analyze、jplag、prepare_review、export_public；context/report/descriptive_stats仅做研究解释和统计。

新增3个测试文件：`test_ai_convergence_protocol.py`、`test_ai_convergence_analysis.py`、`test_ai_convergence_privacy.py`。恢复后只修正隐私测试夹具根目录并补1项路径契约，**门禁实现及全部生产源码未变**。

新增研究材料：AI_ERA_VALUE_AUDIT、VALUE_CLAIM_EVIDENCE_MATRIX、AI_CONVERGENCE_PROTOCOL、AI_CONTEXT_EXPLANATION_SPEC、LIVE_GENERATION_PLAYBOOK、PICAS_GO_NO_GO_DECISION、PROPOSAL_AI_ERA_APPENDIX、REPRODUCE_AI_CONVERGENCE、TEST_AND_EVIDENCE_SUMMARY，以及本报告/续接记录。增加独立日期化证据目录。

增量更新根 README、coderisk 的 TEST_REPORT/KNOWN_ISSUES、文档导航/ROADMAP/VERSION_MATRIX/EXPERIMENT_PLAN/TEST_PLAN/PAPER_OUTLINE，以及proposal导航/内容稿/文献矩阵。保留截图、启动、架构、MIT、数据规模、历史实验与旧阶段结果。

**生产四权重、规则阈值、风险等级、API、数据库、Vue页面和原有评分代码无本轮修改。** V4 experimental 权重保持0，不新增核心检测算法。此前Java header降级和异步业务修改是本轮开始前的已有改动，不认领或回滚。

## 3. 协议、数学与统计口径

来源关系（独立/派生/未知）、生成辅助方式、课程政策分别记录；功能正确性另作资格和分层字段，不能将functional pass解释为独立。不同供应商或相同题目不是独立性依据，共享上游/同一会话/无证据者必须保留UNCERTAIN。真实raw仅本地ignored output；Gitignore不是访问控制或加密。

复用原loader/评分/阈值/指标与原生JPlag，不另写第二套算法。严格按题目、source family、session、源码hash连通隔离，重复prompt/model snapshot作敏感性披露。以组件为聚类单位宏平均配对bootstrap，不能把n(n-1)/2 pair当独立样本。当前test组件只有2，默认不足6时CI=N/A。

数学证据区分三件事：

1. **有限不变性**：固定名称域、捕获规避、外部名保留及绑定结构不变等条件下讨论 `C(g·P)=C(P)`，独立gold和动作检查支持有限实现契约；不是全Java/Python机器证明。
2. **信息损失**：C可合并不同轨道，指纹集合可合并不同完整序列；canonical稳定不能证明区分更强或完整语义等价。整个Full含raw，不是群不变量。
3. **来源不可识别性**：相同题面与最终代码、不同来源历史构成两世界；确定性输出相同，随机化的条件输出分布也相同，源码分数/LLM不能凭空恢复缺失历史。可用授权过程记录是另一输入条件。

正反例见 [条件不变性与轨道边界](ORBIT_ALPHA_EQUIVALENCE.md)、[本轮审计](AI_ERA_VALUE_AUDIT.md) 及 properties/gold_bindings、discrimination、rename_sensitivity；不推断所有高canonical程序都属于同一轨道。

## 4. 实际测试、退出码和失败

| 记录 | 实际结果 | 退出码 |
| --- | --- | --- |
| 初始既有基线 | 522pass/1fail，GBK中文Git状态；UTF8重跑523pass | 1 / 0 |
| 关机前完整实现 | 590pass/1既有warning，46.24s | 0 |
| 恢复后初跑 | 589pass/1fail/1warning，63.25s，basetemp位置依赖夹具 | 1 |
| 隔离夹具与路径契约 | 2pass，1.32s | 0 |
| **最终Python全量** | **591pass/1warning，61.37s，相对523基线新增68项** | **0** |
| H2 Maven | 19tests/0failure/error/skip，测试8.883s，总16.356s | 0 |
| vue-tsc/Vite | 1699modules，build5.11s；既有PURE/chunk warning | 0 |
| 新JPlag原生 | Java、Python退出0；19对对齐 | 0 |
| 正式评测门禁 | FORMAL_BLOCKED，不生成假指标 | 2（预期） |

Python命令：`python -m pytest -q -p no:cacheprovider --basetemp <新目录> --junitxml <新报告>`；本机Python3.12.14、Tree-sitter0.25.2、PYTHONUTF8=1、workspace TEMP，复现前缀见手册。后端 `mvn -f coderisk/backend-springboot/pom.xml test`，前端 `npm --prefix coderisk/frontend-vue run build`。

新协议CRLF/哈希、adapter模式与具体告警、直接CLI的stdlib遮蔽、raw输出门禁、恢复后测试夹具失败均有日志/JUnit；jar读取UTF8失败无独立日志，明确如此记录。失败原因/最终状态见 [failure_records.json](../../coderisk/experiment/evidence/ai-era-value-20261012/failure_records.json)，命令/原生XML结果见 [execution_records.json](../../coderisk/experiment/evidence/ai-era-value-20261012/execution_records.json)。没有删红测或以最后成功掩盖失败。

## 5. 三类数据及正式资格

- **本轮自有合成**：3 mock题、13手写代码、12 MOCK会话、22对；不是模型实际生成，均DEVELOPMENT_ONLY，正式资格0。黄金绑定12样例和1,728动作是另一组性质探针，不是1,728份独立真实代码。
- **公开历史**：ConPlag两个源码view各911对（validation284/test627），只读分解而未重评分/拟合。两view不算双倍独立数据，已观察test与单人公开标签仍有局限。92,513条公开接收/候选登记未变；数量不能转换成可靠独立关系或当前实验运行量。
- **真实新增**：实际模型调用0、新增真实学生/模型来源0、真人审核0、受试者0；未使用收费API或上传私有代码。FORMAL_BLOCKED正确保留，未伪造授权或验证。

MySQL实库、真实模型、功能执行、当前浏览器E2E、教师效益与Dolos为NOT_RUN。H2/build不能替代这些。

## 6. 公平比较、发现与代价

当前六组是 Raw / AST / Canon / NoCanon-fixed / PICAS-fixed / PICAS-rule，额外native JPlag6.2.0、minTokens5。新JPlag只读源码并实际本地运行：22请求、19prepared/matched、严格全方法共同支持14；解析缺失不补零，另列原因。当前**无base-code去除**，PICAS同样保留模板token，不能说已验证去模板收益。

受控改名：raw=0.030303，AST/canonical/mapping=1，Full=0.806061，规则阈值0.820155。这支持有限表示稳定，却同时展示全分非不变以及阈值取舍；不是来源可信的现实漏报率，不为它调生产阈值。

canonical有效14/22、完整C和ngram相等各7/14，只是设计探针，不能推断真实独立AI趋同率。固定/规则模式分数相同而阈值不同。未知关系下FPR/F1/AP都N/A，没有可称正式检测优势的证据。

历史公开只读结果：v1 Full F1=0.554307 < NoCanon=0.598540；v2 Full=0.697368 < NoCanon=0.735202。各自冻结参数和共同分母限制保留，不拼入新AI表，不掩盖不利结果。旧合成动态策略有误报下降与Recall损失，不移植为新真实效益。

## 7. 正式试点为何受阻及操作

完整步骤、文件树、字段、费用空表、授权和双审在 [LIVE_GENERATION_PLAYBOOK](LIVE_GENERATION_PLAYBOOK.md)。用户需亲自：

1. 与导师/学校确认研究目标、隐私、AI政策、再分发和第三方提交范围；不先上传未公开题目或学生代码。
2. 准备4—8分层题的题面、模板和功能测试条件；冻结problem/source/session/hash分集与提示/参数计划，登记版本，不用已见test调参。
3. 在自己有权限的模型/工具中进行分离新会话，保存原始prompt/response、时间、模型snapshot、参数/失败/截断；不同模型仍检查共享上游。预算需本人确认，工具不自行调用。
4. 保存独立人工解答依据及明确父版本派生过程；功能验证在另行授权受限环境执行，来源和功能记录分开，不填写虚构PASS。
5. 两位真人独立审查关系与证据，保留冲突/仲裁/UNCERTAIN；AI不能冒充真人。导入校验通过不认证许可真实性。
6. 使用新run ID依次导入/校验/正式门禁/六方法与native共同cohort实验；有同意后盲走查复核卡。完整命令在复现手册，先`--help`。

资源不足则只做可用性走查；不能声称教师更快/更准确，RQ3不升级为主论文必须结论。

## 8. Go / Pivot / Stop 的判断

**INSUFFICIENT_EVIDENCE** 是正式价值判定；不能填GO。工具完整并不证明效果。

有条件 **PIVOT**：保留有限不变性、表示区分损失、真实公平比较/负结果和辅助复核原型作为可答辩方法研究。尚无证据全面优于Raw/NoCanon/JPlag，也不能由mock断言项目完全无用。

**STOP FEATURE**：不开发AI来源/个体模型归因、自动违规概率或处分功能。暂缓无可信数据的新融合、统计q/LLM增强和复杂Dashboard投入；若证据卡真人走查无益或误导，不集成Vue。转GO需新冻结可信数据、合理对照和可复核净价值，不以挑有利分层替代。

## 9. 仅保留三个最高价值待办

1. 授权与冻结的4—8题真实小试点，可靠独立/派生关系、功能记录和真人复核优先于数量。
2. 共同cohort Raw / NoCanon / PICAS / JPlag比较，分析canonical碰撞/解析降级/阈值Recall代价；负结果如实报告。
3. 有同意的教师盲走查，决定题目预检/证据卡是否产生增量，最后才考虑上线。

## 10. 给导师的200—300字说明

本项目研究的不是自动认定抄袭，而是同题编程作业中相似信号的适用范围及人工复核依据。AI辅助可能使独立程序趋同，因此源码高相似不能直接解释为派生关系。我拟保留题目感知与标识符规范化主线，通过独立绑定金样例验证有限重命名不变性，同时与Raw、NoCanon和JPlag比较稳定性、区分能力及误报召回代价。已有负结果将完整保留。跨模型数据和教师证据卡作为授权条件下的小规模探索，缺少可靠来源或真人审核时明确不计算正式成绩。即使未证明优于现有工具，也可形成可复现的方法边界分析与辅助复核原型，而不夸大研究结论或将风险分用于直接处分学生。
