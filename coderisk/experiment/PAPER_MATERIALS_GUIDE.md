# Research V4 Paper Materials Guide

本文档说明如何把 Research V4 输出整理为论文材料。当前 seed 输出只能作为“工具链预实验”和“流程可复现性”材料，不能作为正式 benchmark 结论。

## 1. 可放入论文的输出文件

结果目录：

```text
data/artifacts/experiments/<RUN_ID>/
```

可用表格：

| 文件 | 论文用途 | 当前 seed 阶段说明 |
|---|---|---|
| `paper_tables/table_dataset_statistics.csv` | 数据集统计表 | 可展示 scaffold 构成，但必须标注 synthetic seed |
| `paper_tables/table_fixed_vs_dynamic.csv` | 固定阈值 vs 动态阈值 | 只能预实验，正式效果待真实数据 |
| `paper_tables/table_dynamic_threshold_calibration.csv` | validation-only 校准 | 可证明流程纪律 |
| `paper_tables/table_raw_vs_canonical.csv` | raw vs canonical | 可展示 seed rename 稳定性 |
| `paper_tables/table_fusion.csv` | Token-only / Token+AST / PICAS | 预实验对比 |
| `paper_tables/table_ablation.csv` | NoDT / NoCanon / Full | 预实验消融 |
| `paper_tables/table_cross_language.csv` | V4 experimental matrix | 只能 exploratory |
| `paper_tables/table_baseline_comparison.csv` | JPlag fixed vs PICAS dynamic | seed 对齐流程，不作优劣结论 |
| `case_analysis/failure_cases.csv` | 失败案例 | 必须选入论文 limitations |
| `case_analysis/borderline_cases.csv` | 边界案例 | 用于人工复核讨论 |
| `case_analysis/common_structure_cases.csv` | common structure 误报 | V4 局限 |
| `case_analysis/unsupported_syntax_cases.csv` | unsupported syntax 漏报 | parser/IR 局限 |

## 2. 哪些实验支持 canonical 表示有效

主要看：

```text
table_raw_vs_canonical.csv
VARIABLE_RENAME
FUNCTION_RENAME
PARAMETER_RENAME
FORMAT_COMMENT_CHANGE
```

正式论文可以写的条件：

```text
样例来自 manual / verified ai_assisted / external
validation/test split 冻结
canonical 在 rename 类样例上稳定高于 raw token
independent/common_structure 没有被 canonical 大量误判
```

seed 阶段只能写：

```text
synthetic seed 表明 canonical-token pipeline 能处理改名样例并生成表格输出。
```

## 3. 哪些实验支持动态阈值有价值

主要看：

```text
table_fixed_vs_dynamic.csv
table_dynamic_threshold_calibration.csv
metrics_summary.json
```

有价值的信号：

```text
NaturalSimilar FPR 下降
简单题或模板题误报下降
risk margin 分布更符合题目画像
validation-only 校准没有使用 test
```

必须同时写：

```text
Recall 是否下降
F1 是否稳定
不同 fixed threshold 是否存在反例
样本量是否足够
```

## 4. 动态阈值召回损失如何写

如果 Dynamic 降低 FPR 但 Recall 下降，建议写：

```text
动态阈值通过提高自然相似题目的复核阈值降低误报，但也可能导致部分相关样例低于阈值，表现为召回下降。该现象说明阈值校准需要在 validation set 上约束自然相似误报与 suspicious recall 的平衡，并在 test set 上报告 trade-off。
```

不要隐去召回损失。

## 5. V4 IR / lightweight summary 的定位

V4 表格：

```text
table_cross_language.csv
cross_language/method_comparison.csv
case_analysis/common_structure_cases.csv
case_analysis/unsupported_syntax_cases.csv
```

论文定位：

```text
experimental research feature
production weight 0
not in PICAS_STANDARD
有限 Java/Python 子集
不是完整 CFG/DFG/PDG
不是完整语义等价判断
```

可写：

```text
轻量 IR 和摘要在部分简单结构上能保留跨语言结构线索，但 common structure 误报和 unsupported syntax 漏报仍明显。
```

不能写：

```text
跨语言相似检测已经成熟可用。
```

## 6. 失败案例分析写法

至少选：

```text
1 个 natural_similar false positive
1 个 transformed false negative
1 个 common_structure false positive
1 个 unsupported_syntax false negative
1 个 parser fallback
```

每个案例写：

```text
pair_id
problem_type
case_type
language
label
系统输出
为什么失败
如何改进
是否属于 production 或 experimental 范围
```

推荐结构：

```text
案例 A 显示简单题自然相似仍可能被误报。
案例 B 显示动态阈值降低误报时可能带来召回损失。
案例 C 显示 experimental IR 对通用结构过敏。
案例 D 显示 unsupported syntax 造成结构摘要缺失。
```

## 7. Threats to Validity

建议分四类：

```text
Internal validity: 标签、split、阈值选择、JPlag 排除原因。
External validity: 数据规模、synthetic seed、课程/语言/题型覆盖。
Construct validity: 相似风险不等于抄袭结论，AI_REWRITE 不等于 AI 检测。
Implementation validity: parser fallback、IR 覆盖、JPlag min-token 和语言支持。
```

必须写：

```text
当前 seed 数据不能代表真实学生提交分布。
```

## 8. Limitations

建议写：

```text
数据集仍需补充 manual、verified ai_assisted 和 external 样例。
动态阈值为规则版，参数仍需更多 validation 数据校准。
V4 IR 只支持有限 Java/Python 子集。
lightweight summary 不是完整 CFG/DFG。
系统不执行上传代码，因此不判断运行行为语义等价。
外部基线目前 JPlag 已对齐，Dolos 仍预留。
MySQL 实库仍需有效凭据验证。
```

## 9. Future Work

优先级建议：

```text
1. 补齐真实/半真实 problem-disjoint 数据。
2. 冻结 validation/test 后重跑 E1-E5、JPlag 和 V4 exploratory。
3. 引入 Dolos 或更多外部基线。
4. 增强 parser/IR 对 unsupported syntax 的覆盖。
5. 在不破坏 production 边界前提下研究更细粒度 evidence。
6. 收集教师人工复核反馈。
```

## 10. 稳定功能 vs 研究实验功能

稳定功能：

```text
Java/Python token similarity
基础 AST similarity
canonical token similarity
identifier mapping
problem profile
dynamic threshold
weightedSimilarityScore / riskMargin / riskLevel
证据详情与 HTML 报告
```

研究实验功能：

```text
PICAS_CROSSLANG
CROSSLANG_IR_SIMILARITY
CROSSLANG_CONTROL_SUMMARY_SIMILARITY
CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY
V4 experimental composite
JPlag aligned seed baseline
Dolos reserved adapter boundary
validation-only threshold offset calibration
```

## 11. 推荐论文素材生成顺序

```text
1. 补数据并冻结 split。
2. 运行 validator，确认无 problem/source/hash overlap。
3. 运行 JPlag 对齐，记录 excluded_pairs.csv。
4. 更新 configs/experiments/research_v4.json 指向最新 JPlag baseline。
5. 运行 run_research_v4.py。
6. 从 paper_tables/ 复制表格到论文草稿。
7. 从 case_analysis/ 选择失败案例。
8. 更新 PAPER_OUTLINE.md 的“当前论文可用结果”。
9. 更新 TEST_REPORT.md 和 EXPERIMENT_PLAN.md。
```

每个效果句都必须能追溯到具体 CSV/JSON/Markdown 产物。
