# 多维相似度：隔离消融与真实流程记录

日期：2026-10-10；研究实施计划阶段 2。当前状态：**实验工具已实现，synthetic 流程已验证，正式效果评测待可信标签**。没有新增核心相似算法，没有修改生产评分、API、数据库或 V4 权重。

## 1. 增量文件、风险与验收

| 文件 | 用途 / 验收 |
| --- | --- |
| `coderisk/experiment/similarity_ablation.py` | 独立 runner；复用已有 loader、分组、生产分析及指标/CSV helper，不重建架构 |
| `coderisk/configs/experiments/similarity_ablation_v1.json` | 固化 14 方法、候选参数、seed 与工作点；不修改生产配置 |
| `coderisk/analysis-service-python/tests/test_similarity_ablation.py` | 19 项：参数合法性、AP ties、未知标签、validation-only、共同样本、完整检索池、真人门禁及真实 seed 集成 |
| 本文、根 README、EXPERIMENT_PLAN、ROADMAP、TEST_REPORT | 状态、命令、限制与后续条件同步，不删除历史探索负结果 |
| `coderisk/experiment/evidence/similarity-ablation-20261010/` | 本次真实 CSV/JSON/Markdown 和 JUnit，不打包为真实 benchmark |

主要风险是不同方法缺失指标造成覆盖偏差、将 UNCERTAIN 视为负例、使用 test 选择阈值，以及从不完整候选池虚报 Recall@K。测试分别覆盖；检索池丢失候选的新增回归先实际失败、再修复。新工具最初仅缺模块导致 collection error，不把它包装成生产算法故障。

## 2. 冻结配置和比较范围

现有同语言 Java/Python 信号：raw、基础 AST 节点序列、canonical token、identifier mapping。可用的数值均读取已有分析模块；实验组合只在离线 runner 内计算。

| 组 | 方法 / 权重 |
| --- | --- |
| 单项 | RAW_ONLY、AST_ONLY、CANONICAL_ONLY、MAPPING_ONLY，各 1.0 |
| 两两组合 | 4 项中的全部 6 对，各 0.5/0.5 |
| 固定权重对照 | ALL_EQUAL，各 0.25；PICAS_FIXED 读取现行完整分数（正常路径 .20/.20/.45/.15） |
| 阈值对照 | PICAS_RULE_DYNAMIC 不调参、offset=0；PICAS_DYNAMIC_OFFSET 只在 validation 固定网格选 offset |

PICAS_FIXED 可作为 NoDT 对照；RAW_AST_EQUAL 在正常可用路径上相当于同时移除 canonical 和 mapping 的 NoCanon，不应把这项差异单独归因于 canonical。单项和两两组合帮助观察相关性，而非假定各指标相互独立。

固定阈值网格、动态 offset 网格及 tie-break 均在配置/源码固化：普通选择最大 validation F1，再较低 FPR，fixed 同分取较高阈值、offset 同分取最接近 0。test 不参与选择。固定阈值 1.000001 用于 reject-all 工作点，不作为相似分数。规则阈值沿用 .50–.95 clamp；离线 offset 不写回生产。

“固化配置”不等于这批已反复查看的 seed 获得预注册研究资格。正式运行还要求新数据的 dated FROZEN registration 对应精确配置 SHA-256、独立真人复核及许可；当前默认运行实际被门禁拒绝，只有显式 `--allow-development` 可运行 seed。

## 3. 样本、缺失和公平比较

- loader 校验字段/路径/hash；连通分组综合 problem、source、source_family 和代码 hash，任何跨 validation/test 连通泄漏均致命，即便 development 也不能跳过。
- placeholder、UNCERTAIN、不合格或跨语言样例不进本轮准确率计算，记录 excluded.csv；不能把不同同题提交自动当作独立负例。
- AST/canonical/mapping 不可用记 `null`，不以 0 或 raw 冒充单项结果。PICAS 原有 raw 回退分保留在生产对照。
- **COMMON 主表**在 14 方法都可用的相同样本上比较；validation 也使用同样的共同支持规则。**AVAILABLE 附表**观察各方法实际覆盖/降级，仅诊断，不能视为相同样本比较。
- scores.csv 保留题目、split、source/hash、各分量、full、阈值、warning 与耗时。predictions.csv 保留逐样本方法、预测、原标签和 common 标记；不能将风险预测视为违规结论。

