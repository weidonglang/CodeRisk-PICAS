# ARCHITECTURE.md

> 2026-10-08 新增 `app/analyzers/structured_languages.py`，由 Tree-sitter 解析 C/HTML，再提供词法位置、结构序列及保守规范化。上传后缀映射和任务同语言校验在 Spring Boot，HTML 固定阈值策略在分析服务，Vue/报告展示同一结果。Flyway V3 保存逐结果画像快照，阈值读取原始 JSON，不将 HTML 写入算法题画像表。来源固定配置、导入器和逐源码审计位于 `experiment/`；下载源码不执行。见 [实际边界](proposal/MULTILANGUAGE_PROGRESS.md)。

> 本文件定义 CodeRisk / PICAS 的系统架构、模块边界、数据流、部署模式和扩展策略。架构设计必须服务“题目感知型代码相似风险检测”主线，避免把系统做成普通管理平台。

---

## 1. 架构目标

系统架构需要同时满足四类目标：

### 1.1 工程闭环

能够完成：

```text
题目创建 → 代码上传 → 检测任务 → 分析服务 → 结果保存 → 前端展示 → 报告导出
```

### 1.2 算法扩展

能够逐步加入：

```text
Token 相似度
AST 相似度
置换不变规范化
题目复杂度评分
动态阈值
控制流相似度
数据依赖相似度
语言无关 IR
实验评测
```

### 1.3 论文复现

能够保存实验数据、配置、指标和图表，使论文实验可重复运行。

### 1.4 成果交付

能够支撑：

```text
本科毕设
软著
发明专利交底
期刊论文
GitHub 展示
```

---

## 2. 总体架构

推荐采用：

```text
Vue 3 前端
        ↓ HTTP
Spring Boot 主业务服务
        ↓ HTTP / REST
Python FastAPI 分析服务
        ↓
Tree-sitter / Similarity Engine / Experiment Engine
        ↓
MySQL / Redis / File Storage / Experiment Files
```

### 2.1 架构图，文本版

```text
┌───────────────────────────────────────────┐
│                Frontend Vue               │
│ Task UI / Report UI / Evidence UI / Charts│
└─────────────────────┬─────────────────────┘
                      │ REST API
┌─────────────────────▼─────────────────────┐
│          Backend Spring Boot               │
│ Question / Submission / Task / Result      │
│ Auth / File / Report / Experiment API      │
└───────────────┬───────────────┬───────────┘
                │               │
                │ REST           │ JDBC / Cache / File
┌───────────────▼──────────────┐ │
│    Analysis Service FastAPI  │ │
│ Parser / Canonicalizer       │ │
│ Similarity / Threshold       │ │
│ Evidence / Experiment        │ │
└───────────────┬──────────────┘ │
                │                │
┌───────────────▼────────────────▼──────────┐
│ MySQL / Redis / Local File / Experiment DB │
└───────────────────────────────────────────┘
```

---

## 3. 推荐仓库结构

```text
coderisk/
  README.md
  AGENTS.md
  PROJECT_SPEC.md
  ROADMAP.md
  ARCHITECTURE.md

  backend-springboot/
    pom.xml
    src/main/java/
    src/main/resources/
    src/test/java/
    docs/

  analysis-service-python/
    pyproject.toml 或 requirements.txt
    app/
      main.py
      api/
      core/
      parsers/
      canonicalization/
      similarity/
      problem_scoring/
      evidence/
      experiment/
      schemas/
    tests/

  frontend-vue/
    package.json
    src/
      api/
      router/
      stores/
      views/
      components/
      charts/
      editors/

  experiment/
    datasets/
    configs/
    runs/
    reports/
    plots/
    scripts/

  docs/
    algorithm/
    api/
    database/
    paper/
    patent/
    software-copyright/
    screenshots/

  deploy/
    docker-compose.yml
    docker-compose.full.yml
    mysql/
    redis/

  scripts/
    init-db.sh
    seed-demo-data.sh
    run-experiment.sh
```

---

## 4. 服务划分

### 4.1 frontend-vue

职责：

1. 题目创建；
2. 代码上传；
3. 检测任务管理；
4. 结果总览；
5. 代码对比；
6. 证据链展示；
7. 动态阈值解释；
8. 实验图表展示；
9. 报告导出入口。

