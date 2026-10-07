# ENUMS.md

> 本文件是 CodeRisk / PICAS 项目的枚举真源。`API_SPEC.md`、`DATABASE_SCHEMA.md`、`FRONTEND_SPEC.md`、`FRONTEND_TASKS.md`、`UI_FLOW.md`、`CODEX_TASKS.md` 和 `ROADMAP.md` 不得再各自定义另一套后端/数据库/API 真实枚举。

---

## 1. 总原则

1. 后端、数据库、API 和前端类型定义必须使用本文件中的枚举值。
2. 前端可以为枚举提供中文显示标签，但真实请求值、响应值、数据库值不得使用中文或旧枚举。
3. 系统只输出“相似风险”，禁止输出“抄袭成立”“作弊成立”“确认抄袭”等结论性枚举。
4. 新增枚举前必须先更新本文件，再同步修改 API、数据库、前端类型和测试用例。

---

## 2. task_mode

检测模式统一采用：

```text
BASIC_TOKEN
TOKEN_AST
PICAS_INVARIANT
PICAS_STANDARD
PICAS_CROSSLANG
PICAS_EXPERIMENTAL
```

| 枚举值 | 含义 | 版本定位 | 是否正式承诺 |
|---|---|---|---|
| `BASIC_TOKEN` | 只做 token 基础检测 | V1 | 是 |
| `TOKEN_AST` | token + 基础 AST | V1 | 是 |
| `PICAS_INVARIANT` | 加入 canonicalization / 标识符归一化 | V1.5 | 是 |
| `PICAS_STANDARD` | 题目感知 + 动态阈值 + 多维融合，作为主版本 | V2 | 是 |
| `PICAS_CROSSLANG` | 跨语言 IR + lightweight control/data-flow summary | V4 | 否，实验性 |
| `PICAS_EXPERIMENTAL` | 实验、消融、批处理 | V3/V4 | 论文实验使用 |

废弃旧枚举：

```text
BASIC
```

旧枚举不得出现在后端、数据库、API 请求或响应中；如前端需要展示，可作为中文标签来源而不是实际值。

---

## 3. task_status

任务状态统一采用：

```text
PENDING
QUEUED
RUNNING
PARTIAL
FAILED
CANCELLED
FINISHED
```

| 枚举值 | 含义 |
|---|---|
| `PENDING` | 已创建，未入队 |
| `QUEUED` | 已入队 |
| `RUNNING` | 运行中 |
| `PARTIAL` | 部分成功 |
| `FAILED` | 失败 |
| `CANCELLED` | 已取消 |
| `FINISHED` | 完成 |

废弃旧任务状态：

```text
CREATED
SUCCESS
PARTIAL_SUCCESS
COMPLETED
```

说明：前端可以把 `FINISHED` 显示为“成功”或“完成”，但真实值必须是 `FINISHED`。

---

## 4. language_support_level

```text
STABLE
EXPERIMENTAL
DISABLED
```

| 枚举值 | 含义 |
|---|---|
| `STABLE` | 稳定支持，可作为正式交付能力 |
| `EXPERIMENTAL` | 实验性支持，不作为 V0-V2 必交付能力 |
| `DISABLED` | 当前不可用，仅保留展示或未来扩展 |

首期建议：

```json
[
  {"language": "java", "supportLevel": "STABLE"},
  {"language": "python", "supportLevel": "STABLE"},
  {"language": "c", "supportLevel": "EXPERIMENTAL"}
]
```

---

## 5. risk_level

```text
LOW
MEDIUM
ELEVATED
HIGH
```

| 枚举值 | 中文显示 | 含义 |
|---|---|---|
| `LOW` | 低风险 | 当前证据不足以提示明显相似风险 |
| `MEDIUM` | 中风险 | 存在一定相似性，建议查看证据 |
| `ELEVATED` | 较高风险 | 超过动态阈值或接近高风险边界，建议人工复核 |
| `HIGH` | 高风险 | 明显超过动态阈值，必须人工复核 |

禁止使用：

```text
EXTREME
CONFIRMED_PLAGIARISM
```

---

## 6. evidence_type

