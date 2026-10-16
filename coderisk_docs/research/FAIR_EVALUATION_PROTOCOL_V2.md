# S4 公平评测协议 V2：保留生产，冻结实验

本文件细化既有 [DATA_PROTOCOL](../proposal/DATA_PROTOCOL.md)、[FAIR_EVALUATION](../proposal/FAIR_EVALUATION.md)、research_protocol.py、similarity_ablation.py、natural_similarity_calibration.py。**不创建第二套数据schema，不覆盖历史配置或标签，不宣称已经有正式数据。**

## 1. 三层证据

SYNTHETIC_DEVELOPMENT用于单测/探针/流程；PUBLIC_PILOT按发布者标签及既有已观察test描述；FORMAL仅在来源许可、真实双人关系复核、功能/模板、父版本或独立依据、冻结及隔离均满足后成立。Formal-ready的自动检查只验证声明结构和隔离，不认证同意书真伪/身份/独立性；必须保留人类审计。

默认生产分数/阈值原样。实验固定权重/offset/q/LLM在configs/experiments中冻结，不写回生产。公式文件和源码hash存入run manifest；缺指标为null，不以0、raw或IR假冒canonical/AST。

## 2. 双重问题：性质与效果

RQ1a：同一受限G轨道的完整C是否恒等（独立gold/逆/复合、所有拒绝分母）。RQ1b：规范化是否损失区分能力（自有机制，不等于真实FPR；真实已知关系正负例另测）。

RQ2：在同一query集上固定、原规则动态、独立分布q的误报—召回如何变化。不能因synthetic低FPR就声称自然误报改善；题目画像风险指标是启发式，不是实测自然相似概率。

## 3. 数据与冻结前检

1. source_registry/pair_annotations/split_registry沿用；代码/题面/模板真实授权、来源版本、匿名家族和SHA可追踪。功能未核/标签未决/placeholder/AI provenance不全排正式池。
2. problem/source/family/hash连通分组，不跨validation/test；group数量也要报告。重复题翻译统一ID，近重复来源不因hash不同而分家族。
3. 首次test分析前冻结：数据/标签/schema/config/源码hash，seed，公式/算法/dataset版本，阈值/权重/alpha候选、FPR目标、缺指标处理、主支持集、baseline模板/minTokens、bootstrap单位及预算。日期、责任人、真实记录索引写evaluation_registration。
4. 先loader校验，再 `check_formal_readiness.py --require-ready`。它复用loader、connected_groups及existing formal/quality blockers，额外查负例双来源独立依据、功能/模板/已知父版本和空正式池；excluded也显示原因，不静默消失。附加metadata在现有provenance/annotation扩展字段中。
5. 改源码/配置/标签后重新记录版本；看过test再迭代则移为exploratory并取得新holdout。预登记不能追溯伪填。

## 4. 多维消融公平口径

复用14方法：raw/AST/canonical/mapping单项、6个等权两两、all-equal、production-fixed、production-rule、validation-only offset。各方法阈值只能validation选择；生产rule行不被“公平调参”隐性改掉。报告原rule与offset分别的召回/FPR代价。

COMMON为所有比较方法可用的同一pair；AVAILABLE是各方法覆盖诊断，不直接排行优劣。同时报告总体覆盖、parser/normalization fallback、语言/长度/题型/模板分层、排除原因。若JPlag参与，分别ALL_PICAS与MATCHED_JPLAG，缺JPlag为不可用而非0；不合并不同源码版本/不同背景的旧新score。

Precision=TP/(TP+FP)，Recall=TP/(TP+FN)，FPR=FP/(FP+TN)，NaturalSimilar FPR只以该可信负例子集作分母。分母0时N/A。PR面积采用非插值AP并列成组，明确不同于梯形积分；动态策略报告score与margin排名口径。固定FPR下Recall只在validation选操作点，test实际FPR另列，不能保证population FPR≤目标。

Recall@K只适用于有完整标注pool、query/pool大小和候选身份的检索任务；任意pair集合输出N/A。分析耗时含共享特征提取/可用性检查；aggregation耗时不当作独立算法端到端时间。

区间按题目/家族连通组bootstrap，报告组数、seed、repeats和配对差值；同一个代码多pair不是IID。很少组时区间不足以正式推断，报告不稳定。已有run_fair_evaluation.py提供cluster_intervals；本轮不捏造新真实区间/显著性。

## 5. 题目q的两种协议

`q_p(s)=Pr(S_independent,p ≥ s)`仅指可信独立解答达到该相似度的上尾概率；经验频率及+1平滑不是抄袭概率、自动校准p-value或语义判断。来自同题的不同提交不自动独立。

| 协议 | 可答的问题 | 必须公开的限制 |
| --- | --- | --- |
| VALIDATION_PROBLEMS_ONLY（默认） | 新题冷启动时整体策略如何表现 | test题无同题reference，q不可用、规则回退；不证明q改善test |
| PREREGISTERED_CONTEXT_PANEL（另冻配置） | 有同题独立参考面板的条件收益/代价 | 题目可同，参考/query作者/来源/家族/hash隔离；不能叫reference/test problem-disjoint |

reference关系由两名真人及过程证据确认；match去重减少作者/源/家族/hash复用但不是exchangeability证明。有效代码<41 token、模板覆盖≥.5、解析失败或同context参考<20 disjoint pair会拒绝q（当前配置）；不能为test改这些门槛。缺q/alpha都用原规则回退，并分表CALIBRATABLE_ONLY与ALL_TEST_POLICY及每条原因。若全部回退，统计收益为未验证。

外部公共未标注/许可证待定只做exploratory分布，不冒充reference/负例。新的正式参考与现有被看过test不共享身份；样本不足要BLOCKED，不用合成探针填空。

## 6. Baseline与LLM

JPlag固定版本/Java/parser/minTokens/模板，按pair_id对齐有效共同集、输出失败/不适用原因。Dolos尚无新真实运行，不写已完成。DirectLLM继续mock/dry-run或明确授权离线导入：同题/模板背景、冻结提示/schema、成本/延迟/失败/证据及重复稳定性；真实执行和上传需另授权。Hybrid需完整pool和Recall@K门禁，当前blocked，不纳入默认业务。

## 7. 运行顺序及验收

从根目录，先真实数据校验/前检，再 similarity_ablation.py 和 natural_similarity_calibration.py（正式时**不加**allow-development），基线用run_fair_evaluation.py/research_v4_jplag.py现有入口，具体参数先--help。独立数据配置文件不能仍指seed，输出必须新目录。合成复现命令见 [总导航](OPENING_RESEARCH_PACKAGE.md)。

每次完整归档包括run/config/source/data SHA、UTC时间、seed、环境、selection、逐pair score/prediction/warning、coverage、metrics/AP/low-FPR、baseline/ablation/failure/borderline、reference_audit和人工冻结索引。若日志/manifest缺失或run失败，仅标失败，不从部分CSV择优摘成绩。

当前状态：工具及示例运行可复现，**Formal evaluation BLOCKED**。80—150真实pair只是目标；可信q和自然误报效果需更强独立参考。本轮不修改生产评分或提高V4权重。
