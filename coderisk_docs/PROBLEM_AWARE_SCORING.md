# PROBLEM_AWARE_SCORING.md

> 本文件定义 CodeRisk / PICAS 的题目复杂度自适应评分与动态阈值机制。它是项目最重要的研究创新文件，直接决定论文主线、专利技术点和系统区别于普通查重工具的程度。

---

## 1. 模块定位

### 1.1 模块名称

```text
Problem-aware Similarity Calibration Module
```

中文名称：

```text
题目感知相似度校准模块
```

### 1.2 核心思想

不同题目的自然相似风险不同，因此不应使用统一固定阈值判断所有代码对。

本模块回答的问题是：

```text
在这道题的难度、模板化程度、解法空间和历史提交分布下，两份代码达到某个相似度是否异常。
```

### 1.3 研究贡献表述

论文中可表述为：

```text
提出一种题目复杂度自适应的代码相似度阈值校准方法，通过对题目难度、解法空间、模板化风险和自然相似风险进行建模，实现不同题目下相似风险阈值的动态调整，以降低简单题误报并增强复杂题中结构相似代码的识别能力。
```

---

## 2. 输入与输出

### 2.1 输入

```text
QuestionTextFeatures
ReferenceSolutionFeatures，可选
HistoricalSubmissionFeatures，可选
DetectedCodeMetrics，可选
DetectionConfig
```

### 2.2 输出

```text
DifficultyScore
SolutionSpaceScore
TemplateRiskScore
NaturalSimilarityRisk
ProblemComplexityLevel
DynamicThreshold
MetricWeightAdjustment
ThresholdExplanation
ProblemScoringWarnings
```

### 2.3 分数范围

所有核心分数统一归一化到：

```text
0.0 <= score <= 1.0
```

其中 0 表示最低，1 表示最高。

---

## 3. 核心分数定义

### 3.1 DifficultyScore

表示题目求解难度和实现复杂度。

高 DifficultyScore 通常意味着：

```text
代码自然相似概率较低
结构相似更可疑
动态阈值可适当降低
```

### 3.2 SolutionSpaceScore

表示题目可能存在多少不同解法和实现路径。

高 SolutionSpaceScore 通常意味着：

```text
独立实现的结构差异应更明显
若高度相似，风险更高
动态阈值可适当降低
```

### 3.3 TemplateRiskScore

表示题目是否容易套用标准模板。

高 TemplateRiskScore 通常意味着：

```text
常见模板片段相似不应直接视为强证据
模板相关结构需要降权
动态阈值应提高或模板片段权重应降低
```

### 3.4 NaturalSimilarityRisk

表示独立完成也可能产生相似代码的概率。

高 NaturalSimilarityRisk 通常意味着：

```text
简单题、固定输入输出题、固定算法模板题容易自然相似
应提高阈值并降低通用结构证据权重
```

---

## 4. 特征体系

题目评分由三类特征组成：

```text
TextFeatures：题面文本特征
ReferenceFeatures：参考答案静态特征
HistoricalFeatures：历史提交分布特征
```

开发顺序：

```text
规则特征优先
历史分布增强
LLM 只作为可选解释辅助
```

---

## 5. TextFeatures：题面文本特征

### 5.1 基础文本特征

```text
description_length
input_format_length
output_format_length
constraint_count
sample_count
tag_count
keyword_count
math_symbol_count
```

### 5.2 题目结构特征

```text
has_multiple_cases
has_complex_constraints
has_custom_data_structure
has_graph_description
has_tree_description
has_dynamic_programming_hint
has_sorting_hint
has_simulation_hint
has_string_processing_hint
has_fixed_output_pattern
```

### 5.3 输入输出复杂度特征

```text
input_variable_count
input_nested_level
output_variable_count
requires_formatting
requires_multiple_outputs
requires_matrix_input
requires_graph_input
requires_tree_input
```

### 5.4 关键词规则

可以维护关键词表：

