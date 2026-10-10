# AGENTS.md

> 本文件是给 Codex / AI 编程助手 / 后续开发者的项目总指令。任何开发任务开始前必须先阅读本文件。若本文件与临时口头需求冲突，以本文件中“项目定位、核心创新、禁止事项、验收标准”为优先；确需变更时，先更新本文件和相关规格文件，再修改代码。

---

## 1. 项目身份

2026-10-08 用户明确要求增加 C 与 HTML 检测。C 是算法题实验增强项，HTML 是独立的页面源码结构风险检测分支，使用待校准固定阈值，不套用算法题画像；二者当前只允许同语言任务。Java/Python 仍是论文主评测范围。HTML 不执行网页或脚本，C 不编译或运行下载的代码，公开未标注源码不得当作正负例。具体范围见 `proposal/MULTILANGUAGE_PROGRESS.md`。

### 1.1 项目名称

**CodeRisk / PICAS：面向编程作业的题目感知型代码相似风险检测系统**

建议论文方法名：

```text
PICAS: Problem-aware Invariant Code Similarity Analysis
```

中文表述：

```text
基于题目复杂度自适应与置换不变结构表示的代码相似风险检测方法
```

### 1.2 项目定位

本项目不是普通的“代码查重系统”，也不是简单的 token/字符串相似度工具，而是一个面向编程作业、课程设计和算法题提交场景的**题目感知型代码相似风险评估系统**。

系统核心不是直接判定“抄袭”，而是输出：

```text
相似风险分数 + 动态阈值 + 风险等级 + 结构化证据 + 人工复核建议
```

任何页面、接口、算法、文档都必须遵守以下原则：

1. 不直接给出“抄袭成立”的结论；
2. 只输出“相似风险等级”和“复核证据”；
3. 所有高风险判断必须可解释、可追溯、可复核；
4. 题目本身的自然相似风险必须参与判断；
5. 系统创新点必须围绕题目复杂度自适应、置换不变规范化、多维结构相似度和证据输出展开。

---

## 2. 核心研究问题

开发时必须始终服务以下研究问题：

### RQ1：题目感知动态阈值是否能降低简单题误报？

简单输入输出题、模板题、固定套路题天然容易相似，因此不能使用统一固定阈值。系统需要根据题目难度、解法空间、模板化风险和自然相似风险动态调整阈值。

### RQ2：置换不变规范化是否能提升对表层伪装的鲁棒性？

代码改变量名、函数名、参数名、格式、注释后，结构相似性不应显著下降。系统需要构建 canonical representation，弱化无语义标识符差异。

### RQ3：多维结构证据是否比单一相似度更适合人工复核？

系统不能只给一个百分比，必须输出 token、AST、控制流、数据依赖、稀有片段、变量映射、边界处理等证据。

### RQ4：跨语言结构表示是否能对 Java/Python/C 的同题解法进行初步对齐？

跨语言检测不是第一阶段强制完整完成，但系统架构必须预留语言无关 IR，优先支持 Java + Python，C 作为增强项。

---

## 3. 优先级规则

开发优先级如下：

```text
算法正确性与可解释性 > 实验可复现性 > 后端稳定性 > 前端展示清晰度 > UI 美观 > 非核心功能
```

### 3.1 必须优先实现

1. 代码上传、任务创建、结果查询的基础闭环；
2. Java/Python 代码预处理；
3. Token 相似度和基础 AST 相似度；
4. 标识符归一化；
5. 题目复杂度评分；
6. 动态阈值计算；
7. 风险等级输出；
8. 相似片段和证据输出；
9. 实验脚本和可复现实验结果。

### 3.2 后续增强实现

1. 控制流相似度；
2. 数据依赖相似度；
3. 稀有片段相似度；
4. Java-Python 语言无关 IR；
5. C 语言支持；
6. JPlag/Dolos 结果导入和对比；
7. AI 改写样本检测；
8. 论文图表自动生成。

### 3.3 暂不优先实现

以下内容不是项目核心，除非核心功能已经稳定，否则不要投入过多时间：

```text
复杂权限系统
复杂社交功能
复杂消息通知
在线多人协作
拖拽式工作流
3D 可视化
过度动画
主题换肤
复杂后台运营系统
云端大模型强依赖
```

---

## 4. 技术栈约束

### 4.1 推荐总体架构

```text
frontend-vue/              Vue 3 前端
backend-springboot/        Spring Boot 主业务服务
analysis-service-python/   Python/FastAPI 分析服务
experiment/                实验数据、脚本、评测结果
docs/                      项目文档、论文材料、专利材料
scripts/                   启动、构建、数据初始化脚本
deploy/                    Docker Compose 与部署配置
```

