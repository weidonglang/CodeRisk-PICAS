# API_SPEC.md

> 本文件定义 CodeRisk / PICAS 的 API 规范。接口设计必须服务“题目创建、代码上传、检测任务、结果证据、实验评测、报告导出”的完整闭环。所有接口必须返回结构化结果，禁止只返回裸字符串或不可解释状态。

---

## 1. API 设计目标

### 1.1 核心目标

```text
前后端联调稳定
后端与分析服务边界清晰
检测任务状态可追踪
算法结果可解释
实验结果可复现
报告可导出
```

### 1.2 API 分层

接口分为两类：

```text
External API：前端调用 Spring Boot Backend
Internal API：Spring Boot Backend 调用 Python Analysis Service
```

前端不得直接调用 Python Analysis Service。

---

## 2. 通用约定

### 2.1 Base URL

开发环境：

```text
Frontend -> Backend: http://localhost:8080/api
Backend -> Analysis Service: http://localhost:8010/internal
```

### 2.2 请求格式

普通 JSON 请求：

```http
Content-Type: application/json
```

文件上传请求：

```http
Content-Type: multipart/form-data
```

### 2.3 通用响应结构

所有外部接口统一返回：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {},
  "traceId": "20260617-abcdef"
}
```

失败响应：

```json
{
  "success": false,
  "code": "TASK_NOT_FOUND",
  "message": "Detection task not found",
  "data": null,
  "traceId": "20260617-abcdef"
}
```

### 2.4 分页响应结构

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 128,
  "totalPages": 7
}
```

### 2.5 时间格式

统一使用 ISO-like 字符串：

```text
2026-06-17T10:30:00
```

### 2.6 认证方式

V1 可简化为开发模式免登录。正式版推荐：

```http
Authorization: Bearer <jwt-token>
```

---

## 3. 错误码规范

### 3.1 通用错误码

```text
OK
BAD_REQUEST
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
VALIDATION_ERROR
INTERNAL_ERROR
SERVICE_UNAVAILABLE
```

### 3.2 业务错误码

```text
QUESTION_NOT_FOUND
SUBMISSION_NOT_FOUND
TASK_NOT_FOUND
RESULT_NOT_FOUND
EVIDENCE_NOT_FOUND
EXPERIMENT_NOT_FOUND
REPORT_NOT_FOUND
```

### 3.3 文件错误码

```text
FILE_EMPTY
FILE_TOO_LARGE
FILE_TYPE_NOT_SUPPORTED
FILE_SAVE_FAILED
FILE_NOT_FOUND
INVALID_FILE_PATH
```

### 3.4 分析错误码

```text
ANALYSIS_SERVICE_UNAVAILABLE
ANALYSIS_TIMEOUT
PARSE_FAILED
UNSUPPORTED_LANGUAGE
ANALYSIS_RESULT_INVALID
```

---

## 4. 用户接口

### 4.1 登录

```http
POST /api/auth/login
```

请求：

```json
{
  "username": "admin",
  "password": "123456"
}
```

响应：

```json
{
  "token": "jwt-token",
  "user": {
    "id": 1,
    "username": "admin",
    "displayName": "管理员",
    "role": "ADMIN"
  }
}
```

### 4.2 当前用户

```http
GET /api/auth/me
```

响应：

```json
{
  "id": 1,
  "username": "admin",
  "displayName": "管理员",
  "role": "ADMIN"
}
```

---

## 5. 题目接口

### 5.1 创建题目

```http
POST /api/questions
```

请求：

```json
{
  "title": "数组中偶数计数",
  "description": "给定一个整数数组，统计其中偶数的个数。",
  "inputFormat": "第一行 n，第二行 n 个整数。",
  "outputFormat": "输出偶数个数。",
  "constraintsText": "1 <= n <= 1000",
  "sampleText": "5\n1 2 3 4 5\n2",
  "manualDifficulty": "EASY"
}
```

响应：

```json
{
  "id": 1001,
  "title": "数组中偶数计数",
  "createdAt": "2026-06-17T10:30:00"
}
```

