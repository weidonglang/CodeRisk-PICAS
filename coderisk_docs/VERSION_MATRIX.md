# VERSION_MATRIX.md

> 2026-10-12 AI 时代 Stage V（任务书 V0—V5）是离线研究阶段，不是生产版本升级。会话导入/校验、六方法分布及只读预检/复核报告可运行；13 artifacts / 12 mock sessions / 22 pairs 均 DEVELOPMENT_ONLY，native JPlag 共同支持 14。真实模型、真实标签、教师效益尚 NOT_RUN，正式效果 INSUFFICIENT_EVIDENCE。生产公式/API/数据库冻结，V4 权重仍 0，双工作流未默认接入 Vue。最新 Python591/H2后端19/build通过；MySQL/浏览器未新验证。见 [协议](research/AI_CONVERGENCE_PROTOCOL.md)、[测试](research/TEST_AND_EVIDENCE_SUMMARY.md)。

> 2026-10-11 开题S0—S5收口：有限Java/Python改名条件理论、独立性质gold和研究工具已加强；正式数据与统计收益仍BLOCKED，绝非版本升级为稳定语义检测。V4 IR/轻量摘要生产权重仍0；表达式交换/语句重排/完整α判定/完整CFG-DFG/AI来源检测不支持，LLM/Hybrid仅离线实验门禁。当前工作树回归Python523/H2后端19/build通过，MySQL实库和本轮浏览器E2E未验。见 [开题研究包](research/OPENING_RESEARCH_PACKAGE.md)。

> 本文件定义 CodeRisk / PICAS 各版本承诺范围。开发、前端宣传、论文实验、软著说明和答辩演示不得把探索项提前包装为正式能力。

---

## 1. 版本矩阵

| 版本 | 定位 | 必须交付 | 不承诺内容 |
|---|---|---|---|
| V0 | 业务闭环 + mock analysis | 题目创建、代码上传、任务创建、mock 结果、结果列表、代码对比 | 真实相似度、动态阈值、跨语言 IR |
| V1 | 真实 token + 基础 AST + 基础证据 | Java/Python 代码清洗、token 相似度、基础 AST、基础证据、early golden cases | 标识符归一化、题目评分、动态阈值 |
| V1.5 | 标识符归一化 + canonical token + identifier mapping | 变量名/参数名/函数名归一化、canonical token、identifier mapping 证据 | 动态阈值、多维融合、跨语言 IR |
| V2 | 题目评分 + 动态阈值 + 多维融合 + 报告导出 | 题目画像、自然相似风险、动态阈值、风险边际、报告导出 | 完整跨语言语义等价、CFG/DFG 高级图分析 |
| V3 | 实验、基线、消融、论文图表 | 最低实验矩阵、基线对比、消融实验、失败案例分析 | 工业级大规模平台能力 |
| V4 | 跨语言 IR、CFG/DFG、AI 改写增强 | 探索性实验、有限范围跨语言验证 | 不作为毕业设计主交付，不作为稳定产品能力 |

---

## 2. 毕业设计主交付范围

毕业设计主交付只承诺：

```text
V0 - V2
```

V3 用于论文实验和答辩增强，最低实验矩阵必须完成。V4 全部标为 exploratory / experimental。

---

## 3. 语言支持范围

| 语言 | 支持级别 | 版本定位 |
|---|---|---|
| Java | STABLE | V1+ |
| Python | STABLE | V1+ |
| C | EXPERIMENTAL | V4 探索项 |

前端和 README 不得在 V1/V2 阶段宣传 C 语言为正式稳定能力。

---

## 4. 跨语言与 AI 改写说明

```text
PICAS_CROSSLANG：实验性，不承诺完整跨语言语义等价。
PICAS_EXPERIMENTAL：用于批处理、消融和论文实验。
AI_REWRITE：实验 case_type，不代表系统能稳定识别所有 AI 改写。
CFG/DFG：V4 探索项，不进入毕业设计最低交付。
```

## 5. V4 Ready Gate

进入 V4 探索前必须保持 V0-V2 live E2E、H2/MySQL 配置边界、V3 problem-level validation/test 隔离、E1-E5 结果与失败案例、报告安全措辞、三套测试和文档一致性。外部基线 adapter 不等于真实基线已运行；MySQL profile 配置完成不等于实库凭据验证完成。

## 6. V4 Phase 1-3 实现边界

| 阶段 | 已实现 | 状态 | 不包含 |
|---|---|---|---|
| Phase 1 | 有限 Java/Python normalized IR、零权重 IR metric/evidence、3-case 实验、JPlag 6.2.0 真实 smoke run | EXPERIMENTAL | 完整语义 IR、跨语言语义等价 |
| Phase 2 | lightweight control-flow summary、lightweight data-flow summary、7-case 多指标/失败实验 | EXPERIMENTAL | CFG/DFG 图、PDG、符号执行 |
| Phase 3 | 91-pair synthetic seed manifest、problem/source/code-hash 隔离校验、录入辅助、validation-only 校准、统一 E1-E5/V4 runner、72-pair aligned JPlag、论文表格与失败分析 | SEED TOOLCHAIN READY | 可追溯真实数据、真实数据外部基线、统计显著性 |

Phase 1-3 的跨语言指标只在 PICAS_CROSSLANG 启用。PICAS_STANDARD、FORMULA_SPEC_V1 和 V0-V3 主交付权重不变。Research V4 当前 91 个 pair 全部为 synthetic seed，其中 4 个 AI_REWRITE 是明确排除的 placeholder。case_type 覆盖只验证工具链，不能替代 manual、verified ai_assisted 或 external 数据，也不能表述为正式 benchmark。