### 4.2 后端主服务

推荐：

```text
Java 21
Spring Boot 3.x
Spring Web
Spring Security / 简化 JWT
MyBatis Plus 或 Spring Data JPA
MySQL 8
Redis
OpenAPI/Swagger
```

职责：

1. 用户与任务管理；
2. 题目管理；
3. 代码文件上传与存储；
4. 调用分析服务；
5. 保存分析结果；
6. 提供前端 API；
7. 报告导出；
8. 实验结果展示接口。

### 4.3 Python 分析服务

推荐：

```text
Python 3.11+
FastAPI
Pydantic
Tree-sitter
numpy
pandas
scikit-learn 可选
networkx 可选
pytest
```

职责：

1. 语言识别；
2. 代码预处理；
3. Token 提取；
4. AST 解析；
5. 标识符归一化；
6. 结构指纹生成；
7. 多维相似度计算；
8. 题目复杂度评分；
9. 动态阈值计算；
10. 证据片段定位；
11. 实验评测脚本。

### 4.4 前端

推荐：

```text
Vue 3
Vite
TypeScript
Element Plus
Pinia
Vue Router
Axios
ECharts
Monaco Editor
```

前端不是创新核心，但必须把创新展示清楚：

1. 题目复杂度分析；
2. 动态阈值解释；
3. 多维相似度图表；
4. 左右代码高亮对比；
5. 结构化证据链；
6. 实验结果看板。

---

## 5. 代码质量要求

### 5.1 通用要求

1. 所有核心算法函数必须有单元测试；
2. 所有接口必须有明确请求/响应模型；
3. 不允许把复杂逻辑写在 Controller；
4. 不允许把算法逻辑写死在前端；
5. 不允许直接在业务代码中拼接大量魔法字符串；
6. 配置项必须放入配置文件或常量类；
7. 错误返回必须有统一格式；
8. 日志必须能定位任务 ID、提交 ID、代码对 ID；
9. 实验结果不得硬编码；
10. 任何评分公式都必须可配置、可解释、可复现。

### 5.2 命名规范

推荐使用以下概念名，避免混乱：

```text
Question                题目
Submission              代码提交
DetectionTask           检测任务
CodePair                代码对
ProblemFeature          题目特征
SimilarityMetric        相似度指标
RiskResult              风险结果
Evidence                证据
DynamicThreshold        动态阈值
CanonicalRepresentation 规范化表示
LanguageIndependentIR   语言无关中间表示
```

### 5.3 风险等级命名

统一使用：

```text
LOW
MEDIUM
ELEVATED
HIGH
```

中文展示为：

```text
低风险
中风险
较高风险
高风险
```

不要使用：

```text
抄袭
确定抄袭
作弊成立
直接判定违规
```

---

## 6. 数据与结果真实性要求

### 6.1 不得伪造实验结果

Codex 或开发者不得写入虚假 Precision、Recall、F1、误报率、响应时间等指标。实验结果必须来自真实脚本运行输出。

### 6.2 不得用随机数模拟核心指标

允许构造 demo 数据用于前端展示，但必须明确标注：

```text
mock / demo / sample
```

论文、实验报告、README 中不得把 mock 数据写成真实实验结果。

### 6.3 实验数据必须可追溯

每条实验结果至少记录：

```text
dataset_id
case_id
method_name
config_version
run_time
metric_values
result_file_path
```

---

## 7. 算法开发边界

### 7.1 第一阶段算法底线

必须至少实现：

1. 代码清洗；
2. Token 序列提取；
3. 标识符归一化；
4. Token 相似度；
5. AST 节点类型序列相似度；
6. 题目特征评分；
7. 动态阈值；
8. 风险等级；
9. 相似片段证据。

### 7.2 不允许伪装成已完成的高级能力

如果尚未实现真正的 CFG/Data Dependency/IR，不得在 UI、README 或论文中声称已经实现。

允许标注：

```text
experimental
prototype
limited support
future work
```

不允许标注：

```text
fully supports semantic clone detection
complete cross-language understanding
accurately determines plagiarism
```

### 7.3 LLM 使用边界

2026-10-10 研究实施计划阶段 4–5 的明确例外：允许在 `experiment/` 的隔离、可关闭工具中比较 Direct LLM，并试验 PICAS 候选筛选后的 LLM 复核线索。默认 mock/dry-run、无网络；真实响应只作带来源记录的离线导入，不能把 mock 算作模型准确率。提示词/Schema/阈值仅 development/validation 调整；真实混合实验须先满足可靠基线、完整标注候选池和 Recall@K 门禁。许可、隐私、预算、缓存、失败及原文证据必须记录；人工判断仍是最终环节。本例外不允许自动付费、上传学生代码、执行源码、接入生产评分或给出关系成立结论。以下限制继续适用于生产链路。