### 5.2 更新题目

```http
PUT /api/questions/{questionId}
```

请求字段同创建题目。

### 5.3 查询题目详情

```http
GET /api/questions/{questionId}
```

响应：

```json
{
  "id": 1001,
  "title": "数组中偶数计数",
  "description": "给定一个整数数组，统计其中偶数的个数。",
  "inputFormat": "第一行 n，第二行 n 个整数。",
  "outputFormat": "输出偶数个数。",
  "constraintsText": "1 <= n <= 1000",
  "manualDifficulty": "EASY",
  "createdAt": "2026-06-17T10:30:00"
}
```

### 5.4 查询题目列表

```http
GET /api/questions?page=1&pageSize=20&keyword=数组
```

响应 data 为分页结构。

### 5.5 删除题目

```http
DELETE /api/questions/{questionId}
```

逻辑删除。若已有任务，默认不允许物理删除。

---

## 6. 参考答案接口

### 6.1 上传参考答案

```http
POST /api/questions/{questionId}/reference-solutions
Content-Type: multipart/form-data
```

表单字段：

```text
file: 代码文件
language: java/python/c
description: 可选说明
```

响应：

```json
{
  "id": 2001,
  "questionId": 1001,
  "language": "java",
  "fileName": "Solution.java",
  "lineCount": 35
}
```

### 6.2 查询参考答案列表

```http
GET /api/questions/{questionId}/reference-solutions
```

### 6.3 删除参考答案

```http
DELETE /api/reference-solutions/{referenceSolutionId}
```

---

## 7. 提交代码接口

### 7.1 上传单个提交

```http
POST /api/questions/{questionId}/submissions
Content-Type: multipart/form-data
```

表单字段：

```text
file: 代码文件
language: java/python/c
submitterId: 可选
submitterAlias: 可选
```

响应：

```json
{
  "id": 3001,
  "questionId": 1001,
  "language": "python",
  "fileName": "student_01.py",
  "fileSizeBytes": 1024,
  "codeHash": "sha256:xxxx",
  "parseStatus": "PENDING"
}
```

### 7.2 批量上传提交

```http
POST /api/questions/{questionId}/submissions/batch
Content-Type: multipart/form-data
```

表单字段：

```text
files: 多个代码文件
languageMode: AUTO / MANUAL
language: 若 MANUAL 则必填
```

响应：

```json
{
  "questionId": 1001,
  "uploadedCount": 20,
  "failedCount": 1,
  "items": [
    {
      "fileName": "A.java",
      "submissionId": 3001,
      "success": true
    },
    {
      "fileName": "bad.exe",
      "success": false,
      "errorCode": "FILE_TYPE_NOT_SUPPORTED"
    }
  ]
}
```

### 7.3 查询提交列表

```http
GET /api/questions/{questionId}/submissions?page=1&pageSize=50&language=java
```

### 7.4 查询提交代码内容

```http
GET /api/submissions/{submissionId}/code?type=raw
```

`type` 可取：

```text
raw
clean
canonical
```

响应：

```json
{
  "submissionId": 3001,
  "fileName": "A.java",
  "language": "java",
  "code": "public class A { ... }"
}
```

---

## 8. 题目复杂度评分接口

### 8.1 触发题目评分

```http
POST /api/questions/{questionId}/features/compute
```

请求：

```json
{
  "featureVersion": "pf-v1.0",
  "useReferenceSolution": true,
  "useHistoricalDistribution": false
}
```

响应：

```json
{
  "questionId": 1001,
  "featureVersion": "pf-v1.0",
  "difficultyScore": 0.25,
  "solutionSpaceScore": 0.20,
  "templateRiskScore": 0.65,
  "naturalSimilarityRisk": 0.78,
  "recommendedBaseThreshold": 0.86
}
```

### 8.2 查询题目特征

```http
GET /api/questions/{questionId}/features/latest
```

响应：