```text
TOKEN_MATCH
AST_STRUCTURE_MATCH
CANONICAL_TOKEN_MATCH
IDENTIFIER_MAPPING
CONTROL_STRUCTURE_MATCH
OPERATION_SEQUENCE_MATCH
BOUNDARY_PATTERN_MATCH
RARE_FRAGMENT_MATCH
TEMPLATE_COMMON_FRAGMENT
CROSSLANG_IR_MATCH
PARSER_WARNING
REVIEW_NOTE
```

说明：

1. `TEMPLATE_COMMON_FRAGMENT` 用于提示通用模板结构，不应直接提升为高风险结论。
2. `PARSER_WARNING` 用于解析失败、部分解析、降级分析等情况。
3. `REVIEW_NOTE` 用于人工复核备注。

---

## 7. experiment_label

实验样本标签统一采用：

```text
SIMILAR
SUSPICIOUS
TRANSFORMED
INDEPENDENT
NATURAL_SIMILAR
UNCERTAIN
```

| 枚举值 | 含义 |
|---|---|
| `SIMILAR` | 明确构造或标注为相似样本 |
| `SUSPICIOUS` | 可疑相似样本，需人工复核 |
| `TRANSFORMED` | 由原代码通过伪装/变换生成的样本 |
| `INDEPENDENT` | 独立解法样本 |
| `NATURAL_SIMILAR` | 简单题/模板题导致的自然相似样本 |
| `UNCERTAIN` | 标签不确定，不用于核心指标或单独报告 |

禁止使用“确认抄袭”“作弊成立”等标签。

---

## 8. case_type

```text
ORIGINAL_COPY
HUMAN_REWRITE
VARIABLE_RENAME
PARAMETER_RENAME
FUNCTION_RENAME
FORMAT_COMMENT_CHANGE
LOCAL_REORDER
SPLIT_MERGE
CROSSLANG_REWRITE
AI_REWRITE
COMMON_STRUCTURE
UNSUPPORTED_SYNTAX
PARSER_FAILURE
NATURAL_TEMPLATE
INDEPENDENT_SOLUTION
```

| 枚举值 | 含义 |
|---|---|
| `ORIGINAL_COPY` | 原始复制或极小改动 |
| `HUMAN_REWRITE` | 经人工改写且保留可追溯来源关系 |
| `VARIABLE_RENAME` | 变量名替换 |
| `PARAMETER_RENAME` | 参数名替换 |
| `FUNCTION_RENAME` | 函数名替换 |
| `FORMAT_COMMENT_CHANGE` | 格式或注释修改 |
| `LOCAL_REORDER` | 安全的局部无依赖语句重排 |
| `SPLIT_MERGE` | 函数拆分或合并 |
| `CROSSLANG_REWRITE` | 跨语言重写 |
| `AI_REWRITE` | AI 辅助改写 |
| `COMMON_STRUCTURE` | 独立代码共享通用控制结构，用于误报探针 |
| `UNSUPPORTED_SYNTAX` | 包含当前实验解析器不支持的语法 |
| `PARSER_FAILURE` | 语法错误或解析失败降级样例 |
| `NATURAL_TEMPLATE` | 模板或简单题自然相似 |
| `INDEPENDENT_SOLUTION` | 独立解法 |

---

## 9. parser_status

```text
NOT_PARSED
PARSED
PARTIAL
FAILED
FALLBACK_TOKEN_ONLY
```

说明：解析失败时不得伪造 AST、CFG 或 IR 证据；只能输出 token 级降级结果和 `PARSER_WARNING`。

---

## 10. report_status

```text
NOT_GENERATED
GENERATING
GENERATED
FAILED
```

报告文件必须写入 `/data/artifacts/...`，并在数据库中保存 `artifact_path`。

---

## 11. Research dataset source_type

```text
manual
synthetic
ai_assisted
external
placeholder
```

`source_type` 只描述研究数据来源，不改变生产风险含义。`placeholder` 必须同时满足 `synthetic=true` 与 `eligible_for_core_metrics=false`；`ai_assisted` 进入核心指标前必须具备模型/提示词来源、生成时间、人工验证和功能验证。研究 manifest 的规范字段使用 `pair_id` 与 `dataset_split`，兼容旧 shard 的 `case_id`/`split` 时两者必须一致。
