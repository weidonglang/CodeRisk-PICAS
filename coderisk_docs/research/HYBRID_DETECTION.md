# 隔离混合复核实验

2026-10-11 研究阶段 5。已实现可关闭的离线原型及门禁，**未完成真实混合检测效果验证**，不接入生产业务。

## 流程和边界

`完整标注候选池 → 现有 PICAS 排序 → validation 选 K → 授权离线模型复核 → 原文引文核对 → 人工判断`。

不增加相似度算法，不改变生产公式、API、数据库或 V4 权重。模型不是裁判；工具不调用网络、不读取密钥、不执行源码。不能认定抄袭、作弊、完整语义等价或 AI 来源。

生产分数/阈值读取现有分析器；按 risk margin、weighted score、pair_id 确定性排序。同一 query 的题目背景、语言和阈值必须一致。解析/规范化降级仍保留 raw 回退候选，不得为了高 Recall 先删低分或 unsupported 候选。

## 完整候选池要求

给每条已有 case 增加以下 metadata（模板位于 `experiment/templates/hybrid_query_pool.template.json`）：

| 字段 | 要求 |
| --- | --- |
| retrieval_query_id | 冻结 query ID，所有对应候选一致，不跨题目/split |
| query_source_sha256 | 精确等于 loader 的 code_a_sha256 或 code_b_sha256，保留其 hash 格式 |
| retrieval_pool_complete | 只有该预先声明有限池的全部候选及关系标签已登记，才填 true |
| retrieval_pool_size | 实际候选数量，不能只填支持语法或高分样本数量 |

目标 hash 不重复、不含自身；pair_id 唯一；每个候选必须有可信已知标签和可用生产回退分数。题目/模板背景 hash 自动计算。不满足时整个实验阻断，而不是缩小池后报告召回。validator 检查声明一致性，不能证明操作者没有遗漏未声明文件；池目录、来源和冻结清单还需人工核验。

默认 K 网格 1/3/5/10、目标 validation macro Recall@K ≥0.95、至少 10 个含正例 query。只在 validation 选择满足目标的最小 K，test 不参与；这是观测工作点，非置信下界或总体召回保证。全负 query 不进入 macro Recall 的分母，仍保留在队列/指标中。真实数据还须 problem/source/hash 分离。

候选漏掉的派生关系无法被后续模型找回。逐 query、采用相同分母时，混合召回不可能超过候选召回；macro Recall@K 不能直接与全局 micro Recall 数值等同。

## 真实混合导入的额外门禁

即使 `--allow-development`，import 仍要求此前真实 Direct LLM 的可靠基线；mock 不能绕过。基线需：

1. 正式冻结数据、import 模式、非空真实响应、formalBlockers 为空，测试未参与选参。
2. 当前数据 hash、生产源码 hash、模型/参数相同；三方共同 test 至少 30 对（配置可在冻结前设置，不能看 test 后降低要求）。
3. 真人核验的批准记录，绑定基线 run_manifest hash，并说明数据、许可、失败分析、覆盖和费用记录为何足以支持进一步实验。

批准模板为 `experiment/templates/hybrid_baseline_review.template.json`，默认 pending/null，不是真人复核证据。离线文件和人工声明不能外部证明提供方真的执行了模型，必须核对原始运行凭证。

混合提示词独立版本 `hybrid-review-1.0`，包含 PICAS 分量、阈值和降级提示但不含标签。不能拿 Direct LLM 的响应当混合响应；请求 hash 会不同。共享阶段 4 的严格 Schema、授权、费用/Token 门禁、缓存、重复汇总及原文行号核对。提示词可能受 PICAS 提示的锚定影响，须与 Direct LLM 公平比较。

## 运行与产物

仓库根目录 PowerShell，先 `--help`；输出目录必须未存在：

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/hybrid_review.py --help
& $Python coderisk/experiment/hybrid_review.py --output output/hybrid-mock-new --allow-development
# 取得完整池、真实模型基线和人工批准后，才使用自己的冻结配置与授权离线响应：
& $Python coderisk/experiment/hybrid_review.py --config path/to/frozen-hybrid-config.json --output output/hybrid-import-new --mode import --baseline-dir path/to/real-direct-baseline --baseline-review path/to/human-approval.json --responses path/to/hybrid-responses.jsonl --cache-dir output/hybrid-cache
```

`--export-prompts` 仅本地导出已授权选中代码，不是远程使用许可。默认 mock；真实 import 不自动付费。配置和模板路径不能用生产任务代替实验。

| 输出 | 用途 |
| --- | --- |
| pool_audit.json / pool_failures.csv | 完整池缺口与阻断原因 |
| candidate_recall.csv / selection.json | 每个 split/K 的 macro Recall；仅 validation 的 K 工作点 |
| scores.jsonl / requests.jsonl | 现有 PICAS 分量、候选、请求 hash |
| model_outputs.jsonl / responses_template.jsonl | 逐次模型输出与待填响应结构；模板不是模型数据 |
| human_review_queue.csv | SELECTED / NOT_SELECTED_UNASSESSED / PIPELINE_BLOCKED，模型状态与人工待核验状态 |
| pipeline_evaluation.json / pipeline_metrics.csv | 仅完整有效模型响应后计算，全池含候选遗漏；缺选中响应则 N/A |
| REPORT.md / run_manifest.json | 汇总、版本/模型/参数/源码/数据/配置 hash、时刻、预算与门禁 |

模型输出 NO_REVIEW_SIGNAL 和未选中均不证明独立创作。人工状态不由模型改成“完成”。端到端工作点只由选中 validation 样本决定；若无两类或选中响应不完整，不输出假精确率。全池未选中样本在复核队列检测指标中视为未标记，正例保留为 FN；这不是关系判定。

## 实际验证及下一步

27 项新测试通过：缺字段、错 hash/数量、重复目标、背景/语言/split 冲突、缺标签/分数阻断；fallback 保留；tie 固定；仅 validation 选 K；候选遗漏计入分母；未知候选身份不能悄悄缩小统计；预算/Schema 复用阶段 4 契约。

测试专用完整池的 mock 队列选 K=3、6 对/18 请求，模型可评分与网络调用均 0；这是控制流程测试，非 benchmark。基线“批准”测试对象显式 MOCK_TEST_ONLY，不是真人审核。

现有 seed 的 mock 与 import 门禁实际运行：91 输入、75 分析、16 排除；缺完整 query pool，status=BLOCKED_INCOMPLETE_QUERY_POOLS，K=null、Recall@K=N/A、选中 0、真实响应/费用 0。真实基线门禁也未满足。受控记录见 [阶段 5 证据](../../coderisk/experiment/evidence/hybrid-review-20261011/README.md)。

后续先补授权、可信关系标签与完整冻结 query pool，再做 Direct LLM 三方共同评测和人工批准，最后评估混合召回、失败、稳定性与成本。现在只能在论文中写原型设计、实现契约和未验证限制，不能写混合优越性或真实检测效果。