```json
{
  "questionId": 1001,
  "featureVersion": "pf-v1.0",
  "difficultyScore": 0.25,
  "solutionSpaceScore": 0.20,
  "templateRiskScore": 0.65,
  "naturalSimilarityRisk": 0.78,
  "recommendedBaseThreshold": 0.86,
  "explanation": {
    "naturalSimilarityReasons": ["题目输入输出简单", "参考答案结构短"],
    "templateRiskReasons": ["存在固定循环计数模板"]
  }
}
```

---

## 9. 检测任务接口

### 9.1 创建检测任务

```http
POST /api/tasks
```

请求：

```json
{
  "questionId": 1001,
  "taskName": "第 1 次作业查重",
  "taskMode": "PICAS_STANDARD",
  "submissionIds": [3001, 3002, 3003, 3004],
  "config": {
    "enableCanonicalization": true,
    "enableProblemAwareThreshold": true,
    "enableRareFragment": true,
    "maxEvidencePerPair": 20
  }
}
```

响应：

```json
{
  "taskId": 4001,
  "status": "PENDING",
  "totalSubmissions": 4,
  "totalPairs": 6
}
```

### 9.2 启动检测任务

```http
POST /api/tasks/{taskId}/start
```

响应：

```json
{
  "taskId": 4001,
  "status": "QUEUED"
}
```

### 9.3 查询任务状态

```http
GET /api/tasks/{taskId}
```

响应：

```json
{
  "id": 4001,
  "questionId": 1001,
  "taskName": "第 1 次作业查重",
  "taskMode": "PICAS_STANDARD",
  "status": "RUNNING",
  "progress": 0.50,
  "totalPairs": 6,
  "finishedPairs": 3,
  "failedPairs": 0,
  "startedAt": "2026-06-17T10:40:00",
  "finishedAt": null
}
```

### 9.4 查询任务列表

```http
GET /api/tasks?page=1&pageSize=20&questionId=1001&status=FINISHED
```

### 9.5 取消任务

```http
POST /api/tasks/{taskId}/cancel
```

V1 可仅设置取消标记，不强制终止分析进程。

### 9.6 删除任务

```http
DELETE /api/tasks/{taskId}
```

逻辑删除，不删除原始代码和报告文件。

---

## 10. 检测结果接口

所有外部响应必须包裹在 `ApiResponse<T>` 中。以下示例仅展示 `data` 内部对象。

### 10.1 查询任务结果总览

```http
GET /api/tasks/{taskId}/results?page=1&pageSize=20&riskLevel=HIGH&sort=riskMargin,desc
```

响应 data：

```json
{
  "items": [
    {
      "id": 5001,
      "taskId": 4001,
      "submissionAId": 3001,
      "submissionBId": 3002,
      "submissionAFileName": "A.java",
      "submissionBFileName": "B.java",
      "tokenSimilarity": 0.86,
      "astSimilarity": 0.89,
      "canonicalTokenSimilarity": 0.93,
      "identifierMappingSimilarity": 0.60,
      "weightedSimilarityScore": 0.94,
      "dynamicThreshold": 0.82,
      "riskMargin": 0.12,
      "calibratedRiskScore": 0.80,
      "riskLevel": "HIGH",
      "exceedThreshold": true,
      "marginScale": 0.40,
      "formulaVersion": "FORMULA_SPEC_V1",
      "algorithmVersion": "picas-v2-rule-1.0",
      "metricConfigHash": "sha256:...",
      "reasonSummary": "变量名不同但循环、条件和边界处理结构高度一致，建议人工复核。",
      "isMock": false,
      "createdAt": "2026-06-20T14:30:00+08:00"
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 12,
  "totalPages": 1
}
```

### 10.2 查询单个结果详情

```http
GET /api/results/{resultId}
```

响应 data：