如果后续接入 LLM：

1. LLM 不得直接判定抄袭；
2. LLM 不得作为唯一评分来源；
3. LLM 只可用于题目辅助解释、报告语言化、样本改写生成；
4. 所有核心分数必须来自可复现的规则、统计或算法模块。

---

## 8. 前端开发边界

前端必须服务算法解释，不做无意义炫技。

### 8.1 必做页面

1. 题目与任务创建页；
2. 代码上传页；
3. 任务状态页；
4. 题目复杂度分析页；
5. 检测结果总览页；
6. 代码对比与证据页；
7. 实验结果看板页；
8. 报告导出页。

### 8.2 必做展示组件

1. 多维相似度雷达图/柱状图；
2. 动态阈值解释卡片；
3. 左右代码对比 Monaco Editor；
4. 相似片段高亮；
5. 变量映射表；
6. 证据列表；
7. 风险等级标签；
8. 实验指标图表。

---

## 9. 文档同步要求

每完成一个核心模块，必须同步更新对应文档：

```text
PROJECT_SPEC.md         功能边界变化
ROADMAP.md              阶段进度变化
ARCHITECTURE.md         架构或模块变化
ALGORITHM_SPEC.md       算法公式或指标变化
API_SPEC.md             接口变化
DATABASE_SCHEMA.md      表结构变化
EXPERIMENT_PLAN.md      实验变化
```

如果代码实现与文档不一致，优先修正文档或代码，不能长期保留冲突。

---

## 10. 分支与提交建议

推荐分支：

```text
main
release/v1.0.0
dev
feature/parser
feature/canonicalization
feature/problem-scoring
feature/report
feature/frontend
feature/experiment
```

提交信息建议：

```text
feat(parser): add Java token extraction
feat(scoring): implement dynamic threshold calculator
feat(report): add evidence summary API
fix(canonical): handle scoped variable renaming
exp(eval): add L1 identifier rename benchmark
```

---

## 11. 任务验收规则

每个 Codex 任务完成后，必须至少满足：

1. 代码可编译/可运行；
2. 单元测试或最小接口测试通过；
3. 不破坏已有功能；
4. 有明确输入输出；
5. 有异常处理；
6. 有日志；
7. 有必要文档更新；
8. 如果是算法任务，必须有可复现测试样例；
9. 如果是前端任务，必须能通过 mock 或真实接口展示；
10. 如果是实验任务，必须保存运行配置和结果文件。

---

## 12. 禁止事项清单

严禁：

1. 把项目做成普通学生管理系统；
2. 只实现字符串相似度后宣称完成查重；
3. 直接输出“抄袭”结论；
4. 没有证据只输出风险等级；
5. 没有题目特征却声称动态阈值；
6. 没有规范化模块却声称置换不变；
7. 没有真实实验却写论文结论；
8. 把 LLM 输出当作最终判断；
9. 用 mock 数据冒充真实实验；
10. 为了 UI 美观牺牲核心算法和可复现性。

---

## 13. 最小可交付版本定义

### V1：基础可运行版

必须具备：

1. Java/Python 文件上传；
2. 代码清洗；
3. Token 相似度；
4. 基础 AST 相似度；
5. 标识符归一化；
6. 基础风险报告；
7. 前端结果展示。

### V2：本科毕设版

必须具备：

1. 题目复杂度评分；
2. 动态阈值；
3. 置换不变规范化；
4. 多维相似度融合；
5. 结构化证据；
6. 实验对比；
7. 报告导出。

### V3：期刊增强版

必须具备：

1. 完整实验集；
2. L0-L8 伪装等级；
3. JPlag/Dolos 或同类工具对比；
4. 消融实验；
5. 统计分析；
6. 失败案例分析；
7. 论文图表输出。

---

## 14. 自检清单

开发者在提交任何重要任务前，必须自检：

```text
[ ] 是否服务“题目感知代码相似风险检测”主线？
[ ] 是否避免直接判定抄袭？
[ ] 是否保留结构化证据？
[ ] 是否考虑简单题自然相似风险？
[ ] 是否有测试样例？
[ ] 是否有异常处理？
[ ] 是否没有伪造实验结果？
[ ] 是否与 PROJECT_SPEC / ROADMAP / ARCHITECTURE 一致？
[ ] 是否没有引入过度复杂的非核心功能？
[ ] 是否更新必要文档？
```
