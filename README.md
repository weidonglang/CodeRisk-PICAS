# CodeRisk / PICAS

面向编程作业的题目感知型代码相似风险检测系统。

已取得两份公开真实研究数据：AD2022的1,526份课程解答、ConPlag的911对Java标注样本。来源、许可、导入脚本与数据检查见[获取记录](coderisk_docs/proposal/PUBLIC_DATA_INTAKE.md)；当前处于独立数据接收阶段，尚未据此生成正式评测结论。

新增 C 与 HTML 实验检测，并接收 CodeNet 320 份源码（Java 107、Python 102、上游 C 111）及 MDN 46 份 HTML。C 目录存在语言混杂，72 份通过当前 C 语法解析；本批均无可靠代码对标签。功能、完整性核查和解析失败记录见[多语言进展](coderisk_docs/proposal/MULTILANGUAGE_PROGRESS.md)。

结合题目画像、动态阈值、标识符规范化和多维代码相似度，输出风险等级、代码片段证据与人工复核建议。系统不直接判定抄袭。

## 项目结构

| 目录 | 内容 |
| --- | --- |
| `coderisk/frontend-vue` | Vue 3、TypeScript、Element Plus 前端 |
| `coderisk/backend-springboot` | Java 21、Spring Boot 业务服务与 JDBC 持久化 |
| `coderisk/analysis-service-python` | FastAPI 分析服务与算法测试 |
| `coderisk/experiment` | 数据集、校验、对比、消融与失败案例分析 |
| `coderisk_docs` | 项目规范、架构、公式、接口与论文材料 |

## 本地启动

需要 Python 3.11+、Java 21、Maven 3.9+、Node.js 22 和 npm。以下命令在仓库根目录运行（PowerShell）：

```powershell
python -m venv coderisk/analysis-service-python/.venv
& ./coderisk/analysis-service-python/.venv/Scripts/python.exe -m pip install -e './coderisk/analysis-service-python[dev]'
npm --prefix coderisk/frontend-vue ci
```

如 Java 21 未在 PATH 中，请将 `JAVA_HOME` 设置为本机 JDK 21 目录。在三个终端分别运行：

```powershell
./coderisk/scripts/start-analysis-dev.ps1
./coderisk/scripts/start-backend-dev.ps1
./coderisk/scripts/start-frontend-dev.ps1
```

前端：http://127.0.0.1:5173；后端：http://127.0.0.1:8080；分析服务：http://127.0.0.1:8001。

默认使用持久化 H2 本地数据库，无需先安装 MySQL。MySQL 配置、完整演示步骤与实验命令见 [项目说明](coderisk/README.md) 和 [数据库说明](coderisk/database/README.md)。`.env.example` 仅作为配置参考，启动脚本不会自动加载 `.env`。

## 验证

```powershell
./coderisk/scripts/run-all-tests.ps1
```

GitHub Actions 分别运行 Python 测试、Maven 测试与前端类型检查/构建，并验证合成开发数据上的公平评测及图表生成（CI跳过外部JPlag）。

## 当前范围

- 支持 Java/Python 同语言分析、规则题目画像、动态阈值、作用域标识符规范化、证据展示和 HTML 报告。
- C 增加 Tree-sitter 结构解析与局部作用域规范化；HTML 增加标签/属性/文本比较、待校准固定阈值。二者实验性、仅同语言，不编译代码或执行网页。
- Java AST 是简化结构序列解析；跨语言 IR 与控制/数据摘要为实验功能，生产评分权重为零。
- Research V4 的 91 对样本是合成种子数据，用于验证工具链，不能作为真实作业上的效果结论。
- 本地上传、数据库、日志、构建产物和常规生成实验结果不纳入版本控制；审核后的开发实验快照保存在 `experiment/evidence/` 供复核。克隆后实验页面需先运行实验脚本生成结果；JPlag 比较需单独安装并运行基线。
- 历史验证记录见 [测试报告](coderisk/TEST_REPORT.md)，限制见 [已知问题](coderisk/KNOWN_ISSUES.md)。

开发前阅读 [项目约定](coderisk_docs/AGENTS.md)；生产公式以 [FORMULA_SPEC.md](coderisk_docs/FORMULA_SPEC.md) 为准。

## 本科毕设推进

当前按开题阶段组织后续工作，见 [毕设后续计划](coderisk_docs/GRADUATION_NEXT_STEPS.md) 和 [论文材料写作约定](coderisk_docs/THESIS_WRITING_WORKFLOW.md)。阶段安排使用相对周次，正式报告按学校模板和导师意见调整。

首批 [开题准备材料](coderisk_docs/proposal/README.md) 包含选题说明、文献矩阵、开题内容初稿与证据核对表。

新增 [开题交流准备包](coderisk_docs/proposal/OPENING_DISCUSSION.md)、[数据收集与标注规范](coderisk_docs/proposal/DATA_PROTOCOL.md)、[公平评测协议](coderisk_docs/proposal/FAIR_EVALUATION.md) 和 [本轮验证结果](coderisk_docs/proposal/RESULTS_REVIEW.md)。