```json
{
  "id": 5001,
  "taskId": 4001,
  "submissionAId": 3001,
  "submissionBId": 3002,
  "submissionAFileName": "A.java",
  "submissionBFileName": "B.java",
  "weightedSimilarityScore": 0.94,
  "tokenSimilarity": 0.86,
  "astSimilarity": 0.89,
  "canonicalTokenSimilarity": 0.93,
  "identifierMappingSimilarity": 0.60,
  "dynamicThreshold": 0.82,
  "riskMargin": 0.12,
  "calibratedRiskScore": 0.80,
  "riskLevel": "HIGH",
  "exceedThreshold": true,
  "marginScale": 0.40,
  "formulaVersion": "FORMULA_SPEC_V1",
  "algorithmVersion": "picas-v2-rule-1.0",
  "metricConfigHash": "sha256:...",
  "thresholdAdjustment": {
    "baseThreshold": 0.80,
    "difficultyAdjustment": -0.03,
    "templateRiskAdjustment": 0.04,
    "naturalSimilarityAdjustment": 0.01,
    "finalThreshold": 0.82,
    "formulaVersion": "FORMULA_SPEC_V1"
  },
  "problemProfile": {
    "featureVersion": "pf-rule-v1.0",
    "difficultyScore": 0.25,
    "solutionSpaceScore": 0.20,
    "templateRiskScore": 0.65,
    "naturalSimilarityRisk": 0.78,
    "recommendedBaseThreshold": 0.82,
    "confidence": 0.78
  },
  "reasonSummary": "该代码对超过动态阈值，且存在多条高置信结构证据，建议人工复核。",
  "isMock": false,
  "createdAt": "2026-06-20T14:30:00+08:00"
}
```

分项指标通过 `GET /api/results/{resultId}/metrics` 单独返回，不在结果详情中重复嵌套。外部字段统一 camelCase；数据库与 Python 内部字段统一 snake_case。

当前 V1/V1.5 实现说明：`astSimilarity` 为基础 AST 节点类型序列相似度；解析失败时返回 0，并通过 `PARSER_WARNING` evidence 标记降级。`canonicalTokenSimilarity` 为标识符归一化后的 token 相似度，`identifierMappingSimilarity` 用于辅助展示变量/函数名映射，不直接给出纪律结论。

### 10.3 查询相似度分项指标

```http
GET /api/results/{resultId}/metrics
```

### 10.4 查询动态阈值解释

```http
GET /api/results/{resultId}/threshold-adjustment
```

响应 data：

```json
{
  "baseThreshold": 0.80,
  "difficultyAdjustment": -0.03,
  "solutionSpaceAdjustment": -0.02,
  "templateRiskAdjustment": 0.04,
  "naturalSimilarityAdjustment": 0.03,
  "historicalDistributionAdjustment": 0.00,
  "finalThreshold": 0.82,
  "formulaVersion": "FORMULA_SPEC_V1",
  "explanation": "题目自然相似风险较高，因此提高阈值；题目存在一定复杂度，因此轻微降低阈值。"
}
```

---

## 11. 证据接口

### 11.1 查询证据列表

```http
GET /api/results/{resultId}/evidence?type=AST_STRUCTURE_MATCH&page=1&pageSize=20
```

响应：

```json
{
  "items": [
    {
      "id": 6001,
      "evidenceType": "AST_STRUCTURE_MATCH",
      "confidence": 0.92,
      "similarityScore": 0.89,
      "codeAStartLine": 12,
      "codeAEndLine": 22,
      "codeBStartLine": 10,
      "codeBEndLine": 20,
      "title": "循环-条件-累加结构相似",
      "description": "两份代码在核心循环中均包含取模判断与计数器累加结构。",
      "visualizable": true
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 8,
  "totalPages": 1
}
```

### 11.2 查询证据详情

```http
GET /api/evidence/{evidenceId}
```

响应：

```json
{
  "id": 6001,
  "evidenceType": "AST_STRUCTURE_MATCH",
  "confidence": 0.92,
  "similarityScore": 0.89,
  "codeASnippet": "for (int x : arr) { ... }",
  "codeBSnippet": "for (int y : nums) { ... }",
  "payload": {
    "astNodeType": "FOR_STATEMENT",
    "operationSignature": "ITERATE_SEQUENCE->MOD_CHECK->COUNTER_INCREMENT"
  }
}
```

