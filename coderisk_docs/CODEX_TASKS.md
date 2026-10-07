# CODEX_TASKS.md

> 本文件是 CodeRisk / PICAS 项目的 Codex 可执行任务清单。Codex 开发时必须优先遵守本文件，同时参考 `AGENTS.md`、`PROJECT_SPEC.md`、`ROADMAP.md`、`ARCHITECTURE.md`、`API_SPEC.md`、`DATABASE_SCHEMA.md`、`ALGORITHM_SPEC.md`、`CANONICALIZATION_SPEC.md`、`PROBLEM_AWARE_SCORING.md` 和 `TEST_PLAN.md`。

---

## 1. 总体执行原则

### 1.1 项目主线

本项目不是普通代码查重系统，而是：

```text
PICAS：面向编程作业场景的题目感知与置换不变代码相似风险检测系统
```

核心链路：

```text
题目特征 → 代码解析 → 基础相似度 → 标识符归一化 → 动态阈值 → 多维融合 → 风险边际 → 结构化证据 → 人工复核建议
```

### 1.2 生产版风险公式

生产版固定采用：

```text
weightedSimilarityScore = Σ wi * Sim_i
dynamicThreshold = f(problem profile)
riskMargin = weightedSimilarityScore - dynamicThreshold
```

禁止在生产版最终分数中同时叠加无界 `NaturalSimilarityPenalty` 和 `TemplatePenalty`。若要测试扣分策略，只能作为实验分支，并在 `EXPERIMENT_PLAN.md` 中作为消融实验。

### 1.3 版本边界

```text
V0 / Phase 1：业务闭环 + mock 分析
V1：真实 token + 基础 AST + 基础证据 + 代码对比
V1.5：标识符归一化 + canonical token + identifier mapping
V2：题目评分 + 动态阈值 + 多维融合 + 报告导出
V3：实验、基线、消融、论文图表
V4：跨语言 IR、CFG/DFG、AI 改写增强
```

### 1.4 接口真源

`API_SPEC.md` 是唯一外部接口真源。所有外部响应必须为 `ApiResponse<T>`，分页统一为 `ApiResponse<PageResult<T>>`。

### 1.5 文件读取策略

Docker/答辩/正式运行统一采用共享 volume：

```text
Backend:          /data/uploads/...
Analysis Service: /data/uploads/...
Artifacts:        /data/artifacts/...
```

Backend 调用 Analysis Service 时默认传 `rawCodePath` / `cleanCodePath`，路径必须在 `/data/uploads` 下。

### 1.6 语言支持级别

```text
java    STABLE
python  STABLE
c       EXPERIMENTAL
```

前端必须显示 `supportLevel`，不得把 C 或跨语言 IR 展示为稳定能力。

---

## 2. 任务格式

每个任务包含：任务目标、输入文档、涉及目录、实现要求、禁止事项、验收标准、测试命令、完成后需要更新的文档。

---

## 3. Phase 0：仓库骨架与规范

### TASK-0001：创建项目仓库结构

涉及目录：

```text
backend/
analysis-service/
frontend/
docs/
database/
scripts/
tests/golden_cases/
demo_dataset/simple_template_complex/
experiment/
reports/
```

验收标准：目录存在；`docs/` 无重复同名多版本文档；`tests/golden_cases/` 和 `demo_dataset/simple_template_complex/` 已创建。

### TASK-0002：建立统一配置与环境变量

要求：Backend、Analysis Service、Frontend 均能通过环境变量配置后端地址、分析服务地址、上传目录、artifact 目录。默认上传目录为 `/data/uploads`，默认 artifact 目录为 `/data/artifacts`。

---

## 4. Phase 1：V0 业务闭环与 Mock 分析

### TASK-BE-0101：搭建 Spring Boot Backend 骨架

接口：

```text
GET /api/system/health
GET /api/system/languages
```

要求：统一响应 `ApiResponse<T>`、统一异常处理、生成 `traceId`、支持 dev mock login。

验收标准：Backend 可启动；健康检查正常；支持语言返回 `supportLevel`。

### TASK-BE-0102：实现题目管理最小闭环

接口：

```text
POST /api/questions
GET /api/questions
GET /api/questions/{questionId}
```

要求：保存题目标题、描述、输入格式、输出格式；分页返回 `ApiResponse<PageResult<T>>`；时间格式带 offset。

### TASK-BE-0103：实现代码上传与共享 Volume 存储

接口：

```text
POST /api/questions/{questionId}/submissions/upload
GET /api/questions/{questionId}/submissions
```

要求：文件保存到 `/data/uploads/submissions/{questionId}/{submissionId}/raw.ext`；数据库保存 `raw_code_path`；限制大小和后缀；C 语言标记为 `EXPERIMENTAL`。

### TASK-AN-0101：搭建 Python Analysis Service 骨架

接口：

```text
GET /internal/health
POST /internal/analyze/mock
```

要求：FastAPI；返回固定结构 mock 结果；路径必须校验在 `/data/uploads` 下。

### TASK-BE-0104：实现检测任务创建与 Mock 调用

