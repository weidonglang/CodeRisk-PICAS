# CodeRisk 文档导航

[项目首页](../README.md) · [运行手册](../coderisk/README.md) · [开题材料](proposal/README.md)

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
