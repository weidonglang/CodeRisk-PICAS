# FORMULA_SPEC.md

> 2026-10-08 实验性 HTML 分支使用独立公式 `HTML_STRUCTURE_FIXED_V1`：规范化可用时 `S=0.25 Token+0.30 HTML结构序列+0.45 Canonical`，阈值 `T=htmlThreshold`（默认 0.85，有限值且在 `[0,1]`），不应用本文件算法题动态调整。风险边际/等级和展示分计算沿用本文件规则；展示分不是抄袭概率。降级时 `S=Token`。C 暂沿用 PICAS 规则但未完成 C 标注数据校准。HTML/C 实际范围和验证见 [多语言进展](proposal/MULTILANGUAGE_PROGRESS.md)。

> 本文件是 CodeRisk / PICAS 生产版公式真源。算法、数据库、API、前端展示、实验脚本和论文写作必须优先遵守本文件。

---

## 1. 核心原则

PICAS 输出的是“相似风险”，不是“抄袭结论”。生产版公式必须清晰、可解释、可复现，并避免在多个环节重复惩罚同一因素。

生产版固定采用：

```text
weighted_similarity_score = Σ wi * Sim_i

dynamic_threshold = f(problem_profile)

risk_margin = weighted_similarity_score - dynamic_threshold

calibrated_risk_score = clamp(
  0.5 + risk_margin / margin_scale,
  0,
  1
)
```

默认：

```text
margin_scale = 0.40
```

补充约束：`calibrated_risk_score` 仅用于面向用户的归一化展示，不作为高风险样本内部排序的第一关键字。结果排序必须优先使用：

```text
risk_level DESC
risk_margin DESC
weighted_similarity_score DESC
rare_fragment_similarity DESC
```

这样可以避免展示分数饱和后导致高风险样本无法区分。


---

## 2. 字段定义

| 字段 | 含义 | 范围 | 是否入库 |
|---|---|---:|---|
| `weighted_similarity_score` | 多维相似度加权结果 | 0-1 | 是 |
| `dynamic_threshold` | 根据题目画像生成的动态阈值 | 0-1 | 是 |
| `risk_margin` | `weighted_similarity_score - dynamic_threshold` | 可正可负 | 是 |
| `calibrated_risk_score` | 面向展示的校准风险分数 | 0-1 | 是 |
| `risk_level` | 风险等级 | 枚举 | 是 |
| `exceed_threshold` | 是否超过动态阈值 | boolean | 是 |
| `margin_scale` | 风险边际映射尺度 | >0 | 是，配置/实验记录 |

---

## 3. 生产版禁止事项

生产版禁止使用无界扣分形式：

```text
RiskScore = Σ wi * Sim_i - NaturalSimilarityPenalty - TemplatePenalty
```

原因：`NaturalSimilarityRisk` 与 `TemplateRiskScore` 已经通过 `dynamic_threshold` 或指标权重调整发挥作用，若再在最终分数中无界扣分，会造成双重校正，增加漏检风险。

---

## 4. NaturalSimilarityRisk 与 TemplateRiskScore 的使用方式

允许使用方式：

1. 影响 `dynamic_threshold`；
2. 影响 metric weight adjustment；
3. 作为证据解释标记；
4. 作为实验分析维度。

默认不允许：

1. 在生产版最终分数中再次无界扣分；
2. 直接将模板片段相似判为高风险；
3. 直接输出“抄袭成立”。

### 4.1 V2 规则版动态阈值

V2 初版采用以下有界、可配置公式：

```text
base_threshold = 0.68

dynamic_threshold = clamp(
  base_threshold
  - 0.06 * DifficultyScore
  - 0.04 * SolutionSpaceScore
  + 0.08 * TemplateRiskScore
  + 0.12 * NaturalSimilarityRisk,
  0.50,
  0.95
)
```

系数可由任务配置覆盖，但每项权重必须限制在 `0-0.30`，最终阈值必须保持在 `0.50-0.95`。历史分布尚未接入时，`historical_distribution_adjustment` 固定为 `0`，不得用模拟分布替代。

---

## 5. 风险等级映射建议

风险等级应主要依据 `risk_margin` 与 `calibrated_risk_score`：

```text
risk_margin < -0.10                    -> LOW
-0.10 <= risk_margin < 0               -> MEDIUM
0 <= risk_margin < 0.10                -> ELEVATED
risk_margin >= 0.10                    -> HIGH
```

该边界可在验证集上校准，但必须记录：

```text
formula_version
margin_scale
risk_level_boundary
random_seed
dataset_version
git_commit
```

---

## 6. 实验分支说明

若需要研究扣分策略，只能作为实验分支，例如：

```text
PICAS-Penalty-Ablation
```

实验分支必须单独记录公式版本，不得混入生产版默认输出。

## 7. V4 跨语言实验指标

以下指标固定为实验性零权重指标：

```text
CROSSLANG_IR_SIMILARITY                         weight = 0.0
CROSSLANG_CONTROL_SUMMARY_SIMILARITY            weight = 0.0
CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY          weight = 0.0
```

它们不得进入 PICAS_STANDARD 的 weightedSimilarityScore、dynamicThreshold、riskMargin、calibratedRiskScore、riskLevel 或 exceedThreshold。Phase 2/3 实验中的 composite 与 0.70 阈值只用于独立实验失败分析，不是生产公式。Research V4 runner 必须记录 `experimentalMetricsProductionWeight=0.0` 和 `productionFormulaChanged=false`。

## 8. Research V4 校准纪律

Research V4 的阈值 offset 只能从 validation set 候选中选择；test set 不得参与候选排序或参数修改，只能在参数冻结后评估一次。每次校准必须记录 `formulaVersion`、`algorithmVersion`、`datasetVersion`、`randomSeed`、`runId`、候选参数、选中参数及 `testSetUsedForSelection=false`。

seed 数据上的选中 offset 仅验证校准流程，必须标记 `experimentOnly=true` 和 `productionFormulaChanged=false`。它不能写回 FORMULA_SPEC_V1，也不能作为真实数据上的生产阈值结论。