不负责：

```text
核心算法计算
风险评分
代码解析
实验指标计算
```

### 4.2 backend-springboot

职责：

1. 用户和基础鉴权；
2. 题目管理；
3. 上传文件管理；
4. 检测任务编排；
5. 调用 Python 分析服务；
6. 保存分析结果；
7. 提供查询接口；
8. 报告导出；
9. 实验结果查询；
10. 系统日志与审计。

不负责：

```text
复杂代码解析
AST 规范化
相似度核心算法
实验批处理核心逻辑
```

### 4.3 analysis-service-python

职责：

1. 语言识别；
2. 代码清洗；
3. token 提取；
4. AST 解析；
5. canonical representation；
6. similarity engine；
7. problem scoring；
8. dynamic threshold；
9. evidence extraction；
10. experiment runner。

不负责：

```text
用户登录
复杂权限
页面展示
业务数据长期管理
```

---

## 5. 模块边界

### 5.1 后端模块

推荐 Java 包结构：

```text
com.coderisk
  common
    config
    exception
    response
    security
    util
  user
  question
  submission
  task
  result
  evidence
  report
  experiment
  integration
    analysis
```

### 5.2 分析服务模块

推荐 Python 结构：

```text
app/
  main.py
  api/
    health_api.py
    analyze_api.py
    problem_api.py
    experiment_api.py
  schemas/
    analyze_schema.py
    problem_schema.py
    evidence_schema.py
  core/
    language_detector.py
    code_cleaner.py
  parsers/
    java_parser.py
    python_parser.py
    c_parser.py
  canonicalization/
    identifier_normalizer.py
    expression_normalizer.py
    ast_canonicalizer.py
  similarity/
    token_similarity.py
    ast_similarity.py
    control_flow_similarity.py
    data_dependency_similarity.py
    risk_fusion.py
  problem_scoring/
    feature_extractor.py
    difficulty_scorer.py
    template_risk_scorer.py
    natural_similarity_scorer.py
    threshold_calculator.py
  evidence/
    snippet_locator.py
    mapping_evidence.py
    structure_evidence.py
    report_builder.py
  experiment/
    dataset_loader.py
    baseline_runner.py
    metric_calculator.py
    ablation_runner.py
```

### 5.3 前端模块

推荐 Vue 结构：

```text
src/
  api/
    questionApi.ts
    submissionApi.ts
    taskApi.ts
    resultApi.ts
    experimentApi.ts
  views/
    DashboardView.vue
    QuestionListView.vue
    QuestionCreateView.vue
    SubmissionUploadView.vue
    TaskListView.vue
    ResultOverviewView.vue
    EvidenceDetailView.vue
    ExperimentDashboardView.vue
  components/
    ProblemScorePanel.vue
    DynamicThresholdCard.vue
    SimilarityRadar.vue
    CodeCompareEditor.vue
    EvidenceList.vue
    IdentifierMappingTable.vue
    RiskLevelTag.vue
  stores/
    taskStore.ts
    resultStore.ts
  router/
  utils/
```

---

## 6. 数据流设计

### 6.1 检测任务数据流

```text
1. 前端提交题目和代码
2. 后端保存题目数据
3. 后端保存原始代码文件
4. 后端创建 DetectionTask
5. 后端调用分析服务
6. 分析服务读取代码文本
7. 分析服务执行清洗、解析、规范化、相似度计算
8. 分析服务返回多维指标、风险等级、证据
9. 后端保存 AnalysisResult 和 Evidence
10. 前端查询并展示结果
```

### 6.2 题目复杂度数据流

```text
题目文本 / 输入输出 / 约束 / 参考答案
→ feature_extractor
→ difficulty_scorer
→ template_risk_scorer
→ natural_similarity_scorer
→ threshold_calculator
→ ProblemFeature 保存
→ Result 页面展示
```

### 6.3 证据输出数据流

```text
代码对
→ token alignment
→ AST sequence alignment
→ identifier mapping
→ snippet locator
→ evidence builder
→ Evidence 表
→ 前端 EvidenceDetailView
```

### 6.4 实验数据流

```text
experiment/datasets
→ experiment configs
→ baseline runners
→ PICAS runner
→ metric calculator
→ CSV/JSON results
→ plots
→ frontend dashboard
→ paper tables
```

