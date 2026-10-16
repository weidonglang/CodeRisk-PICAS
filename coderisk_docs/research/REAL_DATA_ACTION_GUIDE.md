# S4 首批真实数据：从申请到冻结的中文操作教程

本轮能完成工具，不能代替你取得授权、邀请真人复核或确认独立创作。**当前正式核心pair=0、可信独立参考pair=0**；92,513只是公开/候选登记。目标4—8题流程试点、随后12—20题/80—150对，是待完成计划，不是本轮数据规模。

## 1. 先收什么，别先凑两万对

先选Java–Java、Python–Python同题：simple_io、array_loop、sort_template、string_processing、dfs_graph/bfs_graph、dp_variant、simulation。第一批至少含两类独立原始解答、共享题面/模板的独立解答、已知父版本改名/格式变化和unsupported边界。不要按检测得分挑高分“自然相似”负例。

4—8题时优先每题找4—6位自愿作者的原始解答，记录是否看过彼此代码和共用材料；这是**采集计划，不是现有样本**。邀请不能得到真实独立性证据时标UNCERTAIN，不补填。80—150个pair不能替代来源/题目数；同一个原实现的百次改写仍是一个家族。

已知改写可从自愿授权的原始代码产生：变量/函数/参数名、格式；保存父源码和操作日志，source family相同。这些是受控派生关系，不是学生违规样本。复杂local_reorder/split_merge需实测功能，不能因规范化高分就假设等价。AI改写是可选附组，不能冒充manual。

## 2. 怎么取得来源与授权

向课程教师/作者发送下面的**申请草稿**，不是已批准的授权书：

> 我正在做“编程作业代码相似风险辅助复核”的本科研究，拟使用您自愿提供的题面、模板和代码。不会自动认定违规；代码默认只在本地分析，不执行未知上传，不向模型或第三方上传。请分别确认：可否用于本地研究、可否运行功能测试、可否发表脱敏片段/统计、可否公开原始代码、保存期限及撤回方式。拒绝或不参与不产生学习评价后果。学校伦理/课程政策适用时先办理审批。

由真实责任人确认范围和日期。私下保存真实作者、授权原件和身份对应表，仓库只用匿名ID/授权索引。授权分析不等于授权公开/LLM上传/功能执行；各项分开。公开代码保存精确文件/commit URL、许可证原文/版本、下载时间，必要时联系权利人。MIT只覆盖本项目自有代码，**不替第三方数据授权**。许可不明的PoolC等继续隔离，不把公开可见当授权。

## 3. 文件放哪里

沿用 [DATA_PROTOCOL](../proposal/DATA_PROTOCOL.md) 和已有schema/loader，不新造一套标签格式。建议真实集合使用独立 `coderisk/experiment/datasets/graduation-v1/`；私有材料放不公开的 `coderisk/data/private-research/` 或校方许可目录（先检查.gitignore，不把身份/代码加入Git）。开发seed永远留在 research-v4，不改名伪装新test。

```text
graduation-v1/
  dataset.json                 # 新集合清单，sources只登记本集合
  case.schema.json             # 从现有schema复制，版本const对应新集合；保留字段规则
  DATA_CARD.md                 # 来源、授权、覆盖、限制和真实review状态
  pairs/manual_cases.json      # {"cases": [...]}，沿用RESEARCH_V4_PAIRS_JSON
  samples/manual/<problem>/<source_record>.py 或 .java
  samples/ai_assisted/<problem>/<source_record>...
  samples/external/<problem>/<source_record>...
  review/                      # 非公开或匿名化A/B首次意见、合并及裁决索引
  functional/                  # 已授权隔离测试的日志、题目测试版本、输出
```

manifest、代码和review受许可限制；未经允许不git add/push。不要修改既有历史case的标签/版本以迁移成绩。

新 `dataset.json` 使用现有 `RESEARCH_V4_PAIRS_JSON` source、相对路径和dataset_version；可参考 research-v4/dataset.json 的同类source，**只保留本集合来源**，不自动夹带seed。`pairs/manual_cases.json`初始为空，清单应明确AWAITING_REVIEW。schema的seed版本const不直接适用于新集合：复制后只更新本集合版本，不修改历史schema/既有seed。冻结配置`datasetManifest`指向新集合，不能仍用默认seed路径。已有 [目录指南](../../coderisk/experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md) 详细解释字段与路径。