```text
简单题关键词：sum, count, average, max, min, print, input, output
排序模板：sort, order, ranking
图算法：graph, shortest path, dfs, bfs, edge, vertex
动态规划：dp, optimal, subsequence, state, transition
模拟题：simulate, operation, query, update
字符串：substring, palindrome, match, pattern
```

中文题目同样维护中文关键词：

```text
求和、统计、最大值、最小值、排序、图、路径、树、动态规划、模拟、查询、更新、字符串、回文、匹配
```

---

## 6. ReferenceFeatures：参考答案特征

### 6.1 静态复杂度特征

如果有参考答案，提取：

```text
reference_line_count
reference_token_count
reference_function_count
reference_loop_count
reference_branch_count
reference_nested_depth
reference_cyclomatic_complexity
reference_data_structure_count
reference_api_call_count
reference_operator_diversity
```

### 6.2 算法结构特征

```text
uses_sorting
uses_hash_map
uses_set
uses_queue
uses_stack
uses_priority_queue
uses_recursion
uses_dfs_bfs
uses_dynamic_programming
uses_greedy
uses_two_pointers
uses_sliding_window
```

### 6.3 多参考答案

若有多个参考答案，计算：

```text
reference_solution_diversity
reference_pairwise_similarity_mean
reference_pairwise_similarity_std
```

多参考答案差异越大，说明解法空间可能越大。

---

## 7. HistoricalFeatures：历史提交分布特征

### 7.1 作用

历史提交分布是判断自然相似风险的强特征。

如果大量独立提交天然相似，则不应轻易判高风险。

### 7.2 特征定义

```text
historical_submission_count
pairwise_similarity_mean
pairwise_similarity_std
pairwise_similarity_p75
pairwise_similarity_p90
pairwise_similarity_p95
cluster_count
largest_cluster_ratio
common_fragment_ratio
template_fragment_frequency
```

### 7.3 使用条件

历史特征只有在样本数足够时启用：

```text
historical_submission_count >= 20：可弱启用
historical_submission_count >= 50：正常启用
historical_submission_count >= 100：强启用
```

样本不足时输出 warning：

```text
HISTORICAL_DATA_INSUFFICIENT
```

---

## 8. DifficultyScore 计算

### 8.1 推荐公式

```text
DifficultyScore = clamp(
  0.20 * TextComplexity
+ 0.25 * InputOutputComplexity
+ 0.30 * ReferenceImplementationComplexity
+ 0.15 * AlgorithmicKeywordComplexity
+ 0.10 * ConstraintComplexity,
0, 1)
```

### 8.2 子分数

```text
TextComplexity = normalize(description_length + constraint_count + tag_count)
InputOutputComplexity = normalize(input_variable_count + input_nested_level + output_variable_count)
ReferenceImplementationComplexity = normalize(line_count + cyclomatic_complexity + nested_depth + data_structure_count)
AlgorithmicKeywordComplexity = keyword_weighted_score(tags + description)
ConstraintComplexity = normalize(constraint_count + numeric_constraint_complexity)
```

### 8.3 无参考答案降级

如果无参考答案：

```text
ReferenceImplementationComplexity 使用 0.5 中性值
并输出 REFERENCE_SOLUTION_MISSING warning
```

---

## 9. SolutionSpaceScore 计算

### 9.1 含义

SolutionSpaceScore 表示题目是否允许多种实现路径。

### 9.2 推荐公式

```text
SolutionSpaceScore = clamp(
  0.30 * AlgorithmDiversityPotential
+ 0.20 * DataStructureChoicePotential
+ 0.20 * ReferenceDiversity
+ 0.20 * HistoricalClusterDiversity
+ 0.10 * ImplementationFreedom,
0, 1)
```

### 9.3 子分数说明

```text
AlgorithmDiversityPotential：题目是否可用多种算法
DataStructureChoicePotential：是否存在多种数据结构选择
ReferenceDiversity：多个参考答案之间差异
HistoricalClusterDiversity：历史提交聚类数量
ImplementationFreedom：I/O 和输出格式是否限制较少
```

### 9.4 典型判断