---

## 7. 数据存储架构

### 7.1 MySQL

生产 profile 使用 MySQL 8；本地与测试 profile 使用 H2 file/memory 的 MySQL compatibility mode，并执行同一套 Flyway 迁移。业务服务通过 Spring JDBC Repository 持久化：

```text
user
question
problem_feature
submission
detection_task
analysis_result
evidence
experiment_run
experiment_result
similarity_metric
threshold_adjustment
identifier_mapping
report_file
```

### 7.2 Redis

用途：

```text
任务状态缓存
临时进度缓存
接口限流，增强项
重复提交防护，增强项
热点结果缓存，增强项
```

### 7.3 文件系统

用途：

```text
原始代码文件
清洗后代码文件
报告文件
实验数据集
实验输出
图表文件
```

建议目录：

```text
data/
  uploads/
  cleaned/
  artifacts/
    reports/
    experiments/
```

### 7.4 不建议第一阶段引入

```text
MinIO
Elasticsearch
Kafka
复杂对象存储
分布式任务系统
```

除非核心功能稳定，否则不要增加系统复杂度。

---

## 8. API 架构

### 8.1 后端对前端 API

推荐 REST 路径：

```text
GET    /api/health
POST   /api/questions
GET    /api/questions
GET    /api/questions/{id}
PUT    /api/questions/{id}
POST   /api/submissions/upload
GET    /api/submissions/question/{questionId}
POST   /api/tasks
GET    /api/tasks
GET    /api/tasks/{id}
POST   /api/tasks/{id}/run
GET    /api/results/task/{taskId}
GET    /api/results/{resultId}
GET    /api/results/{resultId}/evidence
GET    /api/reports/{resultId}/markdown
GET    /api/experiments
GET    /api/experiments/{id}
```

### 8.2 后端对分析服务 API

```text
GET  /health
POST /analyze/pair
POST /analyze/task
POST /problem/score
POST /experiment/run
```

### 8.3 分析服务响应原则

所有分析响应必须包含：

```text
success
error_code
message
analysis_version
config_version
result
```

---

## 9. 分析服务核心接口

### 9.1 代码对分析请求

```json
{
  "question": {
    "id": 1,
    "title": "Array Sum",
    "description": "...",
    "input_format": "...",
    "output_format": "...",
    "constraints": "..."
  },
  "submission_a": {
    "id": 101,
    "language": "java",
    "code": "..."
  },
  "submission_b": {
    "id": 102,
    "language": "java",
    "code": "..."
  },
  "config": {
    "enable_canonicalization": true,
    "enable_problem_aware_threshold": true,
    "enable_cross_language_ir": false
  }
}
```

### 9.2 代码对分析响应

```json
{
  "success": true,
  "analysis_version": "0.1.0",
  "result": {
    "token_similarity": 0.86,
    "ast_similarity": 0.81,
    "identifier_mapping_similarity": 0.93,
    "weighted_similarity_score": 0.94,
    "dynamic_threshold": 0.82,
    "risk_margin": 0.12,
    "calibrated_risk_score": 0.80,
    "exceed_threshold": true,
    "risk_level": "HIGH",
    "problem_features": {
      "difficulty_score": 0.42,
      "solution_space_score": 0.35,
      "template_risk_score": 0.72,
      "natural_similarity_risk": 0.68
    },
    "evidence": []
  }
}
```

---

## 10. 算法架构

### 10.1 Pipeline

```text
Input Code Pair
→ Language Detection
→ Code Cleaning
→ Token Extraction
→ AST Parsing
→ Identifier Normalization
→ Canonical Representation
→ Similarity Calculation
→ Problem Feature Scoring
→ Dynamic Threshold Calculation
→ Risk Fusion
→ Evidence Extraction
→ Report Output
```

### 10.2 Similarity Engine

模块：

```text
TokenSimilarityEngine
ASTSimilarityEngine
IdentifierMappingEngine
ControlFlowSimilarityEngine，增强
DataDependencySimilarityEngine，增强
RareFragmentSimilarityEngine，增强
RiskFusionEngine
```

### 10.3 Problem Scoring Engine

模块：

```text
ProblemFeatureExtractor
DifficultyScorer
SolutionSpaceScorer
TemplateRiskScorer
NaturalSimilarityScorer
DynamicThresholdCalculator
```

