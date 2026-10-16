# V3：只读上下文与双工作流

当前仅离线 JSON/Markdown。没有Vue/API/DB接入，没有“AI概率”或学生行为判定；需V4真实收益证据才考虑集成。

ContextEvidence复用生产分量、risk、threshold、原文位置、模板覆盖和effective token数。canonical/AST不可用保留null和具体原因，不用fallback raw假装结构。已有token evidence只给有限ngram位置，**不是完整连续匹配长度分布**；match_length_distribution明确UNAVAILABLE，不能据它生成长匹配统计。

参考池分三种：UNAVAILABLE显示“没有可用AI参考证据”；DEVELOPMENT_ONLY显示“仅管线验证”；真实导入ELIGIBLE_DESCRIPTIVE只说“本参考集合观察到”。参考样本数、model snapshot数、会话数和经声明审核的独立参考数分别列，不把全部生成样本叫独立参考。provenance NONE/PARTIAL/VERIFIED_RECORDS只指声明证据链，不认证事实真伪。

## 出题前 Assignment Preflight

使用已获许可的未发布题面/模板与本地参考池；报告样本、规范表示数量、模板占比、局限，提出考虑阶段提交、自编测试或设计解释的选项。不能预测真实学生抄袭率、判断掌握程度或给真实课程质量打分。未发布内容未经许可不得发送第三方；工具无网络。

## 交卷后 Submission Review

列原始/规范化/AST/mapping、风险边际、模板/非模板长度、匹配位置、降级和来源不足，附复核问题。高分不是行为证据；低分/无匹配不是独立性证明。共同模式只是可能解释，**不改变**任何分数、阈值或risk。过程证据的事实核查、政策判断由有权限的人处理。

## 反误导验收

同题同代码的两世界请求，生产结果必须相同，文案不因假设历史写相反行为断言。覆盖空池、合成池、解析失败、Java header降级、完整模板覆盖、短代码和缺来源。摘要不输出代码token，只保存允许范围的hash/行位置；敏感代码仅在ignored本地数据/真人工作台，公开导出用字段白名单和小cell抑制，不等于自动出版授权。

本轮示例见新证据目录的 `analysis/context_evidence.json`、`assignment_preflight.md`、`submission_review.md`。这些是信息展示，不是已证明更有效的教师工具。
