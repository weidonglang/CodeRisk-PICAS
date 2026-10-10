# 题目感知独立解答上尾校准：隔离研究分支

2026-10-10，研究实施计划阶段 3。实现入口：[`natural_similarity_calibration.py`](../../coderisk/experiment/natural_similarity_calibration.py)，冻结初版配置：[`natural_calibration_v1.json`](../../coderisk/configs/experiments/natural_calibration_v1.json)。这是 offline experimental，不进入 API、数据库、前端或默认生产评分。FORMULA_SPEC、生产规范化与融合源码未改，V4 IR/摘要权重仍为 0。

## 1. 定义与已实现内容

对同一题目 p、同一语言及已登记模板背景的可信独立解答，目标为：

```text
q_p(s) = Pr(S_independent,p >= s)
k = count(reference_score >= s)
q_empirical = k / m
q_smoothed = (1 + k) / (m + 1)
```

S 直接读取现有 PICAS_STANDARD 的 weightedSimilarityScore，不增加扣分或重新定义融合。并列分数计入上尾。q 是独立解答达到该相似度的上尾概率目标；代码输出的是有限参考样本估计，**不是抄袭概率**，也不是语义等价概率。

空参考输出 null；不会输出伪造的 q=0。+1 平滑使最小值为 1/(m+1)，随目标分数 s 单调不增，测试验证该代数契约。这个性质不证明参考样本无偏、IID、可交换或总体 FPR 受控；本轮不提供置信区间或 conformal 保证。

默认至少 20 对通过门禁且互不复用源码/作者的参考。20 对只能达到约 0.0476 的最小平滑尾值；alpha=0.025 至少需要 39 对，alpha=0.01 至少需要 99 对，且都要上尾计数为 0。不能用大量有依赖的两两组合制造虚假的尾部分辨率。

当前实现：经验上尾、保守平滑、参考数据质量门禁、确定性去复用、模板/短代码/解析降级、新题冷启动、validation-only alpha 选择、固定/规则/统计回退策略的同样本表及 CSV/JSON/Markdown 输出。正式效果尚未验证。

## 2. 两个不同的评测问题

| 协议 | 参考池 | test 是否可有同题 q | 可以怎样描述 |
| --- | --- | --- | --- |
| VALIDATION_PROBLEMS_ONLY，默认 | 仅 validation 题目的独立参考解 | 不可；新题显式冷启动，回退规则阈值 | 查询集及参考与 test 题目隔离的新题部署 |
| PREREGISTERED_CONTEXT_PANEL，显式选用 | test 访问前预先冻结的每题独立参考面板 | 满足门禁时可；alpha 仍仅 validation 选择 | 已有题目参考背景的条件评估，不是参考/test problem-disjoint |

两个协议都要求 validation/test 查询题目隔离；参考与查询的作者、source、family、hash 隔离，参考 validation/test 面板之间也不能共享这些身份。同题参考池与 test 查询使用不同代码，不意味着题目本身隔离。不能一边要求测试新题没有同题数据，一边又宣称已估计其同题经验分布。

本轮不实现新题总体参考分布、题型迁移或层次模型；新题只回退现有有界规则动态阈值。冷启动回退不是统计校准成功。

## 3. 参考面板录入与质量门禁

独立参考 manifest 与查询集 manifest 分开管理。默认 [`independent_references.json`](../../coderisk/experiment/datasets/research-v4/independent_references.json) 是 EMPTY / PENDING，records=[]，没有真人数据或真实关系标签。

复制 [`independent_reference_pair.template.json`](../../coderisk/experiment/datasets/research-v4/templates/independent_reference_pair.template.json)，填入真实记录后放入独立 manifest 的 records。模板 active=false、placeholder/synthetic、复核 PENDING，不可直接当可信样本。

每对参考需填写：

