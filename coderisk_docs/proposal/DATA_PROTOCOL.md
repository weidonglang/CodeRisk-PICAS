# 实验数据收集、标注与划分规范 v1

状态：可执行工作规范；尚未收集新的真实学生作业。现有91对数据保持合成开发集身份。正式数据的规模、授权和双人复核需要实际落实。

## 1. 数据目标与收集顺序

本科主实验限同题 Java–Java 与 Python–Python。先覆盖简单输入输出、数组循环、排序模板、字符串、DFS/BFS、动态规划和模拟，再扩充不同长度、解法与改写类型。跨语言、解析失败和未知来源样本单列边界分析。

建议先取得4—8道题的小规模样本检验收集和标注流程，再争取12—20道题、80—150对代码。数量是计划目标，不是已完成统计或效果保证。更重视独立题目和来源家族数量，不能用大量复制改写把代码对数量凑大。

收集顺序：

1. 经教师或作者授权的独立解答，保留授权范围与来源记录。
2. 在明确许可范围内，对上述解答实施人工改名、格式/注释变化等受控改写，保存父版本和修改记录。
3. 有明确代码许可证或另行授权的公开解答，保存精确 URL、提交版本与许可证副本；公开可见不等于允许再分发。
4. AI 改写为可选附加组，记录模型、提示、时间、人工与功能核验，独立汇报。不得将其写成人工作业。

真实身份与授权书保存在访问受限位置；仓库仅使用匿名来源 ID 和授权记录索引。授权只允许分析而不允许公开代码时，保留本地数据，并在仓库提交必要统计、哈希与获取说明。收到第三方材料后按具体授权决定是否上传。

## 2. 来源登记表与目录

使用 [来源登记表](templates/source_registry.csv)，每份原始代码一行。必须填写：`source_record_id`、`problem_id`、`source_family_id`、`origin_type`、`source_url_or_private_ref`、`revision`、`license_or_authorization_ref`、`redistribution_allowed`、`collected_at`、`language`、`code_path`、`sha256`、`functional_check_ref`、`notes`。

- `source_record_id` 标识一份代码版本；`source_family_id` 标识同一个原始实现及所有派生版本。
- `origin_type` 如 `MANUAL`、`PUBLIC`、`HISTORICAL_AUTHORIZED`、`AI_ASSISTED`；须与现有 manifest 的来源字段保持一致。AI 来源在 manifest 用 `source_type=ai_assisted` 记录。
- 私有来源用内部索引，不填姓名、邮箱或学号。
- URL 应精确到文件/提交，许可证与授权必须能查验，`redistribution_allowed` 只填 `YES/NO/UNKNOWN`。
- 哈希按 UTF-8 文本读取后的内容计算，与现有数据加载器一致；如原始文件编码不同，另外保留原始文件哈希和转换记录。

真实数据建议建立独立 `experiment/datasets/graduation-v1/`，不要把既有开发样本重新命名成“新测试集”。沿用现有 `dataset.json`、`pairs/*.json`、`samples/` 格式和 `RESEARCH_V4_PAIRS_JSON` 来源格式。先使用 `add_research_v4_case.py --help` 核对录入参数。

## 3. 标签定义

| 工作标签 | 进入二元指标的含义 | 证据要求 | 不允许的做法 |
| --- | --- | --- | --- |
| `TRANSFORMED` | 正例：具有明确派生关系的改写 | 原始版本、变换记录、来源家族及功能检查 | 因得分高就标正例 |
| `SIMILAR` | 正例：已知原文复制或重复版本 | 文件历史/复制记录；用 `ORIGINAL_COPY` 区分类型 | 仅因算法相似就标为已知复制 |
| `INDEPENDENT` | 负例：有独立创作依据 | 独立来源过程、未查看对方实现的记录或可信来源说明 | 把仓库地址不同直接当作独立 |
| `NATURAL_SIMILAR` | 负例：独立创作且共享模板/题目约束 | 同上，另记共同模板和自然相似原因 | 根据检测器高分挑选此标签 |
| `UNCERTAIN` | 不进入主指标 | 缺少派生/独立证据、标注分歧未解决或功能不明 | 为凑数据强行二分 |

历史 `SUSPICIOUS` 被现有脚本映射为正例，但新增正式数据不宜使用“可疑”替代已知派生证据；不能明确关系时使用 `UNCERTAIN`。上述标签描述研究样本关系，不是学术违规处分结论。

