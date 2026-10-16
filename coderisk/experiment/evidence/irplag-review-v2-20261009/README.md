# IR-Plag 复核材料 v2

2026-10-09。仍是既有 467 份来源中同一 52 对复核候选，未新增样本、未评分、未完成实际真人或 AI 关系标注。所有本地标签 UNCERTAIN，正式资格为 false。

先用固定 ZIP/README/LICENSE 哈希重建来源登记和争议处置，再全局稳定打乱队列、按 pair_id 哈希交换 A/B。裁决文件记录原始参考方向和发布者标签，独立复核期间不要查看。代码注释/名称仍可能透露上游类别，只保证分数盲审。

- `blind_batch.jsonl`：52 对 ID/哈希与待复核状态。
- `publisher_labels_for_adjudicator.jsonl`：原公开标签、争议及 A/B 对应关系；不能当作本地真人标注。
- `review_preparation.json`：新清单 SHA-256、52 对数量、排序规则和本地工作台路径。

新工作台及含源码清单位于忽略目录 `coderisk/data/public-datasets/irplag-20261009/review-v2/`。导出含执行者 HUMAN/AI 声明；软件不会自动核实身份。A/B 互换会改变部分 review_id，与旧导出不混合；输出已有目录会被拒绝，保证历史包不被改写。

真实两位复核者、独立性确认、来源/功能证据、无泄漏划分、冻结研究方案均仍需完成。见 [复核工具说明](../../../../coderisk_docs/proposal/AI_REVIEW_HARDENING.md)。