- reference_id、problem_id、language（java/python），两个代码路径；路径相对于参考 manifest 目录，解析后必须留在该目录树，文件必须存在且为 UTF-8。禁止执行或上传源码。
- code_a_sha256/code_b_sha256：实际文件字节的 SHA-256，64 位 hex，不含前缀；与 Get-FileHash 对齐。用于检测文件被修改，不用它直接比较查询集文本。
- authors/sources/families：各两个非空且不同的稳定匿名身份；不能用文件名或提交序号臆造独立作者。不同 manifest 应使用同一身份命名规则，避免别名绕过泄漏检查。
- source_type 只可 manual/external，synthetic=false，active=true；ai_assisted/synthetic/placeholder 不作可信独立参考。
- provenance.license_or_authorization、source_reference：真实授权/许可证与可追溯来源。
- question.title/description，以及必要的输入输出/约束：与该题查询背景一致。
- review.status=AGREED、label=INDEPENDENT、relation_verified=true；两位不同 HUMAN reviewer、实际复核独立性确认、label_basis、reviewed_at、functional_evidence。必须真实审核独立创作关系，不能只看“同题不同提交”或由 AI 两次确认。
- template_status：明确无公共模板用 NONE；有模板用 REGISTERED，登记 template_code、template_language、template_source。缺失是 UNDECLARED，不是 NONE。

自动门禁只是结构、声明和文件完整性核对，**不能证明填写的授权或 HUMAN 声明真实**。人工证据审核和访问时间外部登记仍是前置条件；不得把测试内的 MOCK_TEST_ONLY 元数据复制成真人记录。

冻结时 registration 需要 status=FROZEN、带时区的 registered_at、frozen_before_test_access=true、evidence_reference，并锁定 records_sha256。该 hash 是 `json.dumps(records, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()` 的 SHA-256，不包含 registration 自身。冻结文件和证据应留 Git/登记记录；不得事后回填“测试前冻结”。

```powershell
# 文件字节 hash；路径需替换为实际授权源码。
(Get-FileHash -Algorithm SHA256 -LiteralPath ./path/to/source.py).Hash.ToLowerInvariant()
# 查看 records 的冻结 hash；先完成真实记录，不会自动变更 FROZEN 状态。
& $Python -c "import hashlib,json,pathlib; m=json.loads(pathlib.Path('coderisk/experiment/datasets/research-v4/independent_references.json').read_bytes()); print(hashlib.sha256(json.dumps(m['records'],sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()).hexdigest())"
```

用于 source-disjoint 的 hash 与既有 Research V4 loader 一致：UTF-8/universal-newline 文本、带 `sha256:` 前缀。参考原始字节 hash 另外输出，CRLF/LF 相同文本会被识别为同一来源；这不是 token/canonical 去重，不能识别任意改名派生源码，仍需 source family 人工登记。

## 4. 查询数据与采样依赖

查询仍使用 Research V4 `dataset.json`，manual shard 的已有字段保留。增加 [`natural_reference_context`](../../coderisk/experiment/datasets/research-v4/templates/natural_reference_context.template.json)：authors/sources/families 各两个身份，template_status 和模板背景。查询两侧可以来自同一作者的已知变体；但不能与参考作者复用。必须对关系正例与自然相似负例分别真实复核。

查询缺少身份/模板背景只会 q 不可用，固定/规则基线仍可运行；已知跨 split 或参考/查询泄漏则直接报错，`--allow-development` 也不能豁免。检查包括既有 source_id/source_family_ids 的可用身份，并不只依赖新增字段。

同一面板先按 SHA256(seed:reference_id) 的稳定顺序贪心筛选，两对不能共享作者、source、family 或文本 hash。选择不看分数、不看查询标签，反转文件顺序不会改变选择。不是最大匹配，也不证明统计独立；模板导致相同文本被去复用可能改变样本分布，需报告拒绝数量、招募方式和重复来源敏感性。不得仅按保留下来的低相似分数建立参考池。