```text
A+B：SolutionSpaceScore 低
数组求和：低
排序：中低
图最短路：中
动态规划变形：中高
业务逻辑/课程设计模块：高
```

---

## 10. TemplateRiskScore 计算

### 10.1 含义

TemplateRiskScore 表示题目是否容易套用标准模板或课堂模板。

### 10.2 推荐公式

```text
TemplateRiskScore = clamp(
  0.30 * KnownAlgorithmTemplateScore
+ 0.25 * CommonStructureFrequency
+ 0.20 * ReferenceTemplateDensity
+ 0.15 * HistoricalLargestClusterRatio
+ 0.10 * IOFixedPatternScore,
0, 1)
```

### 10.3 模板类型

常见模板：

```text
标准输入输出模板
排序模板
DFS/BFS 模板
二分模板
动态规划基本模板
并查集模板
Dijkstra/Floyd 模板
滑动窗口模板
双指针模板
```

### 10.4 模板片段处理

模板片段不应直接删除，而应：

```text
保留证据
降低权重
标记为 TEMPLATE_FRAGMENT
在报告中解释其自然相似性
```

---

## 11. NaturalSimilarityRisk 计算

### 11.1 含义

NaturalSimilarityRisk 表示独立完成也可能相似的风险。

### 11.2 推荐公式

```text
NaturalSimilarityRisk = clamp(
  0.30 * SimplicityFactor
+ 0.25 * TemplateRiskScore
+ 0.20 * HistoricalSimilarityFactor
+ 0.15 * IOFixedPatternScore
+ 0.10 * LowSolutionSpaceFactor,
0, 1)
```

其中：

```text
SimplicityFactor = 1 - DifficultyScore
LowSolutionSpaceFactor = 1 - SolutionSpaceScore
HistoricalSimilarityFactor = normalized(pairwise_similarity_mean + p90)
```

### 11.3 解释规则

高 NaturalSimilarityRisk 时，报告中必须说明：

```text
该题可能由于题目简单、输入输出固定或模板化程度较高，导致独立提交之间自然相似度偏高。因此系统提高风险阈值，并降低通用结构证据权重。
```

---

## 12. ProblemComplexityLevel

将题目分为 5 档：

```text
VERY_SIMPLE
SIMPLE
MEDIUM
HARD
VERY_HARD
```

建议规则：

```text
DifficultyScore < 0.20：VERY_SIMPLE
0.20 <= DifficultyScore < 0.40：SIMPLE
0.40 <= DifficultyScore < 0.65：MEDIUM
0.65 <= DifficultyScore < 0.85：HARD
DifficultyScore >= 0.85：VERY_HARD
```

---

## 13. 动态阈值计算

### 13.1 基础阈值

默认：

```text
BaseThreshold = 0.80
```

可配置范围：

```text
0.70 <= BaseThreshold <= 0.90
```

### 13.2 推荐公式

```text
DynamicThreshold = clamp(
  BaseThreshold
+ a * NaturalSimilarityRisk
+ b * TemplateRiskScore
- c * DifficultyScore
- d * SolutionSpaceScore
+ e * HistoricalHighSimilarityAdjustment,
MinThreshold,
MaxThreshold)
```

推荐初始参数：

```text
a = 0.10
b = 0.06
c = 0.05
d = 0.04
e = 0.05
MinThreshold = 0.68
MaxThreshold = 0.95
```

### 13.3 直观解释

```text
题目越简单 → 阈值越高
自然相似风险越高 → 阈值越高
模板化风险越高 → 阈值越高
题目越复杂 → 阈值越低
解法空间越大 → 阈值越低
历史提交普遍很像 → 阈值提高
```

### 13.4 阈值调整项输出

系统必须输出每个调整项：

```json
{
  "base_threshold": 0.80,
  "adjustments": [
    {"name": "NaturalSimilarityRisk", "score": 0.72, "delta": 0.072},
    {"name": "TemplateRiskScore", "score": 0.60, "delta": 0.036},
    {"name": "DifficultyScore", "score": 0.30, "delta": -0.015},
    {"name": "SolutionSpaceScore", "score": 0.25, "delta": -0.010}
  ],
  "final_threshold": 0.883
}
```