COMMON 可能排除最难解析的样例，有选择偏差；必须同时报告 coverage、AVAILABLE、excluded 和 parser_fallbacks，而不是只展示共同集的好成绩。source/family 隔离依赖元数据，不等于已证明作者身份独立。

## 4. 指标定义与不可计算条件

Precision、Recall、F1、FPR、NaturalSimilar FPR 复用已有混淆矩阵函数；未知标签不进入分母，零分母用 null/N/A。正例遵循既有 SIMILAR/SUSPICIOUS/TRANSFORMED，负例为 INDEPENDENT/NATURAL_SIMILAR；其关系真实性仍须复核。

`pr_auc_ap_score` 是不插值的阶梯 PR 面积（Average Precision）：按不同分数降序成组，每组累加 `ΔRecall × Precision`。同分不按文件顺序拆开，避免虚假优势；不是梯形插值 PR-AUC。缺少任一类别保守记 N/A。`pr_auc_ap_margin` 对 score-threshold 排序；为复用单位区间检查作单调平移/缩放，不改变排序。动态阈值不改原始分数，因此固定/动态的 score AP 一样不是实现错误。

`COMMON_LOW_FPR` 只在 validation 寻找经验 FPR≤0.05 的工作点，并最大化其 Recall；找不到就 N/A。输出独立 test 的**实际** Recall 和 FPR，不宣称 test 或总体 FPR 固定为 5%。本次 validation 负例仅 15 对，非零 FPR 的最小步长为 1/15，无法提供可靠低尾估计；当前未增加独立群 bootstrap 置信区间，新样本统计推断仍待后续研究。

Recall@K 只适用于明确定义且完整标注的 query pool：提供 `retrieval_query_id`、`query_source_sha256`、`retrieval_pool_complete=true`、`retrieval_pool_size`，每个候选包含 anchor，题目/split 一致，候选 hash 不重复且实际数量匹配。排序按 score，再 pair_id 解同分，宏平均有正例 query 的召回。声明元数据还需人工核验；任意抽样代码对不能支持检索结论。

检索计算保留所有候选，某方法不支持的候选不被悄悄删除；存在缺分数、未知标签、缺候选或不完整池则 N/A。本次 seed 没有上述完整池声明，42 条（14×3 个 K）都不可计算。

耗时分开记录：analysis_elapsed_ms 包含共享分析与可用性检查；aggregation_us 只计固定信号组合。不能将共享总耗时分别归给 14 方法后宣称速度优劣；本次没有外部基线耗时测量。

## 5. 实际 synthetic 运行

[原始证据](../../coderisk/experiment/evidence/similarity-ablation-20261010/README.md)，runId=`research-ablation-seed-20261010-r2`：输入 91，对本轮范围分析 75，排除 16；共同可用 68（validation 32，test 36），7 个 canonical 回退（validation 3，test 4）。formalEligiblePairs=0。

共同 test：21 正例、15 负例，其中 7 个 NATURAL_SIMILAR。这里只摘录实际流程结果，完整 14 方法见 REPORT.md/metrics.csv：

| 方法 | Precision | Recall | F1 | FPR | Natural FPR | AP score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RAW_ONLY | .5833 | 1.0000 | .7368 | 1.0000 | 1.0000 | .6134 |
| CANONICAL_ONLY | .9444 | .8095 | .8718 | .0667 | .1429 | .8996 |
| AST_CANONICAL_EQUAL | .9444 | .8095 | .8718 | .0667 | .1429 | .9054 |
| PICAS_FIXED | .6667 | .9524 | .7843 | .6667 | 1.0000 | .7454 |
| PICAS_RULE_DYNAMIC | .7647 | .6190 | .6842 | .2667 | .5714 | .7454 |
| PICAS_DYNAMIC_OFFSET | .8182 | .8571 | .8372 | .2667 | .5714 | .7454 |

不回避负结果：此 seed 上完整融合不是最高 F1，规则动态阈值虽然减少假阳性也明显降低召回；不同模块是权衡，不是都加入就一定更优。不能由这批合成标签推论真实课堂误报改善，更不能在同一旧 seed/test 上反复优化后宣称泛化。