同一对内部允许两个 hash 相同，前提仍需真实独立关系审核。该规则不自动承认两段相同代码独立创作。跨面板/查询的已知身份复用始终拒绝，隔离声明还需外部证据。

## 5. 失败、短代码和模板处理

q 不可用的显式原因包括：

| 原因 | 行为 |
| --- | --- |
| PROBLEM_DISJOINT_TEST_COLD_START / COLD_START_NO_MATCHED_REFERENCE | 不估计新题 q，规则阈值回退 |
| INSUFFICIENT_DISJOINT_REFERENCE_PAIRS | 不通过依赖样本的两两组合填数量 |
| QUERY_IDENTITIES_UNDECLARED / TEMPLATE_CONTEXT_UNDECLARED | 等待来源/背景补齐 |
| PARSER_OR_NORMALIZATION_FALLBACK | 保留 raw 生产回退，实验 AST/canonical/mapping 不可用则 null |
| SHORT_EFFECTIVE_CODE | 非模板部分少于 41 token，不估计 q |
| TEMPLATE_DOMINATED | 精确注册模板覆盖任意一侧 >=0.5，不估计 q |
| VALIDATION_ALPHA_UNAVAILABLE | validation 可校准正负类不足，无 alpha，规则回退 |

模板复用现有精确 raw token 分段诊断（最小 8 token），只影响研究资格，不改变相似度或生产阈值；忽略短模板片段、无法识别改写模板等限制依旧存在。这个保守版选择暂不校准短题/高模板题，不能宣称已经解决最需要研究的自然相似误报场景。

## 6. 公平比较与冻结选择

三组共享同一 S 和同一 eligible/known-label/same-language 查询集：

1. FIXED：只在 validation 上，从固定候选网格最大化 F1，平局优先低 FPR/更高阈值。
2. RULE_DYNAMIC：直接使用现有规则题目画像阈值，不调参。
3. STATISTICAL_WITH_RULE_FALLBACK：q_smoothed <= alpha；q 或 alpha 不可用则使用 RULE_DYNAMIC。alpha 网格只在 validation 选择，需 q 可用正负类俱全，优化全 validation 策略（含回退）的 F1，平局低 FPR/更小 alpha。

ALL_TEST_POLICY 是主同查询策略比较，文件也包含 validation 诊断，阅读时必须筛 split=test。CALIBRATABLE_ONLY 是相同 q 可用且 alpha 冻结的补充子集，不能与全表比较为同等覆盖；各表都列实际 n。固定阈值无法选择时记 null/N=0，不用 test 补选。

输出 Precision/Recall/F1/FPR、NaturalSimilar FPR（仅 NATURAL_SIMILAR 分母）及 Suspicious Recall（仅 SUSPICIOUS 分母）；缺相应类则 N/A。FORMULA_VERSION、源码/配置/数据/参考 manifest hash、seed、Git 与工作树状态、运行时间及参数变化保存在产物中。不同题重复 pair 的指标仍是探索性的 pair 微平均，不提供依赖校正的显著性或总体误差保证。

默认正式运行还需既有双人标注、授权、题目隔离和匹配 config hash 的 evaluation_registration；不满足会阻断。allow-development 只允许探索查询集，正式资格计 0，不能放宽参考质量、泄漏或生产边界。

## 7. 本次真实运行结果

证据入口：[原始产物与验证](../../coderisk/experiment/evidence/natural-calibration-20261010/README.md)。当前 seed 91 对全为 synthetic；same-language Java/Python 分析 75（validation 35、test 40），16 对排除。不要求全量四子指标共同可用，故**不能直接与阶段 2 的 COMMON test 36 混比**。

可信独立参考 0、q 可用 0、alpha=null、formalEligiblePairs=0。固定 validation 选中阈值 0.3；规则阈值未变。test 自有合成数据实际观察如下，仅用于流程验证：