---

## 14. 指标权重自适应

动态阈值之外，还需要调整不同相似度指标权重。

### 14.1 简单题权重策略

当 NaturalSimilarityRisk 高时：

```text
降低 IOPatternSimilarity 权重
降低普通 TokenSimilarity 权重
降低常见控制结构权重
提高 RareFragmentSimilarity 权重
提高 BugPatternSimilarity 权重
提高 IdentifierMappingSimilarity 的证据要求
```

### 14.2 复杂题权重策略

当 DifficultyScore 和 SolutionSpaceScore 高时：

```text
提高 ASTStructureSimilarity 权重
提高 ControlFlowSimilarity 权重
提高 DataDependencySimilarity 权重
提高 RareFragmentSimilarity 权重
```

### 14.3 模板题权重策略

当 TemplateRiskScore 高时：

```text
模板片段标记为 TEMPLATE_FRAGMENT
模板片段相似度不直接贡献高风险
非模板稀有片段权重提高
```

---

## 15. 历史提交分布校准

### 15.1 背景

如果已有大量历史提交，可以用当前题目的相似度分布校准阈值。

### 15.2 推荐方法

```text
HistoricalHighSimilarityAdjustment = max(0, historical_p90 - BaseThreshold) * 0.5
```

示例：

```text
如果历史 p90 相似度为 0.88，则增加 (0.88 - 0.80) * 0.5 = 0.04
```

### 15.3 分位数辅助阈值

可选增强：

```text
DynamicThreshold = max(formula_threshold, historical_p95 + margin)
```

其中：

```text
margin 默认 0.02
```

但必须注意：历史数据可能包含真实高风险提交，因此不能完全依赖历史分布。

---

## 16. LLM 辅助评分规则

### 16.1 定位

LLM 只能作为辅助解释，不作为核心评分来源。

允许用途：

```text
题目难度文字解释
题目标签补全
模板化风险提示
解法空间分析草稿
报告自然语言润色
```

禁止用途：

```text
LLM 直接判断是否抄袭
LLM 直接给最终风险分
LLM 直接替代规则评分
LLM 生成无法复现的实验指标
```

### 16.2 可复现要求

如果启用 LLM 辅助，必须保存：

```text
model_name
model_version
prompt_template_id
input_hash
output_text
whether_used_in_final_score=false/true
```

默认：

```text
whether_used_in_final_score=false
```

---

## 17. 风险等级与阈值关系

### 17.1 Margin 计算

```text
risk_margin = weighted_similarity_score - dynamic_threshold
```

### 17.2 风险等级

```text
LOW：risk_margin < -0.10
MEDIUM：-0.10 <= risk_margin < 0
ELEVATED：0 <= risk_margin < 0.10
HIGH：risk_margin >= 0.10
```

### 17.3 简单题保护规则

当：

```text
NaturalSimilarityRisk >= 0.75
```

且高风险证据只包含：

```text
TokenSimilarity
IOPatternSimilarity
普通循环结构
```

则不得输出 HIGH，只能最高输出 ELEVATED，并提示：

```text
该题自然相似风险较高，当前证据主要为通用结构相似，建议结合更多非模板证据复核。
```

### 17.4 强证据提升规则

当存在以下证据时，可提升风险等级：

```text
RareFragmentSimilarity 高
BugPatternSimilarity 高
稳定 IdentifierMapping 覆盖多个核心块
复杂 DataDependencySimilarity 高
非模板 AST 子树高度重合
```

但提升必须记录原因。

---

## 18. 输出解释模板

### 18.1 简单题解释

```text
该题难度较低且输入输出模式固定，系统评估其自然相似风险较高。因此本次检测采用较高动态阈值，以降低独立实现之间的误报风险。
```

### 18.2 模板题解释

```text
系统检测到该题存在较高模板化风险，部分相似结构可能来自常见算法模板。报告中已对模板片段进行降权，建议重点关注非模板稀有片段和边界处理证据。
```