`case_type` 与标签分开：如 `VARIABLE_RENAME`、`PARAMETER_RENAME`、`FUNCTION_RENAME`、`FORMAT_COMMENT_CHANGE`、`LOCAL_REORDER`、`SPLIT_MERGE`、`HUMAN_REWRITE`、`INDEPENDENT_SOLUTION`、`NATURAL_TEMPLATE`。复杂变换必须验证功能，不保证当前规范化能识别。

## 4. 标注流程

使用 [代码对标注表](templates/pair_annotations.csv)。

1. 收集人员登记题目、两份代码来源、共同模板和派生记录，暂不计算待评价工具的分数。
2. 两位复核者分别依据来源和代码记录标注；使用匿名复核者 ID，保留首次标签。
3. 核对功能证据：同题输入输出要求、测试集版本、通过/失败记录。只在独立受控环境测试自己或已授权样本，业务上传检测继续不执行代码。
4. 一致则记 `AGREED`；不一致时记录分歧和裁决依据，解决后更新最终标签，无法解决则 `UNCERTAIN` 且 `eligible_for_core_metrics=false`。
5. 标注冻结后方可用于调参与评估。正式 runner 要求 `annotation.label` 与最终标签一致，并检查两名不同复核者、依据、日期、功能证据和来源家族。

两名复核者尚未落实时可以先做单人试标，状态标记 `PENDING_SECOND_REVIEW`。脚本不会把单人试标自动提升为正式实验。

标注表中的最终记录同步到 manifest：

```json
{
  "source_family_ids": ["实际来源家族A", "实际来源家族B"],
  "annotation": {
    "status": "PENDING_SECOND_REVIEW",
    "label": "UNCERTAIN",
    "reviewer_a": "",
    "reviewer_b": "",
    "label_basis": "",
    "reviewed_at": "",
    "functional_evidence": ""
  },
  "eligible_for_core_metrics": false,
  "split_preregistered": false
}
```

上例是字段模板，不是实际样本。派生正例可只有一个来源家族；独立负例应登记两份原始实现各自的家族。

## 5. 验证集与测试集划分

开发集用于找缺陷，当前91对样本始终属于这个层次。新的验证集用于选阈值，新的测试集用于冻结后的评估。

划分单位为连通分组：共享题目 ID、来源 ID、任一来源家族或任一代码哈希的代码对必须在同一组；这种关系需传递合并。相同题目的不同措辞/翻译使用同一个题目 ID，同一实现的不同文件名和修改版使用同一来源家族。

`research_protocol.py` 按固定随机种子和分组哈希提出约30%验证组、70%测试组的方案。比例按组计，不保证代码对数量精确为3:7。它不读分数，也不改数据；输出状态是 `REVIEW_REQUIRED_NOT_PREREGISTERED`。

```powershell
# 在 E:\ms\coderisk 下执行；路径替换为实际的新数据 manifest。
& .\analysis-service-python\.venv\Scripts\python.exe .\experiment\research_protocol.py --manifest .\experiment\datasets\graduation-v1\dataset.json --output .\data\artifacts\graduation-split-proposal.json --seed 20261008
```

生成后检查两集均含正负例、题目类型和语言覆盖。若分组太少或覆盖不足，应补数据或记录修改划分的理由；在看测试得分前固定方案。不能不断换随机种子直到方法表现好。

保存 [划分登记表](templates/split_registry.csv)，确认数据来源与标签后记录冻结时间和版本，才可把实际条目的 `split_preregistered` 设为 `true`。新增 `source_family_ids` 会由数据校验器检查跨集泄漏。

## 6. 正式实验冻结与退回条件

冻结题目、来源、标签、分组、配置、核心源码及外部工具版本。新数据 manifest 添加 `evaluation_registration`，包含 `status=FROZEN`、`registered_at`、`reference`（预注册记录路径/提交）和配置文件原始字节的 `config_sha256`。先形成日期记录再评估；填写字段不能证明历史上没有看过测试结果。

来源不清、缺授权、功能未知、标签争议或分组泄漏时退回修订。正式 runner 默认拒绝合成数据、未预注册、未完成双人复核或配置哈希不符的输入。使用 `--allow-development` 可运行流程验证，但输出明确标记为开发用途。

查看测试结果后若修改方法，该数据即成为开发证据；下一轮确认性研究需新的独立保留数据。保留旧结果、失败案例与排除原因，不覆盖历史运行目录。