### 10.4 Evidence Engine

模块：

```text
SnippetLocator
IdentifierMappingEvidenceBuilder
ASTEvidenceBuilder
ControlStructureEvidenceBuilder
RareFragmentEvidenceBuilder
ReviewSuggestionBuilder
```

---

## 11. 任务调度架构

### 11.1 第一阶段

采用简单同步或半异步模式：

```text
前端创建任务
后端保存任务
后端调用分析服务
分析完成后保存结果
```

适合小规模 demo。

### 11.2 第二阶段

引入异步任务：

```text
任务创建
任务入队
后台 worker 执行
更新进度
前端轮询状态
```

实现方式：

```text
Spring @Async
数据库任务状态
Redis 进度缓存，可选
```

### 11.3 不建议过早引入

```text
RabbitMQ
Kafka
Celery
分布式调度
```

除非检测任务规模明显增大。

---

## 12. 前端架构

### 12.1 页面结构

```text
/dashboard                    项目首页
/questions                    题目列表
/questions/create             创建题目
/questions/:id                题目详情与复杂度分析
/tasks                        检测任务列表
/tasks/create                 创建检测任务
/tasks/:id                    任务详情与进度
/results/task/:taskId         结果总览
/results/:resultId            代码对比与证据详情
/experiments                  实验看板
```

### 12.2 核心组件

```text
ProblemScorePanel             展示题目复杂度
DynamicThresholdCard          展示阈值计算解释
SimilarityRadar               展示多维相似度
CodeCompareEditor             左右代码对比
EvidenceList                  证据列表
IdentifierMappingTable        变量映射表
RiskLevelTag                  风险等级标签
ExperimentMetricChart         实验图表
```

### 12.3 前端原则

1. 不在前端计算核心风险分数；
2. 不用 mock 数据冒充真实结果；
3. mock 数据必须标注；
4. 重点展示动态阈值和证据链；
5. 优先保证代码对比页质量。

---

## 13. 部署架构

### 13.1 开发模式

```text
MySQL + Redis via Docker Compose
Spring Boot 本地运行
FastAPI 本地运行
Vue 本地运行
```

### 13.2 答辩模式

```text
docker-compose 启动 MySQL/Redis
后端打包运行
分析服务运行
前端 build 后由 Nginx 或 Vite preview 提供
准备 demo 数据
```

### 13.3 实验模式

```text
analysis-service-python 单独运行实验脚本
读取 experiment/datasets
输出 experiment/runs
生成 plots 和 reports
```

### 13.4 Docker Compose 服务

最小：

```text
mysql
redis
```

增强：

```text
backend
analysis-service
frontend
nginx
```

---

## 14. 安全架构

### 14.1 文件上传安全

必须实现：

1. 文件后缀白名单；
2. 文件大小限制；
3. 上传路径隔离；
4. 文件名随机化；
5. 防止路径穿越；
6. 不执行上传代码。

### 14.2 API 安全

第一阶段可简化，但至少应有：

1. 统一错误响应；
2. 基础登录或开发 token；
3. 上传接口限制；
4. 任务访问校验。

### 14.3 代码执行原则

本系统只分析代码文本，不运行用户代码。

严禁：

```text
exec
subprocess 执行上传代码
在线编译用户代码
运行未知脚本
```

除非后续建立沙箱，否则不得执行。

---

## 15. 错误处理架构

### 15.1 后端统一响应

```json
{
  "success": false,
  "code": "SUBMISSION_PARSE_FAILED",
  "message": "Python parser failed at line 12",
  "data": null
}
```

### 15.2 常见错误码

```text
QUESTION_NOT_FOUND
SUBMISSION_NOT_FOUND
TASK_NOT_FOUND
FILE_TYPE_NOT_SUPPORTED
FILE_TOO_LARGE
ANALYSIS_SERVICE_UNAVAILABLE
PARSER_FAILED
ANALYSIS_FAILED
RESULT_NOT_FOUND
EXPERIMENT_FAILED
```

### 15.3 分析失败策略

1. 单个代码解析失败，记录该提交失败；
2. 单个代码对分析失败，记录 pair 失败；
3. 不因单个失败终止整个任务；
4. 前端展示失败原因；
5. 实验中记录失败样本。