### 18.3 复杂题解释

```text
该题实现复杂度和解法空间较高，独立实现之间通常会表现出更明显的结构差异。因此当代码出现高度结构相似时，系统会采用相对更敏感的风险阈值。
```

---

## 19. 实验验证设计

本模块必须能支持以下实验。

### 19.1 固定阈值对比

比较：

```text
FixedThreshold 0.75
FixedThreshold 0.80
FixedThreshold 0.85
ProblemAware DynamicThreshold
```

评价：

```text
False Positive Rate
False Negative Rate
Precision
Recall
F1-score
```

### 19.2 题目难度分组实验

按题目分组：

```text
VERY_SIMPLE
SIMPLE
MEDIUM
HARD
VERY_HARD
```

重点证明：

```text
简单题误报率降低
复杂题召回率不明显下降或提升
```

### 19.3 模板题实验

选取排序、DFS/BFS、二分、DP 基础题，验证模板降权是否减少误报。

### 19.4 消融实验

```text
Full Method
- DynamicThreshold
- NaturalSimilarityRisk
- TemplateRiskScore
- HistoricalFeatures
- MetricWeightAdjustment
```

---

## 20. 与专利交底的关系

本模块可作为专利核心技术点之一。

建议专利表述：

```text
一种基于题目特征和历史提交分布的代码相似度动态阈值生成方法。
```

核心步骤：

```text
获取题目文本和参考答案
提取题目复杂度特征
计算自然相似风险和模板化风险
计算动态阈值
根据动态阈值输出相似风险等级
生成阈值调整解释
```

---

## 21. 实现接口建议

### 21.1 Python 函数接口

```python
def analyze_problem(question: QuestionInput, config: ProblemScoringConfig) -> ProblemProfile:
    pass


def compute_dynamic_threshold(problem: ProblemProfile, metric_profile: MetricProfile, config: ThresholdConfig) -> ThresholdResult:
    pass


def adjust_metric_weights(problem: ProblemProfile, base_weights: dict) -> WeightAdjustmentResult:
    pass
```

### 21.2 输出对象

```json
{
  "difficulty_score": 0.42,
  "solution_space_score": 0.36,
  "template_risk_score": 0.58,
  "natural_similarity_risk": 0.67,
  "problem_complexity_level": "MEDIUM",
  "dynamic_threshold": 0.84,
  "threshold_explanation": "该题存在一定模板化风险和自然相似风险，因此阈值高于基础阈值。",
  "warnings": []
}
```

---

## 22. 数据库存储建议

应保存到 `problem_feature` 表：

```text
question_id
difficulty_score
solution_space_score
template_risk_score
natural_similarity_risk
problem_complexity_level
feature_json
threshold_config_json
scoring_version
created_time
```

每次分析结果保存：

```text
dynamic_threshold
threshold_adjustment_json
threshold_explanation
```

---

## 23. 参数默认值

```text
BaseThreshold = 0.80
MinThreshold = 0.68
MaxThreshold = 0.95
NaturalSimilarityWeight = 0.10
TemplateRiskWeight = 0.06
DifficultyWeight = 0.05
SolutionSpaceWeight = 0.04
HistoricalAdjustmentWeight = 0.05
SimpleProblemProtectionThreshold = 0.75
HighRiskMargin = 0.10
MediumRiskMargin = -0.10
```

所有参数必须可配置，并记录到实验配置中。

---

## 24. 自检清单

每次修改本模块后必须检查：

```text
[ ] 是否没有使用固定阈值替代动态阈值
[ ] 是否保留 base_threshold 和 adjustment 明细
[ ] 是否输出阈值解释
[ ] 是否避免 LLM 直接决定最终分数
[ ] 是否对简单题提高阈值
[ ] 是否对复杂题保持敏感性
[ ] 是否对模板片段降权
[ ] 是否保存 scoring_version
[ ] 是否支持实验消融
[ ] 是否支持历史数据不足时降级
[ ] 是否没有输出“抄袭成立”等定性结论
```