## 4. 每份源码先登记

使用 [source_registry.csv](../proposal/templates/source_registry.csv)：源码版本ID、题目ID、来源家族ID、语言、来源/commit/私有索引、授权索引、是否可再分发、采集日期、路径、SHA、功能日志索引。作者身份仅私下保存。题目翻译/措辞变化用同一个problem_id；一个原实现的人工/AI/格式变体都同source_family_id。

SHA按当前loader读取UTF-8文本后的内容计算；原始字节SHA与编码转换记录另存，不能混用两种口径。路径必须存在，录入工具会计算hash并列待确认字段，不能自动判断授权或独立性。

从仓库根目录先`--help`，然后执行下面的**待替换示例**，不直接把例子ID/许可声明当事实：

```powershell
$Python = (Resolve-Path ./coderisk/analysis-service-python/.venv/Scripts/python.exe).Path
& $Python coderisk/experiment/add_research_v4_case.py --help
& $Python coderisk/experiment/add_research_v4_case.py `
  --dataset-root coderisk/experiment/datasets/graduation-v1 `
  --dataset-version coderisk-graduation-prototype-0.1 `
  --pair-id YOUR-PAIR-ID --problem-id YOUR-PROBLEM-ID --problem-type array_loop `
  --problem-group G2 --dataset-split validation --source-id YOUR-ANON-SOURCE-ID `
  --source-type manual --experiment-label UNCERTAIN --case-type INDEPENDENT_SOLUTION `
  --language-a python --language-b python `
  --code-a samples/manual/YOUR-PROBLEM-ID/A.py --code-b samples/manual/YOUR-PROBLEM-ID/B.py `
  --title '实际题名' --description '实际题面' `
  --provenance-source '实际非识别性来源索引' --license-or-authorization '实际授权文件索引' `
  --notes '待真人独立复核和功能核验'
# 先检查打印的entry及待确认项；确认后用同命令加 --append。
# 不在待审阶段加 --eligible-for-core-metrics。
```

## 5. 标签与双人盲审

研究标签是关系而非处分：已知派生TRANSFORMED/复制SIMILAR；独立依据充分为INDEPENDENT；共享题目/模板且独立依据充分为NATURAL_SIMILAR；证据不足/分歧/功能不明为UNCERTAIN。新增正式数据不以“SUSPICIOUS”或高分代替已知关系。case_type描述变换/场景，与正负关系分开。

使用 [pair_annotations.csv](../proposal/templates/pair_annotations.csv)，保留A/B首次意见。现有 `prepare_annotation_workbench.py` 和 `annotation_workbench.html` 能制作匿名blind batch和合并两个JSON；先`--help`，按 [工作台教程](../proposal/DATA_REVIEW_WORKBENCH.md)操作。**两位不同实际真人**在不见检测分数、对方意见/公开标签的情况下各自审查来源、父版本/独立记录和功能证据。AI只能技术辅助，不能填HUMAN。分歧记录裁决者与依据，不可偷偷覆盖首次意见；未解决置UNCERTAIN且false。

“来自不同repo”“同一道题的不同提交”“同班不同学号”都不足以证明独立。负例需两个不同原始来源家族、是否看过对方代码/共享教程的真实记录、共同模板与来源说明，并写入 `annotation.independence_evidence` 索引。若知道作者互相参考，不能标独立。

## 6. 功能与附加metadata

业务检测不执行上传代码。只有来源明确、授权覆盖且受控隔离的功能验证才能由你/复核者执行；保存编译/测试命令、环境、题目测试版本、输入输出、通过/失败。`functional_check_status=PASSED`不能只靠目视/模型回答；无法验证置NOT_RUN/FAILED并排除正式主指标，可保留失败分析。

除现有fields，本轮preflight使用**现有可扩展对象中的附加字段**，模板在 `experiment/datasets/research-v4/templates/opening_review_extension.template.json`：

