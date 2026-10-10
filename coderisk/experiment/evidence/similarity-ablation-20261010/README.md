# 隔离多维消融：synthetic 流程证据

2026-10-10 实际运行，由 `output/research-ablation-seed-20261010-r2` 原样复制。运行基线为 `e688a04` 加本批未提交实验代码；`run_manifest.json` 的源码 SHA-256 是完整身份依据，不能仅用基线 commit 复现新增 runner。

**DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK**。全部输入来自既有 91-case synthetic seed；本次不新增真实标签，不读取外部 30k 开发池，不重评 ConPlag/JPlag，不提高实验指标生产权重。formalEligiblePairs=0。默认正式模式因缺真人复核/冻结注册而实际被拒绝，显式 allow-development 才完成。

本轮范围分析 75 对，16 对不合格/未知标签/跨语言等排除；COMMON 68（validation 32、test 36），canonical 回退 7（3/4）。主表同样本比较，不以 AVAILABLE 补集拼接结果。test 中 21 正例/15 负例来自合成标签，7 个自然相似负例也不是可信独立课堂数据。

| 产物 | 用途 |
| --- | --- |
| config.json / run_manifest.json / dataset_validation.json | 精确参数、版本、源码/数据 hash、seed、UTC、Git dirty 状态、质量阻塞与覆盖 |
| scores.csv / selection.json | 原始分量及 validation-only 选参/低 FPR 工作点 |
| metrics.csv / REPORT.md | 全部 14 方法，COMMON 主表、AVAILABLE 诊断、低 FPR 分支；null 不填 0 |
| predictions.csv / results.json | 每个方法×pair 的分数、阈值、label、correct、共同样本标记与耗时 |
| coverage.csv / excluded.csv / parser_fallbacks.csv | 支持度、排除和解析/绑定降级，避免只报告可解析样例 |
| failures.csv / borderline.csv | 实际 test 失败/边界；行数不是独立 pair 数，按 pair_id 去重分析 |
| retrieval.csv | 14×3 条 Recall@K 均 N/A，当前没有完整标注 query pool |
| rename_stability.csv | 自有 6 个正确性 fixture、48 个置换、672 条方法分数；参照为 identical self pair，不计关系准确率 |
| research-ablation-focused-r2.xml | 19 项新实验契约/seed 集成测试通过 |
| research-ablation-full-r1.xml | 当前完整工作树 337 项通过，1 条既有 warning；含其他未提交任务测试，不等同 clean HEAD 测试数 |

COMMON test 中，PICAS_FIXED F1=.7843、rule dynamic=.6842、validation-offset dynamic=.8372，canonical-only=.8718。不能声称完整融合最佳；规则动态 FPR 从 .6667 到 .2667 的同时 Recall 从 .9524 到 .6190。这里只说明流程可用和合成数据上的权衡，不证明真实误报减少。

改名 fixture 的 AST/canonical/mapping delta 均为 0，而 raw/完整分会改变。这是有限、合法置换的分数敏感性观察，不是语义等价、抄袭或 AI 来源判定。

详细定义、PowerShell 命令、论文使用限制和后续可信数据条件见 [阶段 2 说明](../../../../coderisk_docs/research/SIMILARITY_ABLATION.md)。后端/前端本轮无改动，未重跑；MySQL 实库仍待有效凭据。不得将上次 H2/build 结果冒充本次新验证。
