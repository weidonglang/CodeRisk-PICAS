# Research V4 Data Collection Guide

本文档说明 Research V4 后续应该如何补充真实或半真实样例。当前 `coderisk-research-v4-seed-1.0` 只是 synthetic seed scaffold：它用于验证校验、校准、JPlag 对齐、实验 runner 和论文表格流程，不是正式 benchmark。

## 1. 要收集哪些数据

优先收集能够支撑 PICAS 两条主线的数据：

1. 题目感知动态阈值：独立实现、自然相似、模板题、简单题和复杂题的对比样例。
2. 置换不变规范化：变量名、函数名、参数名、格式注释、局部重排、函数拆分合并等变换样例。
3. V4 experimental 边界：跨语言改写、common structure 误报探针、unsupported syntax 漏报探针。
4. 外部基线对齐：Java-Java 或 Python-Python 同语言样例，便于 JPlag 输出与 `pair_id` 对齐。

推荐 problem_type：

```text
simple_io
array_loop
sort_template
string_processing
dfs_graph
bfs_graph
dp_variant
simulation
```

推荐 case_type：

```text
INDEPENDENT_SOLUTION
NATURAL_TEMPLATE
VARIABLE_RENAME
FUNCTION_RENAME
PARAMETER_RENAME
FORMAT_COMMENT_CHANGE
LOCAL_REORDER
SPLIT_MERGE
COMMON_STRUCTURE
UNSUPPORTED_SYNTAX
CROSSLANG_REWRITE
HUMAN_REWRITE
AI_REWRITE
```

## 2. 数据放在哪里

所有代码文件必须放在 `experiment/datasets/research-v4/samples/` 下，路径不能逃出该目录。

```text
experiment/datasets/research-v4/
  pairs/
    manual_pairs.json
  samples/
    manual/          手工收集或人工改写，可追溯授权
    ai_assisted/     AI 辅助改写，必须有模型、prompt 和人工/功能验证
    external/        公开或外部授权数据，必须记录来源和许可证
    synthetic/       后续新增的流程测试合成样例
    placeholders/    占位样例，只能 exploratory，不能进入核心指标
    seed/            已生成 synthetic seed，不要当成真实 benchmark
  templates/
```

推荐每个问题单独建目录：

```text
samples/manual/P-MANUAL-001/
  A.java
  B.java
  README.md
```

## 3. 每个样例需要准备的信息

每个 pair 至少需要：

```text
pair_id
problem_id
problem_type
problem_group
dataset_split
split_preregistered
source_id
experiment_label
case_type
language_a
language_b
code_a_path
code_b_path
question.title
question.description
provenance.source
provenance.license_or_authorization
notes
```

脚本会自动计算：

```text
language
data_origin
synthetic
eligible_for_core_metrics
code_a_sha256
code_b_sha256
```

但你仍需要人工确认标签、题目、来源和授权。

## 4. source_type 区别

| source_type | 含义 | 能否进入核心指标 |
|---|---|---|
| `manual` | 人工收集、人工改写或人工标注样例 | 可以，前提是授权、标签和 split 已确认 |
| `synthetic` | 明确由脚本或人工构造的合成流程样例 | 可以用于流程验证；论文正式结论需谨慎 |
| `ai_assisted` | 使用 AI 辅助改写后人工验证的样例 | 只有 provenance 完整且功能验证通过后才可以 |
| `external` | 公开数据或外部授权数据 | 可以，必须记录许可证、链接或本地来源说明 |
| `placeholder` | 占位、未验证或未完成样例 | 不能进入核心指标，只能 exploratory |

`placeholder` 必须同时满足：

```text
synthetic=true
eligible_for_core_metrics=false
```

不要把 placeholder 当作真实 AI 改写或真实 benchmark 数据。

## 5. 哪些数据可以进入核心实验

可以进入核心指标的样例必须满足：

```text
eligible_for_core_metrics=true
experiment_label != UNCERTAIN
source_type != placeholder
split_preregistered=true
problem/source/hash 不跨 validation/test 泄漏
代码路径存在且 hash 与 manifest 一致
非 synthetic 数据有 license_or_authorization
AI_REWRITE 有模型、prompt、生成时间、人工验证和功能验证
```

只能 exploratory 的样例：

```text
UNCERTAIN 标签
placeholder
未验证 AI 改写
未授权 external 样例
旧 7 个 non-preregistered cross-language case
parser failure / unsupported syntax 探针可进入失败分析，但不应当支撑主效果结论
```

## 6. validation / test 如何划分

Research V4 使用 `validation` 和 `test` 两个 split：

```text
validation: 只用于校准候选参数，例如 dynamic-threshold offset。
test: 参数冻结后只评估一次，用于最终表格。
```

同一道题不能同时出现在 validation 和 test。原因是题目画像本身会影响动态阈值；如果同一题的其他 pair 出现在 validation，中间接触到的题目特征会泄漏到 test，使结果虚高或不可解释。

新增人工数据时，先决定 split，再运行实验。不要看过 test 结果后再调整 split、标签或阈值。

## 7. problem/source/hash-disjoint 是什么

| 规则 | 含义 | 为什么重要 |
|---|---|---|
| problem-disjoint | 同一个 `problem_id` 只允许出现在一个 split | 防止题目画像泄漏 |
| source-disjoint | 同一个 `source_id` 只允许出现在一个 split | 防止同一原始代码家族泄漏 |
| hash-disjoint | 完全相同代码 SHA-256 不能跨 split | 防止重复文件泄漏 |

校验器会自动检查三类泄漏。任一泄漏都会使实验无效，必须先修复。

## 8. 如何避免数据泄漏