低 FPR 分支的 fixed/raw/canonical 在 validation 可选工作点，但 test FPR 为 .0667，不能写成“5% FPR 下的 test Recall”；rule/offset 在冻结候选集内找不到符合验证约束的工作点，报告 N/A，不扩展网格适配 test。

改名分支复用阶段 1 的 6 个自有 fixture，每例 8 个固定域置换，48 变体 × 14 方法 = 672 逐行分数。参照是源代码与自身相比较，不是未改名前真实关系 pair。AST/canonical/mapping 在这些有限变体中 delta=0；raw 和完整分数可以下降，符合“不主张总分不变”。该表不进入标签准确率或 formal 指标，不能推论任意语义改写。

COMMON_STRUCTURE 的独立标注 seed 仍可产生 full 假阳性，表明共同结构/映射覆盖并非关系证据。UNSUPPORTED_SYNTAX 的分数必须结合 parser_fallbacks 和 AVAILABLE 查看：raw 回退可能漏报，不能只看排除了失败样例的 COMMON 表。failures.csv 的行数是“方法×pair”失败次数，不是独立失败 pair 数；按 pair_id 去重后再描述样本量。

历史 ConPlag 不重评分、不改阈值、不移植 JPlag 分数：raw Full/NoCanon F1 .5543/.5985，去模板 .6974/.7352 仍保留；去模板 JPlag 共同 test 是 625 而非 PICAS 的 627。新版本与旧分数不能混成共同表。本轮 JPlag 状态为 NOT_RUN，不输出外部基线优劣。

## 6. PowerShell 运行与产物

从根目录，先完成 README 中 Python 依赖安装，脚本参数先看 --help：

```powershell
$Python = '.\coderisk\analysis-service-python\.venv\Scripts\python.exe'
& $Python coderisk/experiment/similarity_ablation.py --help
# seed 必须明确 development；output 不得已存在。
& $Python coderisk/experiment/similarity_ablation.py `
  --config coderisk/configs/experiments/similarity_ablation_v1.json `
  --output output/research-ablation-new-run --allow-development
& $Python -m pytest -q -p no:cacheprovider
# 新可信数据先另存配置、精确登记其 hash；正式评估不加 allow-development。
```

主要文件：config.json、run_manifest.json（版本/hash/seed/git/time/门禁）、dataset_validation.json、scores.csv、selection.json、metrics.csv、predictions.csv、results.json、coverage.csv、retrieval.csv、excluded.csv、failures.csv、borderline.csv、parser_fallbacks.csv、rename_stability.csv、REPORT.md。CSV 空单元格表示 null，不自动填 0；JSON 是机器判读的权威类型。

配置里的 datasetManifest 相对 `coderisk/` 解析。configSha256 指输入配置文件的原始字节；产物 config.json 是重新格式化后的等价参数快照，不保证字节相同。精确复现注册时使用版本化的输入配置文件，不对输出漂亮打印后的 JSON hash 重新冒充原注册。

本次本机 Python 3.12.14，使用 `.tmp/language-venv/Scripts/python.exe`，新测试 19 项、完整工作树 337 项通过，1 条既有 Starlette/httpx warning。后端/前端没有本轮改动，不重跑它们；上一批 H2 19 项与 npm build 通过不冒称本轮新结果。FORMULA_SPEC、canonicalization.py、token_similarity.py 哈希与上一批一致。

## 7. 论文使用与下一步阻塞

当前表格可用于方法/评测协议及 synthetic 工具链预实验说明，不可写为真实 benchmark、总体显著改善、完整融合优越性或对 AI 的胜利。相似风险只支持复核，不确认抄袭、作弊、完整语义等价或 AI 来源。

下一步仍是可信独立关系数据和冻结的新题 test，尤其独立/NATURAL_SIMILAR、模板与短代码、common_structure 和 unsupported 失败样例。独立分布统计校准需要足够的可靠参考提交、共享源码 pair 的依赖处理、validation-only 参考选择、样本不足及新题回退；不能把本批 seed 负标签当作真实独立分布。统计校准与 LLM baseline 本阶段未实现，也未接入业务。