### 11.3 查询标识符映射

```http
GET /api/results/{resultId}/identifier-mappings
```

响应：

```json
[
  {
    "mappingType": "VARIABLE",
    "nameA": "sum",
    "nameB": "result",
    "canonicalName": "VAR_1",
    "confidence": 0.95
  }
]
```

---

## 12. 代码对比接口

### 12.1 查询代码对比数据

```http
GET /api/results/{resultId}/diff-view
```

响应：

```json
{
  "resultId": 4001,
  "taskId": 3001,
  "codeA": {
    "submissionId": 2001,
    "fileName": "A.java",
    "language": "java",
    "code": "public class A { ... }"
  },
  "codeB": {
    "submissionId": 2002,
    "fileName": "B.java",
    "language": "java",
    "code": "public class B { ... }"
  },
  "highlights": [
    {
      "evidenceId": 6001,
      "type": "AST_STRUCTURE_MATCH",
      "aRange": {"startLine": 12, "endLine": 22},
      "bRange": {"startLine": 10, "endLine": 20},
      "confidence": 0.92
    }
  ]
}
```

V1 当前实现先返回 token evidence 对应的基础行号高亮；后续接入 AST、canonical token 和 Monaco Editor 后，`highlights.type` 会继续复用证据类型扩展。

---

## 13. 报告接口

### 13.1 导出检测报告

```http
POST /api/tasks/{taskId}/reports
```

请求：

```json
{
  "format": "HTML",
  "includeLowRiskPairs": false,
  "includeCodeSnippets": true,
  "includeThresholdExplanation": true
}
```

响应：

```json
{
  "reportId": 7001,
  "taskId": 4001,
  "status": "GENERATED",
  "format": "HTML",
  "fileName": "task-4001-report.html",
  "downloadUrl": "/api/reports/7001/download",
  "createdAt": "2026-06-20T13:30:00+08:00"
}
```

V2 首个稳定格式为 `HTML`。报告文件写入 artifacts 目录，元数据和 SHA-256 保存到 `report_file`。

### 13.2 查询任务报告

```http
GET /api/tasks/{taskId}/reports
```

返回该任务已生成报告列表。

### 13.3 下载报告

```http
GET /api/reports/{reportId}/download
```

返回文件流。

---

## 14. 实验数据集接口

### 14.1 创建实验数据集

```http
POST /api/experiments/datasets
```

请求：

```json
{
  "datasetName": "PICAS-Obfuscation-Set",
  "datasetVersion": "v1.0",
  "datasetType": "SYNTHETIC_OBFUSCATION",
  "description": "包含变量改名、函数改名、格式化、局部换序、AI 改写的实验集。"
}
```

### 14.2 查询数据集列表

```http
GET /api/experiments/datasets?page=1&pageSize=20
```

### 14.3 查询实验样本

```http
GET /api/experiments/datasets/{datasetId}/cases?page=1&pageSize=50&level=L1_RENAME_VARIABLE
```

---

## 15. 实验运行接口

### 15.1 创建实验运行

```http
POST /api/experiments/runs
```

请求：

```json
{
  "datasetId": 8001,
  "runName": "PICAS 标准方法 v1",
  "methodName": "PICAS_STANDARD",
  "methodVersion": "alg-v1.0",
  "config": {
    "enableProblemAwareThreshold": true,
    "enableCanonicalization": true,
    "enableRareFragment": true
  }
}
```

响应：

```json
{
  "runId": 9001,
  "status": "PENDING"
}
```

### 15.2 启动实验运行

```http
POST /api/experiments/runs/{runId}/start
```

### 15.3 查询实验运行状态

```http
GET /api/experiments/runs/{runId}
```

### 15.4 查询实验汇总结果

```http
GET /api/experiments/runs/{runId}/summary
```

响应：