---

## 16. 配置架构

### 16.1 后端配置

```yaml
coderisk:
  upload:
    max-file-size-mb: 2
    allowed-extensions: [".java", ".py", ".c", ".cpp"]
  analysis:
    base-url: "http://localhost:8001"
    timeout-seconds: 60
  report:
    output-dir: "data/reports"
```

### 16.2 分析服务配置

```yaml
similarity:
  token_weight: 0.30
  ast_weight: 0.30
  identifier_weight: 0.20
  rare_fragment_weight: 0.20

threshold:
  base_threshold: 0.80
  natural_similarity_weight: 0.08
  template_risk_weight: 0.06
  difficulty_weight: 0.05
  solution_space_weight: 0.05
```

所有权重必须可配置。

---

## 17. 实验架构

### 17.1 目录

```text
experiment/
  datasets/v4-ready/cases.json
  baselines/jplag/
  build_v4_ready_dataset.py
  run_minimal_v3.py
configs/experiments/minimal_v3.json
data/artifacts/experiments/<run-id>/
```

### 17.2 实验配置

```json
{
  "experiment_name": "dynamic_threshold_ablation",
  "dataset": "assignment_clone_v1",
  "methods": ["token", "ast", "fixed_threshold", "picas"],
  "metrics": ["precision", "recall", "f1", "fpr", "fnr"],
  "config_version": "0.1.0"
}
```

### 17.3 结果输出

```text
metrics.csv
pair_results.csv
config.json
summary.md
plots/*.png
```

---

## 18. 可观测性与日志

### 18.1 后端日志字段

```text
task_id
question_id
submission_id
result_id
request_id
elapsed_ms
status
error_code
```

### 18.2 分析服务日志字段

```text
analysis_id
language_a
language_b
parser_status
token_count_a
token_count_b
ast_node_count_a
ast_node_count_b
elapsed_ms
```

### 18.3 最低监控

1. 后端健康检查；
2. 分析服务健康检查；
3. 任务成功/失败数量；
4. 平均分析时间；
5. 解析失败样本数量。

---

## 19. 扩展策略

### 19.1 新增语言

新增语言时需要：

1. 添加 parser；
2. 添加 token extractor；
3. 添加 identifier normalizer；
4. 添加 AST node mapping；
5. 添加测试样例；
6. 更新文档。

### 19.2 新增相似度指标

新增指标时需要：

1. 独立模块；
2. 独立配置权重；
3. 单元测试；
4. 消融实验开关；
5. 前端展示字段。

### 19.3 新增实验方法

新增实验时需要：

1. 配置文件；
2. 数据集说明；
3. 运行脚本；
4. 输出结果；
5. 图表生成；
6. 失败样本记录。

---

## 20. 架构验收清单

```text
[ ] 前端、后端、分析服务职责清晰
[ ] 后端不承担复杂算法
[ ] 前端不计算风险分数
[ ] 分析服务不管理用户权限
[ ] 代码上传安全可控
[ ] 分析服务可单独测试
[ ] 实验脚本可单独运行
[ ] 配置项没有硬编码
[ ] 结果可以追溯到代码对和题目
[ ] 证据可以定位到代码行
[ ] 动态阈值可以解释
[ ] mock 数据不会冒充真实结果
```

---

## 21. 当前建议实现顺序

```text
1. 创建 backend-springboot / analysis-service-python / frontend-vue 三个工程
2. 建立 MySQL 表结构雏形
3. 实现健康检查和基础联调
4. 实现题目和上传接口
5. 实现分析服务 token similarity
6. 实现结果保存和前端展示
7. 再进入 AST、规范化、动态阈值
```

## 22. V4 实验隔离层

`analysis-service-python/app/analyzers/normalized_ir.py` 与 `lightweight_summaries.py` 仅由 PICAS_CROSSLANG 调用。前者输出有限节点序列，后者输出控制/数据摘要字典；两者均不执行代码、不构建 CFG/DFG 图。

Spring Boot 继续通过通用 similarity_metric/evidence 表保存实验数据，三个 CROSSLANG 指标权重固定为 0。Vue 与 HTML 报告读取同一 API 数据并展示 EXPERIMENTAL 标记。PICAS_STANDARD 调用路径不依赖该实验层。