- `provenance.manual_check_status`、`functional_check_status`：实际审查和测试状态。
- `provenance.template_status=NONE/REGISTERED`：明确无共同模板或有登记模板；REGISTERED须`annotation.shared_template_ref`，模板内容/语言/来源按既有question/context协议登记。
- `provenance.parent_source_ref`：已知改写父版本/操作日志的真实索引；与source registry关联。
- `annotation.independence_evidence`：独立负例依据；不是“算法不同分”或空白勾选。
- `source_family_ids`、双HUMAN ID/type、`independence_confirmed`、AGREED、label、日期、label_basis、functional_evidence：沿用既有正式规则。

AI组另需model_name、完整提示/版本/参数、带时区generation_time、授权范围、人工VERIFIED、功能PASSED、父版本和家族；不能仅因为用了AI就标派生/违规，已知的操作记录才支持关系标签。external需来源URL/commit、许可证副本及再分发范围。placeholder、seed、未授权/单审/功能未验永远不被脚本自动提升资格。

## 7. 防泄漏划分及冻结

共享problem/source/family/hash的pair传递合并为连通组；同组不得跨validation/test。先登记而不读检测分，再固定seed生成方案：

```powershell
& $Python coderisk/experiment/research_protocol.py `
  --manifest coderisk/experiment/datasets/graduation-v1/dataset.json `
  --output output/graduation-split-proposal-NEW.json --seed 20261011
```

该脚本只提出方案，状态REVIEW_REQUIRED_NOT_PREREGISTERED，不编辑样本。真人核查覆盖/连通组，使用split_registry.csv记录理由/时间，确认后才更新条目并标preregistered。不可反复选seed到方法赢。测试数据已经看过得分就属于探索，下一轮需要新的holdout。

在**首次读取新test分数之前**冻结manifest/来源/标签、配置/源码SHA、模板设置、selection规则、baseline版本/参数、统计方案与日期。evaluation_registration要求FROZEN、config_sha256、registered_at、reference，后者指真实冻结记录，不能编造导师批准。单独复制实验配置指向新manifest；生产配置/公式不变。完整步骤见 [公平协议V2](FAIR_EVALUATION_PROTOCOL_V2.md)。

## 8. 一键查缺及统计参考

```powershell
& $Python coderisk/experiment/validate_research_v4_dataset.py `
  --manifest coderisk/experiment/datasets/graduation-v1/dataset.json --output-dir output/graduation-validate-NEW
& $Python coderisk/experiment/check_formal_readiness.py `
  --config coderisk/configs/experiments/YOUR-FROZEN-ABLATION.json `
  --output output/graduation-readiness-NEW --require-ready
```

报告`case_readiness.csv`逐条缺口，`dataset_validation.json`路径/hash/leakage，`report.json`冻结/资格/分母。退出2是正式未就绪，不是算法崩溃。先修真实记录或排除不可用项，不能填假授权/真人/功能PASSED。元数据通过仍不能自动认证独立性，责任人须审计证据。

统计q单独准备 `independent_reference_pair.template.json`、reference manifest 和 natural_reference_context：独立作者、来源、家族、hash、人工关系确认、功能/模板、授权都要有。在当前严格20个互不复用参考pair门槛下，每个题目/语言/背景至少需要**40份合格独立代码**才可能构成20对；这是必要数量下界而非充分性，也不消除pair依赖/cohort偏差。4—6作者的试点达不到，必须如实冷启动。不能全组合膨胀成20参考“独立观测”。

先做分组/固定 vs 规则阈值，q不足时记录BLOCKED和rule fallback。同题参考面板需预登记、参考与query身份/hash隔离，不能同时宣称reference/test problem-disjoint。不要为了测试题结果改变门槛/alpha/选样。

## 9. 你最小需要亲自完成

取得4—8题授权及匿名来源登记；落实两名实际独立复核者；提供源文件、题面/模板、父版本/独立依据与功能日志；看分前确认分组/冻结；让导师核查理论边界与学校要求。没有这些，工具和开题方法稿可交付，但真实效果不能“补算”出来。MySQL有效凭据、真实浏览器演示和学校个人信息另按 [人工清单](HUMAN_REQUIRED_CHECKLIST.md)办理。