```json
{
  "runId": 9001,
  "methodName": "PICAS_STANDARD",
  "overall": {
    "precision": 0.91,
    "recall": 0.88,
    "f1": 0.895,
    "falsePositiveRate": 0.06,
    "falseNegativeRate": 0.12,
    "averageRuntimeMs": 38.2
  },
  "byObfuscationLevel": [
    {"level": "L1_RENAME_VARIABLE", "precision": 0.94, "recall": 0.93, "f1": 0.935},
    {"level": "L8_AI_REWRITE", "precision": 0.84, "recall": 0.76, "f1": 0.798}
  ]
}
```

### 15.5 导出实验报告

```http
POST /api/experiments/runs/{runId}/reports
```

### 15.6 查询最新可复现实验产物

```http
GET /api/experiments/latest
```

V3 minimal 实现从 `data/artifacts/experiments/latest.json` 读取最近一次真实脚本运行，返回 run metadata、E1-E5 汇总和 Markdown 报告路径。该接口不生成 mock 指标。

---

## 16. 配置接口

`API_SPEC.md` 是外部接口唯一真源。枚举定义以 `ENUMS.md` 为准。

### 16.1 查询支持语言

```http
GET /api/system/languages
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "traceId": "trace-20260617-0001",
  "data": [
    {"code": "java", "name": "Java", "supportLevel": "STABLE"},
    {"code": "python", "name": "Python", "supportLevel": "STABLE"},
    {"code": "c", "name": "C", "supportLevel": "EXPERIMENTAL"}
  ]
}
```

前端必须显示“C：实验性支持”，不得显示为稳定能力。

### 16.2 查询检测模式

```http
GET /api/system/task-modes
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "traceId": "trace-20260617-0002",
  "data": [
    {"code": "BASIC_TOKEN", "name": "基础 Token 检测", "version": "V1", "stable": true},
    {"code": "TOKEN_AST", "name": "Token + 基础 AST 检测", "version": "V1", "stable": true},
    {"code": "PICAS_INVARIANT", "name": "置换不变规范化检测", "version": "V1.5", "stable": true},
    {"code": "PICAS_STANDARD", "name": "PICAS 标准检测", "version": "V2", "stable": true},
    {"code": "PICAS_CROSSLANG", "name": "跨语言 IR 检测", "version": "V4", "stable": false},
    {"code": "PICAS_EXPERIMENTAL", "name": "实验/消融检测", "version": "V3/V4", "stable": false}
  ]
}
```

---

## 17. Internal Analysis Service API

以下接口仅允许后端调用。

### 17.1 健康检查

```http
GET /internal/health
```

响应：

```json
{
  "status": "UP",
  "version": "analysis-v1.0",
  "supportedLanguages": ["java", "python", "c"]
}
```

### 17.2 分析单个任务

```http
POST /internal/analyze/task
```

请求：

```json
{
  "taskId": 4001,
  "question": {
    "id": 1001,
    "title": "数组中偶数计数",
    "description": "给定一个整数数组，统计其中偶数的个数。",
    "inputFormat": "第一行 n，第二行 n 个整数。",
    "outputFormat": "输出偶数个数。",
    "constraintsText": "1 <= n <= 1000"
  },
  "referenceSolutions": [
    {
      "id": 2001,
      "language": "java",
      "rawCodePath": "/data/uploads/reference/2001.java",
      "cleanCodePath": "/data/uploads/reference/2001.clean.java"
    }
  ],
  "submissions": [
    {
      "id": 3001,
      "language": "java",
      "rawCodePath": "/data/uploads/submissions/3001.java",
      "cleanCodePath": "/data/uploads/submissions/3001.clean.java"
    },
    {
      "id": 3002,
      "language": "python",
      "rawCodePath": "/data/uploads/submissions/3002.py",
      "cleanCodePath": "/data/uploads/submissions/3002.clean.py"
    }
  ],
  "config": {
    "mode": "PICAS_STANDARD",
    "enableCanonicalization": true,
    "enableProblemAwareThreshold": true,
    "maxEvidencePerPair": 20
  }
}
```

响应：

