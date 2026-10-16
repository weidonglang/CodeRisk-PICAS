# CodeRisk 文档导航

同日最新统计视图：[直方图/散点/热力图/箱线图口径](STATISTICAL_VISUALIZATION.md)，含分母、分位数、缺失、小样本、导出和版权署名魏语石；不改变生产评分或正式数据资格。

最新界面增量（2026-10-16）：[结果图表与证据阅读](RESULT_PRESENTATION_GUIDE.md)、[一键启动与本地流程](FRONTEND_AND_DEV_WORKFLOW.md)、[本轮工程验证](../coderisk/experiment/evidence/result-review-20261016/README.md)。图表保持原API及生产公式，experimental权重0；研究结论、公开数据规模和真实授权资格不因UI更新而变化。

最新增量（2026-10-12）：[AI 时代价值审计](research/AI_ERA_VALUE_AUDIT.md)、[会话/来源协议](research/AI_CONVERGENCE_PROTOCOL.md)、[真实采集操作](research/LIVE_GENERATION_PLAYBOOK.md)、[PowerShell 复现](research/REPRODUCE_AI_CONVERGENCE.md)、[测试与失败记录](research/TEST_AND_EVIDENCE_SUMMARY.md)、[Go / Pivot / Stop 决策](research/PICAS_GO_NO_GO_DECISION.md)、[开题补充](research/PROPOSAL_AI_ERA_APPENDIX.md)。最新Python **591** / H2 后端 **19** / build 通过；mock 22 对、JPlag 共同 14 对，仅 development。当前正式结论 **INSUFFICIENT_EVIDENCE**，没有真实生成/人审/教师效益。本轮[证据包](../coderisk/experiment/evidence/ai-era-value-20261012/README.md)与下列历史记录分开。

本轮最新入口（2026-10-11）：[S0—S5开题研究包](research/OPENING_RESEARCH_PACKAGE.md)、[群轨道/α与商集](research/ORBIT_ALPHA_EQUIVALENCE.md)、[独立性质及判别力报告](research/INVARIANCE_DISCRIMINABILITY_REPORT.md)、[真实数据采集教程](research/REAL_DATA_ACTION_GUIDE.md)。本轮工作树Python523/H2后端19/build通过，正式数据/统计效果仍BLOCKED；以下早期轮次数字保留为历史，不累计成独立样本。

[项目首页](../README.md) · [运行手册](../coderisk/README.md) · [开题材料](proposal/README.md)

2026-10-12 [完整交付报告与导师说明](research/AI_ERA_FINAL_REPORT_20261012.md)按V0—V5列明DONE/PARTIAL/BLOCKED、真实测试及负结果，附精确改动与工作区保护证据。需要继续真实试点时先完成手册中的本人授权和双审步骤。

最近增量（2026-10-11）：[离线 LLM 对照](research/LLM_BASELINE.md)与[混合候选门禁](research/HYBRID_DETECTION.md)已实现；最近开发轮 Python 431 / H2 后端 19 项及前端构建通过，真实模型/混合效果未验证。当前公开/候选数据登记 **92,513 行**，统计与已运行实验分开说明于[项目首页](../README.md#数据规模概览)和[数据核对](../coderisk/experiment/evidence/readme-data-refresh-20261011/README.md)。此前[AI 分工检查](proposal/AI_REVIEW_HARDENING.md)的 188 项是历史记录。

按阅读目的选择入口。规范文件说明设计与边界，测试记录说明已验证内容，实验快照保存特定版本的实际结果；三者不能相互替代。

## 了解和运行

| 文档 | 内容 |
| --- | --- |
| [PROJECT_SPEC](PROJECT_SPEC.md) | 项目定位、目标与当前功能范围 |
| [ARCHITECTURE](ARCHITECTURE.md) | 前端、后端、分析与实验模块 |
| [运行手册](../coderisk/README.md) | 环境安装、服务启动、演示与排查 |
| [数据库说明](../coderisk/database/README.md) | H2/MySQL 配置及迁移 |
| [测试报告](../coderisk/TEST_REPORT.md) | 分阶段工程验证，保留历史版本 |
| [已知问题](../coderisk/KNOWN_ISSUES.md) | 支持范围、回退及未验证项 |

## 算法和开发

| 文档 | 内容 |
| --- | --- |
| [FORMULA_SPEC](FORMULA_SPEC.md) | 生产融合、阈值与风险展示公式 |
| [ALGORITHM_SPEC](ALGORITHM_SPEC.md) | 分析流程、表征和指标边界 |
| [CANONICALIZATION_SPEC](CANONICALIZATION_SPEC.md) | 标识符规范化设计 |
| [PROBLEM_AWARE_SCORING](PROBLEM_AWARE_SCORING.md) | 题目画像与阈值解释 |
| [API_SPEC](API_SPEC.md) · [DATABASE_SCHEMA](DATABASE_SCHEMA.md) | 接口与数据模型 |
| [FRONTEND_SPEC](FRONTEND_SPEC.md) · [UI_FLOW](UI_FLOW.md) | 界面能力与业务流程 |
| [前三项推进记录](proposal/NEXT_THREE_PROGRESS.md) | IR-Plag 新数据、融合负结果分解、异步任务与失败恢复 |
| [版本、模板与自然相似](proposal/VERSION_AND_NATURAL_SIMILARITY.md) | 已实现复核上下文与校准边界 |
| [IR_SPEC](IR_SPEC.md) | 跨语言实验表征，生产权重为零 |
| [贡献指南](../CONTRIBUTING.md) · [AGENTS](AGENTS.md) | 修改、验证与数据真实性约定 |

## 数据和评测

| 文档 | 内容 |
| --- | --- |
| [公开数据接收](proposal/PUBLIC_DATA_INTAKE.md) | 来源、许可、导入和核查 |
| [多语言进展](proposal/MULTILANGUAGE_PROGRESS.md) | C/HTML 功能、CodeNet/MDN 与解析审计 |
| [数据标注规范](proposal/DATA_PROTOCOL.md) | 来源登记、关系依据与划分规则 |
| [数据复核工作台](proposal/DATA_REVIEW_WORKBENCH.md) | 离线盲审、标签检查与来源分组 |
| [公平评测协议](proposal/FAIR_EVALUATION.md) | 验证选参、消融、基线及统计限制 |
| [ConPlag 探索结果](proposal/CONPLAG_PILOT_RESULTS.md) | 实际结果、失败、共同集合与解释边界 |
| [实验目录](../coderisk/experiment/README.md) | 导入、运行与各阶段工具 |
| [实验产物](../coderisk/experiment/evidence) | 审核后的运行记录、快照与图表 |

## 开题和论文

| 文档 | 内容 |
| --- | --- |
| [开题材料目录](proposal/README.md) | 选题、初稿、文献与证据核对 |
| [开题交流准备](proposal/OPENING_DISCUSSION.md) | 与导师讨论的事实、问题与路线 |
| [项目与毕设核查](GRADUATION_READINESS_REVIEW.md) | 当前证据、优先优化与完成验收条件 |
| [毕设后续计划](GRADUATION_NEXT_STEPS.md) | 相对周次任务与阶段交付 |
| [论文写作流程](THESIS_WRITING_WORKFLOW.md) | 模板、引用、证据和写作约定 |
| [论文提纲](PAPER_OUTLINE.md) | 章节组织参考 |
| [ROADMAP](ROADMAP.md) | 工程与研究推进路线 |

尚未取得学校模板，正式文稿需按学校及导师要求调整。开题中的研究目标不能直接写成已完成结论，合成开发数据不能充当真实作业评测。