接口：

```text
POST /api/tasks
POST /api/tasks/{taskId}/start
GET /api/tasks/{taskId}
GET /api/tasks/recent
```

要求：状态包含 `CREATED / QUEUED / RUNNING / COMPLETED / FAILED`；保存 mock `analysis_result` 和基础 `evidence`。

### TASK-FE-0101：搭建 Vue 3 前端骨架

页面：

```text
/dashboard
/questions
/questions/create
/questions/:id
/questions/:questionId/submissions
/tasks
/tasks/:taskId/results
/results/:resultId
/experiments
/settings
```

要求：Axios 统一解包 `ApiResponse<T>`。

### TASK-FE-0102：实现 Dashboard 页面

接口：

```text
GET /api/dashboard/summary
GET /api/tasks/recent
GET /api/system/health
GET /api/system/languages
```

要求：展示系统摘要、最近任务、健康状态、语言支持级别；`EXPERIMENTAL` 明确标识。

---

## 5. Phase 2：V1 真实 Token、基础 AST 与早期 Golden Cases

### TASK-TEST-0200：建立早期 Golden Cases

目录：

```text
tests/golden_cases/
demo_dataset/simple_template_complex/
```

最低样例：

```text
identical_same_language
variable_rename_same_language
template_natural_similarity
parse_failed_fallback
simple_ast_difference
cross_language_placeholder
```

每个 case 必须有 `case.json`、题目、代码 A、代码 B、预期区间或趋势判断。

### TASK-AN-0201：实现代码清洗与语言识别

输出：`CleanCode`、`LineMapping`、`LanguageType`、`ParseStatus`。注释删除不能破坏字符串字面量，行号映射要服务证据高亮。

### TASK-AN-0202：实现 Token 提取与 TokenSimilarity

要求：区分 keyword/operator/literal/identifier；实现 n-gram token similarity；输出相似片段候选。

### TASK-AN-0203：实现基础 AST 节点类型序列

要求：Java/Python 可解析；解析失败降级到 token-only；输出 BasicASTStructureSimilarity。

### TASK-AN-0204：实现 pair 级预计算与缓存

要求：每份 submission 只清洗/解析一次；保存 token fingerprint 和 AST summary；pair 比较复用预计算结果；任务进度按 pair 更新。

### TASK-BE-0201：实现真实任务结果保存

涉及表：`analysis_result`、`evidence`、`analysis_artifact`。必须字段：`weighted_similarity_score`、`dynamic_threshold`、`risk_margin`、`risk_level`。V1 中 `dynamic_threshold` 可暂用固定基础阈值。

### TASK-FE-0201：实现任务结果总览页

接口：

```text
GET /api/tasks/{taskId}/results
GET /api/tasks/{taskId}/results/summary
```

展示：weightedSimilarityScore、dynamicThreshold、riskMargin、riskLevel、分页和筛选。

### TASK-FE-0202：实现代码对比与基础证据页

接口：

```text
GET /api/results/{resultId}
GET /api/results/{resultId}/code-pair
GET /api/results/{resultId}/evidence
```

要求：Monaco Editor 左右对比；相似片段高亮；点击证据定位代码；不直接输出“抄袭”。

---

## 6. Phase 3：V1.5 标识符归一化与 Canonical Token

### TASK-AN-0301：实现标识符类别识别

要求：Java/Python 分别处理；变量、参数、函数、类名可区分；保留作用域信息。

### TASK-AN-0302：实现 CanonicalTokenSequence

要求：变量映射为 `VAR_1`，参数映射为 `PARAM_1`，函数映射为 `FUNC_1`；保留关键字、操作符、结构 token。

### TASK-AN-0303：实现 IdentifierMappingSimilarity

要求：输出映射表、mapping coverage、mapping consistency；作为证据，不作为直接抄袭结论。

---

## 7. Phase 4：V2 题目评分、动态阈值与多维融合

### TASK-AN-0401：实现题目特征提取

特征包括：descriptionLength、ioFieldCount、constraintCount、referenceLOC、referenceFunctionCount、referenceCyclomaticComplexity、apiCallCount、dataStructureCount。

### TASK-AN-0402：实现题目评分

计算 `DifficultyScore`、`SolutionSpaceScore`、`TemplateRiskScore`、`NaturalSimilarityRisk`。规则评分为主，LLM 只允许辅助解释；每个评分必须有 confidence 和 evidence。

### TASK-AN-0403：实现动态阈值

要求：输出 dynamicThreshold、riskMargin 和阈值解释；历史提交分布必须稳健处理，禁止直接使用未清洗 p95。

### TASK-AN-0404：实现多维融合评分

V2 必做：TokenSimilarity、BasicASTStructureSimilarity、CanonicalTokenSimilarity、IdentifierMappingSimilarity、TemplateAwareWeightAdjustment。输出 weightedSimilarityScore、每项 metric 和权重配置。

### TASK-FE-0401：实现题目复杂度分析页

展示 DifficultyScore、SolutionSpaceScore、TemplateRiskScore、NaturalSimilarityRisk、dynamicThreshold explanation、Confidence、Evidence。

