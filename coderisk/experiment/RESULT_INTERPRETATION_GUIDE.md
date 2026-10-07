# Research V4 Result Interpretation Guide

本文档说明如何阅读 Research V4 输出。核心原则：PICAS 输出“相似风险”和“人工复核建议”，不输出“确认抄袭”“证明作弊”或“完整语义等价”。

## 1. Dynamic vs Fixed

查看：

```text
paper_tables/table_fixed_vs_dynamic.csv
same_language/fixed_vs_dynamic.csv
```

重点比较：

```text
PICAS_DYNAMIC
FIXED_0.70
FIXED_0.75
FIXED_0.80
FIXED_0.85
```

读法：

```text
如果 Dynamic 的 NaturalSimilar FPR 更低，说明动态阈值在该数据上减少了自然相似误报。
如果 Dynamic 的 Recall 下降，必须同时报告召回损失。
如果 Dynamic 的 F1 没有超过某个固定阈值，不能声称全面优于固定阈值。
```

论文可写：

```text
动态阈值在 seed/验证数据中展示了降低自然相似误报的潜力，同时存在召回损失，需要在真实数据上继续校准。
```

不能写：

```text
动态阈值一定优于所有固定阈值。
```

## 2. NaturalSimilar FPR

NaturalSimilar FPR 指 `NATURAL_SIMILAR` 样例被预测为超过阈值的比例。

读法：

```text
越低越好，表示简单题或模板题的自然相似误报越少。
必须和 Recall 一起看，避免只靠提高阈值降低 FPR 却漏掉真正相关样例。
```

适合放在论文“简单题自然相似误报分析”。

## 3. Precision / Recall / F1

| 指标 | 看什么 | 风险 |
|---|---|---|
| Precision | 被系统提示为风险的样例有多少是正类 | 低 precision 表示误报多 |
| Recall | 正类样例有多少被系统提示出来 | 低 recall 表示漏报多 |
| F1 | precision 与 recall 的折中 | 小样本下波动大 |

解释必须同时包含误报和漏报，不要只报 F1。

## 4. Raw token vs Canonical token

查看：

```text
paper_tables/table_raw_vs_canonical.csv
same_language/raw_vs_canonical.csv
```

重点看 rename 类 case：

```text
VARIABLE_RENAME
FUNCTION_RENAME
PARAMETER_RENAME
```

读法：

```text
raw token similarity 下降而 canonical token similarity 保持稳定，支持“置换不变规范化能抵抗标识符替换”。
如果 canonical 对 independent 或 common_structure 也过高，要在失败分析中报告。
```

当前 seed 可写为流程性结果：rename seed case 上 canonical 均值稳定高于 raw。正式结论需等待 manual/external 数据。

## 5. NoDT / NoCanon / Full 消融

查看：

```text
paper_tables/table_ablation.csv
same_language/ablation.csv
```

读法：

```text
PICAS-NoDT: 去掉动态阈值，观察自然相似 FPR 是否升高。
PICAS-NoCanon: 去掉 canonical 表示，观察 rename / rewrite 的 recall 是否下降。
PICAS-Full: 生产主方法，不包含 V4 experimental 零权重指标。
```

如果 Full 并非所有指标最好，要诚实写成 trade-off，而不是修改表格。

## 6. JPlag vs PICAS

查看：

```text
paper_tables/table_baseline_comparison.csv
paper_tables/table_jplag_vs_picas.csv
baseline_analysis/jplag_vs_picas.csv
baseline_registry.csv
```

读法：

```text
只比较 datasetSplit=test 且 jplagStatus=MATCHED 的行。
JPlag 排除样例必须报告 excluded_pairs.csv 的原因。
seed 数据上的数值只能说明对齐流程可运行，不说明谁更强。
```

正式论文可比较的前提：

```text
manual / external 数据补齐
validation/test split 冻结
JPlag 排除原因透明
同一批 pair 同时有 PICAS 和 JPlag 结果
```

## 7. common_structure 误报

查看：

```text
case_analysis/common_structure_cases.csv
case_analysis/failure_analysis.md
cross_language/failure_cases.csv
```

含义：

```text
两个独立实现共享普通 loop/if/return 结构，导致 IR 或 lightweight summary 分数偏高。
```

论文写法：

```text
有限 IR 和轻量摘要会把通用控制结构当成相似线索，因此需要结合题目画像、数据流细节、稀有片段和人工复核。
```

不能写：

```text
V4 IR 已经可靠解决跨语言相似检测。
```

## 8. unsupported_syntax 漏报

查看：

```text
case_analysis/unsupported_syntax_cases.csv
cross_language/failure_cases.csv
```

含义：

```text
Java lambda、Python generator/comprehension、复杂库调用等语法当前不能被完整映射到 IR 或摘要，结构分数可能偏低。
```

论文写法：

```text
解析降级和 unsupported syntax 是当前方法的主要威胁之一，系统会输出 warning 并避免伪造 AST/CFG/IR 证据。
```

## 9. parser fallback 怎么写

解析失败时正确行为：

```text
保留 token 级结果
输出 PARSER_WARNING
不生成 AST/CFG/IR 结构 evidence
不把 fallback 包装成完整结构分析
```

论文可写：

```text
系统采用保守降级策略，在解析失败时避免生成不可靠结构证据。
```

## 10. 哪些结果可以写成论文结论

在当前 seed 阶段，只能写：

```text
工具链已能校验 problem/source/hash 隔离。
数据录入、hash、manifest、JPlag 对齐、校准和论文表格流程可复现。
seed rename case 显示 canonical token pipeline 能保持稳定。
seed common_structure 和 unsupported_syntax 暴露 V4 experimental 局限。
```

补齐真实或半真实数据后，才可以写：

```text
在冻结 test set 上，动态阈值对自然相似误报的影响。
在 manual/external rename 数据上，canonical 表示的鲁棒性。
在同语言数据上，PICAS 与 JPlag 的对照结果。
```

## 11. 哪些只是 exploratory observation

```text
synthetic seed 上的 F1、FPR、Recall 数值
4 个 placeholder AI_REWRITE 行
旧 7 个 non-preregistered cross-language case
V4 IR / lightweight control/data-flow summary
small-N common_structure 和 unsupported_syntax 分析
Dolos 预留但未运行状态
```

## 12. 不能夸大的内容

不要宣称：

```text
确认抄袭
证明作弊
完整语义等价
检测 AI 生成代码
跨语言 IR 稳定成熟
synthetic seed 是正式 benchmark
PICAS 全面超越 JPlag / Dolos / MOSS
```

推荐措辞：

```text
相似风险
人工复核建议
有限范围实验性结构表示
预实验结果
流程验证
真实数据待补充
```