1. 为每道题固定一个 `problem_id`，并只放入一个 split。
2. 同一份原始代码衍生出的 rename、format、human rewrite、AI rewrite 使用同一个 `source_id`，并只放入一个 split。
3. 不复制同一代码到 validation 和 test。
4. 不根据 test 表现调整 `dataset_split`、阈值、标签或样例内容。
5. 每次补数据后先运行 validator，再运行实验。
6. 记录 `split_preregistered=true` 表示该 split 在分析前已经确定。

## 9. provenance 记录要求

manual 数据至少记录：

```json
{
  "source": "manual collection by project author",
  "license_or_authorization": "author-created sample for CodeRisk Research V4",
  "manual_check_status": "VERIFIED",
  "functional_check_status": "PASSED"
}
```

external 数据至少记录：

```json
{
  "source": "URL or local source package name",
  "license_or_authorization": "MIT / Apache-2.0 / teacher authorization / public dataset terms",
  "manual_check_status": "VERIFIED",
  "functional_check_status": "PASSED"
}
```

AI-assisted rewrite 额外必须记录：

```json
{
  "model_name": "model name and provider",
  "prompt_template": "the exact rewrite instruction or prompt file name",
  "temperature": 0.2,
  "generation_time": "2026-07-05T12:00:00+08:00",
  "manual_check_status": "VERIFIED",
  "functional_check_status": "PASSED"
}
```

AI-assisted 样例评估的是“辅助改写后是否仍保留异常相似结构”，不是检测代码是否由 AI 生成。

## 10. 当前数据缺口

当前 aggregate：

```text
91 total pairs
85 eligible pairs
87 synthetic source_type
4 placeholder source_type
0 manual
0 verified ai_assisted
0 external
```

当前仍至少缺：

```text
manual: 20 pairs
verified ai_assisted: 8 pairs
external: 8 pairs
```

这些是 real-source coverage gap，不是算法功能缺口。

## 11. 后续优先补什么

第一优先级：manual same-language 数据，服务 JPlag 对齐和 V0-V3 主结论。

```text
Java-Java: VARIABLE_RENAME, FUNCTION_RENAME, PARAMETER_RENAME, FORMAT_COMMENT_CHANGE
Python-Python: NATURAL_TEMPLATE, INDEPENDENT_SOLUTION, COMMON_STRUCTURE
simple_io / sort_template / array_loop / string_processing 各至少 2-3 对
```

第二优先级：verified AI-assisted 数据，服务 exploratory 分析。

```text
AI_REWRITE + TRANSFORMED
每个样例必须记录模型、prompt、生成时间、人工验证和功能验证
不要把未验证样例放入核心指标
```

第三优先级：external 数据，服务外部可信度。

```text
优先 Java-Java 或 Python-Python
记录来源链接、许可证、下载时间或教师授权说明
保持 problem/source/hash disjoint
```

第四优先级：cross-language exploratory 数据。

```text
Java-Python simple_io / array_loop / dfs_graph / dp_variant
COMMON_STRUCTURE 独立同构结构
UNSUPPORTED_SYNTAX: Java lambda, Python generator/comprehension, async 等
```

## 12. 如果先补 20 / 40 / 60 对

先补 20 对，最划算方案：

```text
12 manual same-language: rename/function/parameter/format/natural/independent
4 manual common_structure 或 unsupported_syntax
4 verified ai_assisted 或 external 的小样本
```

先补 40 对，推荐方案：

```text
20 manual: 覆盖所有核心 case_type
8 verified ai_assisted: 每个 AI_REWRITE 都完整 provenance
8 external: 优先同语言，便于 JPlag
4 cross_language_rewrite / unsupported_syntax exploratory
```

先补 60 对，推荐方案：

```text
30 manual: 覆盖 8 类 problem_type，validation/test 各自 problem-disjoint
10 verified ai_assisted: 轻度/中度改写都保留
10 external: 至少 Java 和 Python 各 5 对
10 V4 exploratory: cross_language_rewrite, common_structure, unsupported_syntax
```

## 13. JPlag 对齐优先样例

JPlag 最适合同语言样例：

```text
Java-Java
Python-Python
非 placeholder
非 AI_REWRITE placeholder
非 PARSER_FAILURE / UNSUPPORTED_SYNTAX
eligible_for_core_metrics=true
代码能被 JPlag 解析
```

优先为 JPlag 补：

```text
VARIABLE_RENAME
FUNCTION_RENAME
PARAMETER_RENAME
FORMAT_COMMENT_CHANGE
HUMAN_REWRITE
NATURAL_TEMPLATE
INDEPENDENT_SOLUTION
COMMON_STRUCTURE
```

## 14. common_structure 与 unsupported_syntax

common_structure 误报样例应该是：

```text
两个独立来源代码
同题或相近题型
共享普通 loop/if/return 形态
数据流、边界条件或实现细节不同
experiment_label=INDEPENDENT 或 NATURAL_SIMILAR
case_type=COMMON_STRUCTURE
```

unsupported_syntax 漏报样例应该是：

```text
真实或人工构造的相关实现
包含当前 parser/IR 不完整支持的语法
case_type=UNSUPPORTED_SYNTAX 或 PARSER_FAILURE
notes 写明具体语法
```

这些样例重点服务失败分析和 limitations，不要拿它们包装成 V4 已稳定解决跨语言或语义等价。

## 15. 不允许的做法

```text
不允许把 synthetic seed 包装成真实 benchmark
不允许把 placeholder 计入核心指标
不允许补完 test 后反复调参
不允许无授权收集真实学生代码
不允许把 AI-assisted rewrite 写成 AI 生成代码检测
不允许使用“确认抄袭”“证明作弊”“语义等价已解决”等结论
```