```json
{
  "taskId": 4001,
  "status": "FINISHED",
  "problemFeature": {
    "featureVersion": "pf-v1.0",
    "difficultyScore": 0.25,
    "solutionSpaceScore": 0.20,
    "templateRiskScore": 0.65,
    "naturalSimilarityRisk": 0.78,
    "recommendedBaseThreshold": 0.86,
    "explanation": {}
  },
  "results": [
    {
      "submissionAId": 3001,
      "submissionBId": 3002,
      "languagePair": "java-python",
      "weightedSimilarityScore": 0.76,
      "dynamicThreshold": 0.84,
      "riskMargin": -0.08,
      "calibratedRiskScore": 0.30,
      "riskLevel": "MEDIUM",
      "exceedThreshold": false,
      "marginScale": 0.40,
      "metrics": [],
      "thresholdAdjustment": {},
      "evidence": [],
      "identifierMappings": [],
      "artifacts": []
    }
  ],
  "errors": []
}
```

### 17.3 单独计算题目特征

```http
POST /internal/problem/score
```

### 17.4 单独比较两个提交

```http
POST /internal/analyze/pair
```

用于调试和单元验证。

### 17.5 运行实验任务

```http
POST /internal/experiment/run
```

仅允许 Spring Boot Backend 调用，Frontend 不得直接调用 Python Analysis Service。

---

## 18. API 状态机约束

### 18.1 创建任务后

```text
POST /api/tasks -> PENDING
POST /api/tasks/{id}/start -> QUEUED
分析开始 -> RUNNING
分析成功 -> FINISHED
部分失败 -> PARTIAL
整体失败 -> FAILED
```

### 18.2 前端轮询建议

任务运行中：

```text
GET /api/tasks/{taskId}
```

轮询间隔：

```text
1~3 秒
```

任务完成后再请求：

```text
GET /api/tasks/{taskId}/results
```

---

## 19. API 安全要求

### 19.1 文件上传限制

```text
单文件默认不超过 2 MB
批量上传默认不超过 200 个文件
只允许 .java .py .c .h .cpp .txt
禁止路径穿越文件名
禁止直接执行用户代码
```

### 19.2 权限要求

```text
普通用户只能查看自己的任务
管理员可以查看全部任务
实验管理接口默认仅管理员开放
报告下载需要权限校验
```

V1 可简化权限，但接口设计应保留扩展空间。

---

## 20. API 验收标准

接口完成后必须满足：

```text
1. 能创建题目。
2. 能上传参考答案和提交代码。
3. 能创建并启动检测任务。
4. 能查询任务进度。
5. 能查询结果总览。
6. 能查询单个代码对详情。
7. 能查询多维相似度指标。
8. 能查询动态阈值解释。
9. 能查询结构化证据。
10. 能获取代码对比视图。
11. 能导出检测报告。
12. 能创建实验数据集和实验运行。
13. 能查询实验汇总指标。
14. 后端能调用分析服务完成真实分析。
15. 所有错误返回统一响应格式。
```

---

## 21. 禁止事项

```text
禁止接口返回裸字符串。
禁止前端直接调用 analysis-service。
禁止只返回 similarity 一个字段。
禁止没有 task status 就开始查询结果。
禁止上传接口不限制文件类型和大小。
禁止在接口中出现“抄袭确认”作为系统结论。
禁止把动态阈值解释隐藏在不可解析文本里。
禁止实验结果只返回图片，不返回指标数据。
```

## 22. V4 Phase 1-2 实验响应

当且仅当 config.mode=PICAS_CROSSLANG 时，`/internal/analyze/pair` 可额外返回三个 weight=0 的实验指标：CROSSLANG_IR_SIMILARITY、CROSSLANG_CONTROL_SUMMARY_SIMILARITY、CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY。

对应 evidence 的 metadata 必须包含 experimental=true、includedInWeightedScore=false 和版本字段。控制/数据摘要分别复用 CONTROL_STRUCTURE_MATCH 与 OPERATION_SEQUENCE_MATCH，但必须说明未构建完整 CFG/DFG。解析失败时不得返回这三类结构 evidence。
