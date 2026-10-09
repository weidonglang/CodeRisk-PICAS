# 前三项推进记录：新数据、融合诊断、任务可靠性

更新：2026-10-09。本文件按实际产物区分完成项与待验证项，不将 AI 工作登记为独立真人复核。

## 1. 新数据与复核材料

已从[作者仓库](https://github.com/oscarkarnalim/sourcecodeplagiarismdataset)取得 IR-Plag，固定提交 `f07e95120680b25f78659ed63cd6130fd05b2df8`，验证 ZIP、README、LICENSE 的 SHA-256，并逐文件校验。原始源码仅保存在本地忽略目录，没有执行或重新发布。

| 实际登记项 | 数量或状态 |
| --- | --- |
| Java 源码 | 467 个逻辑文件，453 个不同字节哈希 |
| 入门题 | 7 道，有论文第 3.2 节题意与构建过程 |
| 原始参考实现 | 7 份；不是公共教师起始模板 |
| 派生改写 | 355 对“原始实现—派生实现”，发布者有意构建的派生关系 |
| 声称独立编写 | 105 对“原始实现—独立实现” |
| 已知争议负例 | 隔离 10 对；两侧有争议的参与者提交一并隔离 |
| 未涉及该公开争议的负例候选 | 95 对，仍保留发布者协议依据与限制 |
| 新增盲审材料 | 52 对：每题每类按哈希选 3 对，共 42 对，加 10 对争议样本 |
| 本地真人复核、正式实验资格、检测器评分 | 均为 0 |

[论文](https://www.dcs.warwick.ac.uk/~msj/publications/fulltext/karnalim_budi_toba_joy_infed_2019.pdf)第 3.2 节说明，非派生组在看不到其他解答的条件下自行完成题目，派生组根据原始实现改写。独立组在家完成，信任依赖参与者诚信；发布者还说明部分源码可能有输出错误。因此，这是一组有公开构建协议的研究数据，不是本地验证正确的真实作弊事件，也不能将所有独立关系自动标为 NATURAL_SIMILAR。

[作者公开争议](https://github.com/oscarkarnalim/sourcecodeplagiarismdataset/issues/3)涉及 case-02、03、04、06、07 的非派生提交 13 与 15。隔离规则在评分前确定，不按检测分数挑选“干净负例”。原始公开标签另存，不覆盖 UNCERTAIN 的本地复核标签。

已审计重复字节和此前公开数据的哈希交集：与前批 3,865 条登记没有字节哈希重合。14 个重复逻辑文件不能当作独立新增证据。已知争议排除后，按字节代码对去重为 342 对派生、95 对独立候选，仍非本地正式标签。重复组及一对字节相同的派生参考对见 `quality_summary.json`；后续统计保留全部来源映射。

许可证亦记录两类依据：仓库 LICENSE 为 Apache-2.0，论文描述参与者同意非营利研究用途，原始参考实现来自教材。当前只提交元数据和采集工具；不将仓库许可证解释为自动解决所有第三方源码和题面的再分发许可。

因同批参与者跨七题出现，分集暂使用一个全局泄漏阻断组；不将七题随机拆成验证/测试。IR-Plag 暂保持未评分，可作为外部研究评测候选；来源已阅读和审计，不声称完全未接触过该数据。正式用途仍需要先冻结参数选择、争议处置、去重和评测口径。

复核者分别打开本地工作台、使用实际身份登记、提供关系及自然相似依据后，再合并记录。代码原文可能通过标识符暴露上游类别，目录和公开标签隐藏不能保证彻底盲法；应记录既往接触。不能复制同一份意见并换两个名字来满足双人要求。

本地入口：`coderisk/data/public-datasets/irplag-20261009/review/workbench.html`。元数据入口：[新数据证据](../../coderisk/experiment/evidence/irplag-intake-20261009/manifest.json)。

从仓库根目录运行；输出必须是新目录，既有目录只能校验：

```powershell
python coderisk/experiment/acquire_irplag.py
python coderisk/experiment/acquire_irplag.py --verify-only
python coderisk/experiment/prepare_irplag_review.py --output output/irplag-review
python coderisk/experiment/audit_irplag.py --output output/irplag-quality.json
```

相同本地复核清单和工作台可校验复用；内容不同则保留旧文件，使用新的 `--intake` 目录。登记和复核包可复现，不意味着已完成实际复核。

## 2. 融合与规范化负结果

新增诊断器读取已冻结 ConPlag 的两种源码视图及原阈值，不重跑检测、不拟合参数、不改历史快照。逐对保存可重构的分量贡献、预测变化、按类别和划分的 CSV 汇总，以及实际生成的图表。

设 R 为 raw token 分数，A 为 AST 分数，C 为 canonical 分数，M 为标识符映射分数。现行融合 F = .20R + .20A + .45C + .15M；无规范化对照 B = .50R + .50A。

```text
F − B = .45(C − .50(R+A)) + .15(M − .50(R+A))
```

逐对检验该等式，容差为已保存六位小数造成的 2×10⁻⁶。解析回退对的两项贡献均为零，不归因于规范化。

| 既有测试集，全 PICAS 对（各 627 对） | full / 无规范化 F1 | full / 无规范化漏检数 | full / 无规范化误报数 |
| --- | --- | --- | --- |
| 原始视图 version_1 | 0.5543 / 0.5985 | 90 / 82 | 29 / 28 |
| 去模板视图 version_2 | 0.6974 / 0.7352 | 58 / 46 | 34 / 39 |

这里是 PICAS 全集合，**不是**此前去模板 JPlag 的 625 对共同集合。两种方法保留各自验证集选择的阈值，预测差异同时受阈值影响，不能称为单分量因果消融。

原始视图正例 164 对中，118 对因融合而降分、11 对升分；规范化贡献均值约 −0.0609，映射贡献约 −0.0071。去模板正例中规范化贡献均值约 −0.0639，映射约 +0.0087。负例也大多降分。结论是“对表面变换具有某种不变性”不等于“全体派生样本应在固定融合中取得更高分”。

已查源码：raw、AST、canonical 均使用自适应 n-gram 集合 Jaccard，`_sequence_similarity` 名称不能解释为最长公共序列或语义相似度；映射为覆盖/一致性启发式。仍有以下待验证机制：作用域路径及声明次序对结构改写的敏感性；AST 节点摘要与 token 表征分布差异；短题的公共语法；字段权重及阈值在题型间迁移。分量分布支持继续检验这些假设，尚不能证明某一项是唯一原因。

本轮没有根据已观察测试结果调整生产权重或动态阈值。下一步先用独立、自有开发探针检查重命名、无关局部声明、独立简单题、公共模板和解析回退；再限定旧验证集选择规则，冻结后对外部候选池评分。若不能证明融合增益，论文应报告负结果、适用边界和复核证据价值，不把结果写成已优于基线。

[分解汇总](../../coderisk/experiment/evidence/fusion-diagnosis-20261009/component_summary.csv) · [原阈值决策](../../coderisk/experiment/evidence/fusion-diagnosis-20261009/frozen_decision_summary.csv) · [图表](../../coderisk/experiment/evidence/fusion-diagnosis-20261009/component_contributions.png)

```powershell
python coderisk/experiment/diagnose_fusion.py --output output/fusion-diagnosis
```

## 3. 异步任务、超时和恢复

已实现的本地单后端执行路径：

1. 创建任务限制为 2–100 个不同提交，保存时按 ID 排序；100 个提交最多产生 4,950 对，不一次构造全部配对对象。
2. 启动用数据库条件更新认领 PENDING/PARTIAL/FAILED。RUNNING、FINISHED 的重复调用不重复调度。接口返回受理时的完整任务对象，状态为 RUNNING，包含等待线程的情况。
3. 默认 2 个工作线程、8 个等待任务。队列满则返回 503 / TASK_CAPACITY_EXCEEDED，恢复此前可重试状态。
4. 默认单次执行时间预算 900 秒，在新代码对开始前检查；已开始的分析调用受连接/读取超时限制，默认各 60 秒。因此预算不是强制中止 Python 分析的硬截止时间，不声称终止远端 CPU 工作。
5. 逐对保存成功结果、失败原因、失败次数与最近失败时间；失败后继续其他代码对。重试跳过已有结果，失败历史保留并标记恢复。
6. 服务启动时将遗留 RUNNING 按持久化结果数恢复为 PARTIAL/FAILED；全部已存则 FINISHED。计数从结果表重建，覆盖“结果已提交但进度尚未更新时崩溃”的情况。用户随后手动重试。
7. 前端每两秒轮询运行中的任务，离开页面清理轮询；支持进度、错误历史、重试及结果分页。报告标明生成时状态、覆盖数和未完成提示。风险展示分说明为非经验概率，接口旧字段保持兼容。

```text
CODERISK_TASK_WORKERS=2                 # 1–16
CODERISK_TASK_QUEUE_CAPACITY=8          # 0–100
CODERISK_TASK_TIME_BUDGET_SECONDS=900   # 1–7200
CODERISK_ANALYSIS_TIMEOUT_SECONDS=60
```

适用范围：单个后端实例连接该数据库。尚未实现分布式租约、自动重新投递、取消接口、硬中断 Python 分析、缓存或并行分析同任务内的代码对。不能同时启动多个后端共享数据库，否则启动恢复可能影响另一实例。单任务上限是资源保护配置，不是已验证的 100 份性能承诺。

真实联调使用隔离持久化 H2、真实 FastAPI 和自有合成 Python 文件。10、20、50 份运行以及临时缺失文件后的部分失败/恢复记录见[运行证据](../../coderisk/experiment/evidence/async-execution-20261009/runtime.json)。不同机器、源码长度、解析类型和并发程度会改变时间；这不是检测准确率或服务 SLA。

复现时须自行启动隔离服务；脚本会建立自有合成题目与提交，并仅临时移走该隔离上传根目录内的一份文件，最终恢复：

```powershell
python coderisk/experiment/verify_async_runtime.py --base-url http://127.0.0.1:18080/api --upload-root E:/ms/.tmp/async-live/uploads --output output/async-runtime.json
```

## 4. 对毕设的作用与剩余工作

本轮增加了带协议与题意的简单题候选数据、可解释的负结果分析以及可演示的异步恢复能力。开题材料可以据此具体说明前期工作、研究风险和下一阶段验证方法。

尚未完成：真人独立关系/自然相似复核，生产融合改善的外部证明，固定/动态阈值的真实简单题受控比较，C/HTML 可靠关系标签及同口径基线，MySQL 实库迁移验证，以及学校模板/导师审批。不能将上述工程与数据接收直接换算成毕业论文已完成比例。
