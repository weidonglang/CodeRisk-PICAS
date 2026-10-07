# IR_SPEC.md

> 本文件定义 CodeRisk / PICAS V4 Phase 1-3 的跨语言实验能力。它只支持有限 Java/Python 子集，不是完整编译器 IR，不进入默认 PICAS_STANDARD 生产评分。

## 1. 版本与隔离

```text
Task mode: PICAS_CROSSLANG
IR version: normalized-ir-java-python-subset-v0.1
Summary version: lightweight-cfg-dfg-summary-v0.2
Persisted algorithm version: picas-v4-xl-ir0.1-sum0.2-exp
Stable: false
Production metric weight: 0.0
```

新增实验指标：

```text
CROSSLANG_IR_SIMILARITY
CROSSLANG_CONTROL_SUMMARY_SIMILARITY
CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY
```

三个指标权重均为 0。PICAS_STANDARD 不调用这些分析，不生成相应 metric/evidence，FORMULA_SPEC_V1、weightedSimilarityScore、dynamicThreshold、riskMargin 和 riskLevel 均不改变。

## 2. Normalized IR

受控节点包括 PROGRAM、FUNCTION、INPUT、OUTPUT、ASSIGN、IF、LOOP、CALL、RETURN、简单算术、比较和布尔操作。

Java for 头部统一折叠为 LOOP，减少与 Python for 的语法差异。相似度融合序列对齐、IR bigram Jaccard 和 operation-set Jaccard，并使用结构特异度与映射覆盖率抑制只有 LOOP/IF 的通用结构。

只有 Java-Python、两侧解析成功、覆盖率达到边界且存在共同 IR 片段时，才生成 CROSSLANG_IR_MATCH。解析失败时只生成 PARSER_WARNING，不伪造 IR evidence。

## 3. Lightweight Control-flow Summary

该摘要不是 CFG 图，只保存：

```text
branch_count
loop_count
max_nesting_depth
condition_pattern_sequence
return_count
early_return_count
return_path_summary
```

return_path_summary 当前区分 NO_RETURN、SINGLE_TERMINAL_RETURN、SINGLE_GUARDED_RETURN、MULTI_RETURN_WITH_GUARD 和 MULTI_TERMINAL_RETURN。

相似度比较非零计数、条件模式序列和返回路径摘要。evidence 使用 CONTROL_STRUCTURE_MATCH，并在 metadata 中写明 summaryKind=LIGHTWEIGHT_CONTROL_FLOW_SUMMARY、experimental=true、includedInWeightedScore=false。

## 4. Lightweight Data-flow Summary

该摘要不是 DFG 图，不解析完整 def-use chain，只保存：

```text
input_flow
accumulator_update_flow
array_index_flow
comparison_flow
return_dependency
```

当前模式包括 INPUT_TO_ASSIGN、VALUE_TO_OUTPUT、ACCUMULATE_ADD/SUBTRACT/MULTIPLY/DIVIDE/MODULO、INDEX_READ/WRITE、比较类型以及 RETURN_IDENTIFIER/INDEX_READ/ARITHMETIC/CALL/CONSTANT/EXPRESSION。

evidence 使用 OPERATION_SEQUENCE_MATCH，并明确 summaryKind=LIGHTWEIGHT_DATA_FLOW_SUMMARY。它不表示完整数据依赖或语义等价。

## 5. 支持与不支持范围

支持：基础输入输出、赋值、if、for/while/do、普通调用、return、简单算术与比较、常见数组下标和累加器更新。

不支持或只记录 warning：switch/match、try/catch/with、lambda、生成器和推导式、async/await、复杂继承/多态、反射、闭包语义、复杂泛型语义、完整库 API 语义、递归/迭代等价证明。

明确禁止：完整 CFG、完整 DFG、PDG、符号执行、定理证明、上传代码执行、完整跨语言语义等价判断。

## 6. 降级逻辑

```text
PICAS_STANDARD -> 完全跳过全部跨语言实验指标
非 Java-Python -> REVIEW_NOTE，无跨语言结构 evidence
解析失败 -> PARSER_WARNING，三个实验指标为 0，无结构 evidence
IR 覆盖不足 -> REVIEW_NOTE，无 CROSSLANG_IR_MATCH
unsupported syntax -> 保留 warning；仅输出实际可提取的摘要
```

## 7. 实验结果

Phase 1 产物：data/artifacts/experiments/PICAS-V4-PHASE1-XL-20260621-R1/

```text
sum-positive: 1.0000
read-add-print: 0.7639
parse failure: 0.0000, fallback
```

Phase 2 最新产物：data/artifacts/experiments/PICAS-V4-PHASE2-XL-20260623-R2/

Phase 2 使用固定 0.70 实验复核阈值与预先声明的 0.40/0.30/0.30 IR/控制/数据摘要组合，仅用于失败分析，不进入生产公式。7 个固定样例记录 1 个 false positive、2 个 false negative、1 个预期解析降级；运行中未修改样例、标签或阈值。

R2 中 array-loop、BFS、DP 的实验组合分分别为 1.0000、0.8136、0.7075；simple I/O 与 unsupported syntax 分别以 0.6056、0.5460 漏报，common-structure 独立样例以 0.7427 误报。解析失败样例的三个实验指标均为 0，且没有生成 IR/控制/数据摘要 evidence。

这些结果只证明最小原型可运行、可解释、可复现，不构成大规模 benchmark 或统计显著结论。

## 8. Research V4 seed aggregate

`PICAS-RESEARCH-V4-SEED-20260624-R2` 将 80 个同语言 pair 与 11 个跨语言 pair 接入统一 manifest。全部为 synthetic seed，4 个 AI_REWRITE placeholder 不进入核心指标。跨语言 eligible test 中有 6 个 pair：experimental composite F1 为 0.6667、FPR 为 1.0；control summary F1 为 0.8、FPR 为 1.0；data summary F1 为 0.5714、FPR 为 0。结果继续暴露 common structure 误报和 unsupported syntax 漏报，不能用来宣称跨语言效果领先。

旧 7-case 跨语言 split 仍标记为 non-preregistered；新 seed 只用于工具链预实验。IR/control/data 指标生产权重保持 0，人工或外部数据补充后必须重新运行并克制解释。