| 策略 | Test N | Precision | Recall | F1 | FPR | NaturalSimilar FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FIXED | 40 | 0.6875 | 0.9167 | 0.7857 | 0.6250 | 1.0000 |
| RULE_DYNAMIC | 40 | 0.7778 | 0.5833 | 0.6667 | 0.2500 | 0.5714 |
| STATISTICAL_WITH_RULE_FALLBACK | 40 | 0.7778 | 0.5833 | 0.6667 | 0.2500 | 0.5714 |

test 含 24 正类、16 负类，其中 NATURAL_SIMILAR 7；CALIBRATABLE_ONLY 全部 N=0 / N/A。统计策略完全等于规则策略，**没有统计校准改善证据**；规则降低合成 FPR 同时损失 Recall/F1，保留负结果。mathematical_contracts.json 的人工数字是纯代数测试，不是源码检测指标。

新测试 40 项通过，涵盖尾部契约、validation-only、模板分数不变、解析降级、真实文件读取/路径/授权/冻结、贪心去复用以及 query/panel/hash 泄漏。测试中的“人工声明”全部仅 MOCK_TEST_ONLY，不是数据集标注。更早红测试复现了异常 registration 类型、新增身份隔离漏检、CRLF/hash 命名空间及身份首尾空白缺口，随后最小修复。本轮不更改生产算法。

完整工作树测试结果、独立提交版本验证见 TEST_REPORT 和证据记录；后端/前端未修改，本阶段不冒充重新验证其构建或端到端。MySQL 实库仍待有效凭据，已有 H2 验证是历史结果。JPlag 不重跑，也不拼接 ConPlag 历史分数。

## 8. 复现命令与下一步

PowerShell，项目 Git 根目录 E:\ms。本机旧 analysis-service `.venv` 不可用，实际使用下列环境；其他机器按 README 建立可用环境，替换 Python 路径。

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/natural_similarity_calibration.py --help
# 输出目录必须未存在；这里只跑 seed 开发流程。
& $Python coderisk/experiment/natural_similarity_calibration.py --output output/natural-calibration-new-run --allow-development
& $Python -m pytest -q -p no:cacheprovider coderisk/analysis-service-python/tests/test_natural_similarity_calibration.py
# 完成真实参考、查询标注和方案冻结后，不加 allow-development：
& $Python coderisk/experiment/natural_similarity_calibration.py --config coderisk/configs/experiments/natural_calibration_v1.json --output output/natural-calibration-formal-new-run
```

不同协议/参数必须另存配置和输出目录，在 validation/development 完成选择后冻结，不覆盖已看过的 test。参数以 --help/冻结 JSON 为准；参考未准备好默认 formal 实际会报错，不产生伪正式结果。

结果目录：run_manifest/config/dataset_validation/selection/results 的 JSON；queries、reference_audit、excluded、metrics、predictions、failures、borderline、parser_fallbacks 的 CSV；REPORT.md。空 reference_audit.csv 表示 0 行，不是读取成功但隐藏参考。逐查询的 q_available/reasons 与预测 decision_source 是解释覆盖的关键。

下一步先选协议和题目，再收集每题/每语言至少 40 份作者/source/family 独立的授权代码，用不复用来源的 20 对构建参考；另外收集与参考不共享身份的独立查询负例、自然相似负例及已知变体正例，双人复核。数量只是默认最低分辨率，不保证可信性或充足功效。面板冻结/真实独立关系/新测试访问约束目前都是阻塞项；公开同题解、BCB/PoolC 标签或标题对齐不能直接代替它们。

可写论文：研究问题、定义、协议权衡、工程门禁、回退设计和 synthetic 流程观察。不能写：已证明减少真实误报、总体 FPR 控制、确认抄袭、完整语义等价、AI 代码检测或跨语言统计校准。本轮不接 Direct LLM，后续仍须授权、费用上限、dry-run、同背景和冻结测试；混合检测是可选展望。