---

## 8. Phase 5：风险报告、证据输出与人工复核

### TASK-BE-0501：实现报告导出

报告必须包含题目画像、风险分数、动态阈值、riskMargin、证据片段、人工复核建议，不输出“抄袭”结论。

### TASK-BE-0502：实现 manual_review 最小闭环

如果前端需要“已复核”按钮，则必须实现 `manual_review` 表和对应 API。若不实现，则前端只能展示“复核建议”。

---

## 9. Phase 6：前端可解释展示

### TASK-FE-0601：实现多维相似度图表

展示 TokenSimilarity、ASTSimilarity、CanonicalTokenSimilarity、IdentifierMappingSimilarity、weightedSimilarityScore、dynamicThreshold、riskMargin。

### TASK-FE-0602：实现证据链面板

证据类型包括 TOKEN_FRAGMENT、AST_STRUCTURE、CANONICAL_TOKEN、IDENTIFIER_MAPPING、TEMPLATE_PATTERN、RARE_FRAGMENT。点击证据能定位代码。

---

## 10. Phase 7：V3 实验、基线、消融与论文图表

### TASK-EXP-0701：构建正式实验数据集

要求：题目按简单、模板、中等、复杂分组；样本按 L0-L8 伪装等级分组；保存数据卡；不公开未经授权的学生真实代码。

### TASK-EXP-0702：实现基线运行与结果导入

基线包括 StringSimilarity、TokenSimilarity、ASTSimilarity、FixedThreshold、JPlag、Dolos、MOSS 或 MOSS-compatible result import、PICAS variants。

### TASK-EXP-0703：实现消融实验

配置包括 PICAS-Full、w/o ProblemAwareThreshold、w/o Canonicalization、w/o IdentifierMapping、w/o RareFragment、FixedThresholdOnly、TokenOnly、ASTOnly。

---

## 11. Phase 8：V4 跨语言 IR、CFG/DFG 与 AI 改写增强

### TASK-AN-0801：实现跨语言 IR 实验性骨架

Java/Python 优先，C 标记为 EXPERIMENTAL；不宣称完全语义等价检测。

### TASK-AN-0802：AI 改写样本增强

只评价结构相似风险，不宣传成 AI 生成检测。

---

## 12. Phase 9：论文、专利、软著材料

### TASK-DOC-0901：更新论文材料

论文公式与生产版一致，实验结果来自真实运行，图表可复现。

### TASK-DOC-0902：专利公开顺序检查

公开前确认：专利申请已提交或明确放弃；GitHub README 已脱敏；不公开完整核心公式、权利要求草案和技术交底书。

### TASK-DOC-0903：软著说明书按真实版本删减

如果只完成 V1，不写 V2 功能；截图必须来自真实系统；不把 mock 页面作为正式功能截图。

---

## 13. Phase 10：发布与答辩准备

### TASK-REL-1001：清理压缩包与文档重复路径

压缩包只包含一个 `coderisk_docs/` 目录，不包含 `mnt/data/coderisk_docs/` 重复路径。

### TASK-REL-1002：答辩演示脚本

演示顺序：创建题目、上传代码、启动检测、查看任务进度、查看结果总览、查看代码对比、查看证据链、展示动态阈值解释、展示实验看板、导出报告。

---

## 14. 全局禁止事项

1. 禁止直接输出“抄袭”结论；
2. 禁止前端绕过 Backend 直接调用 Analysis Service；
3. 禁止外部接口返回裸 JSON；
4. 禁止把 C 语言和跨语言 IR 标成稳定能力；
5. 禁止把 mock 数据写成真实实验结果；
6. 禁止每个 pair 重复解析两份代码；
7. 禁止生产版最终分数无界扣分；
8. 禁止 Docker 下使用容器私有路径导致 Analysis Service 读不到文件；
9. 禁止公开专利交底书和权利要求草案；
10. 禁止把软著说明书写得超过真实已实现功能。

---

## 15. 当前实现状态与下一步

截至 V4 前置收口：

```text
已完成：V0 业务链路、V1 token/基础 AST、V1.5 scope-aware canonicalization
已完成：V2 规则题目画像、动态阈值、多维融合、JDBC/Flyway 持久化、HTML 报告
已完成：V3 36-case 五题型合成数据、problem-level validation/test 隔离、E1-E5 与失败案例
已完成：JPlag 6.2.0 Java 真实 smoke run、native CSV adapter 与哈希清单
已完成：V4 Phase 1 有限 Java/Python normalized IR
已完成：V4 Phase 2 lightweight control/data-flow summaries 与 7-case 失败实验
待扩展：正式规模授权数据、扩大 JPlag/Dolos 结果、统计显著性、MySQL 实库凭据验证
明确不在当前版本：完整 CFG、完整 DFG、PDG、符号执行、AI 改写增强
```

当前为 `V4 Phase 2 experimental candidate`。不要把 JPlag smoke run 表述为正式规模基线，也不要把当前小样本跨语言结果表述为正式论文结论。
