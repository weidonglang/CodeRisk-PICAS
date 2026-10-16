# CodeRisk 运行与演示手册

> 2026-10-16：新版工作区、证据标签页、窄屏证据列表及真实运行状态已实现；增加一键启动/停止、运行环境探测、端口避让和就绪检查。首选下方“一键启动”，旧三终端方式仍保留。当前界面/启动验证与已知限制见 [前端与启动流程](../coderisk_docs/FRONTEND_AND_DEV_WORKFLOW.md)，不改变研究算法或数据资格。

> 2026-10-11 S0—S5研究增量：新增独立绑定gold/群轨道及α边界、明确Java header遮蔽降级、双维预实验/正式数据前检和真人采集/答辩材料。当前工作树Python523/H2后端19/build通过；生产公式/架构不改，MySQL与本轮浏览器未验。详细PowerShell流程、真实数据操作及结果导航见 [开题研究包](../coderisk_docs/research/OPENING_RESEARCH_PACKAGE.md)。

> 2026-10-11 数据规模：当前公开/候选登记 **92,513 行**，其中 Java/Python 大规模已选 **60,000 对**、跨语言待复核候选 **30,893 对**；正式核心指标资格仍为 0。1,225 对是历史 synthetic 联调，不是全数据池。来源、统计与实际运行量分开列于[首页](../README.md#数据规模概览)及[逐行核对](experiment/evidence/readme-data-refresh-20261011/README.md)。

> 2026-10-10：[Python 与多语言公开接收](../coderisk_docs/proposal/NONJAVA_PUBLIC_INTAKE.md)提供固定下载、离线校验与数据表示说明。新增数据是外部开发/隔离池，不直接加入 Research V4 校准或正式指标；C++/JavaScript/C#/PHP 采集不等于服务支持。

> 2026-10-10：[数据入口与融合开发诊断](../coderisk_docs/proposal/INTAKE_AND_FUSION_DIAGNOSTICS.md)说明资格校验、JPlag 哈希对齐和 16 对自有开发探针；Python 224 项回归通过。正式评测入口与 seed runner 的区别见该文档。

> 2026-10-09 增量：[前三项推进记录](../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md)说明新数据、融合诊断与单实例异步任务恢复；后端 Flyway 已至 V5，H2 已验证，MySQL 实库仍待验证。

[项目首页](../README.md) · [文档导航](../coderisk_docs/README.md) · [数据库配置](database/README.md) · [测试记录](TEST_REPORT.md)

本手册集中说明工程运行。项目定位、语言边界和研究状态以首页及对应规格为准，历史实验记录不代表新版算法已经取得相同效果。

## 环境与依赖

需要 Python 3.11+、JDK 21、Maven 3.9+、Node.js 22 与 npm。以下命令均从**仓库根目录**执行，不是在 `coderisk/` 子目录中执行。

```powershell
python -m venv coderisk/analysis-service-python/.venv
& ./coderisk/analysis-service-python/.venv/Scripts/python.exe -m pip install -e './coderisk/analysis-service-python[dev]'
npm --prefix coderisk/frontend-vue ci
```

如需指定 JDK，可在后端终端设置：

```powershell
$env:JAVA_HOME = 'C:\path\to\jdk-21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

把示例路径替换成已安装的 JDK 21 目录，确保 `mvn` 能在 PATH 中找到。分析脚本优先使用 `CODERISK_PYTHON`，其次为已有 `.venv-coderisk`、`.venv`，最后为系统 `python`。

## 启动服务

### 一键启动（推荐）

```powershell
# 根目录；首次先按上方安装依赖。
.\coderisk\scripts\start-dev.ps1 -CheckOnly
.\coderisk\scripts\start-dev.ps1
.\coderisk\scripts\stop-dev.ps1
```

默认H2 local，逐个等待分析/后端/前端就绪；端口占用自动避让，访问实际输出URL。日志和PID/启动时间/命令指纹留在 `.tmp/coderisk-dev/sessions/`；停止保留数据库及日志，不杀未知进程。`-Python` / `-JavaHome`可固定运行环境，`-DataRoot`可显式隔离数据，`-Profile mysql`需要有效凭据且不是自动验证。`-CheckOnly`不启动服务。受执行策略限制时，仅使用进程级 `powershell -NoProfile -ExecutionPolicy Bypass -File .\coderisk\scripts\start-dev.ps1`，不修改系统策略。

### 手工三终端

分别打开三个 PowerShell 终端，每个终端均进入仓库根目录：

```powershell
# 终端 1
./coderisk/scripts/start-analysis-dev.ps1
```

```powershell
# 终端 2
./coderisk/scripts/start-backend-dev.ps1
```

```powershell
# 终端 3
./coderisk/scripts/start-frontend-dev.ps1
```

| 服务 | 默认地址 | 用途 |
| --- | --- | --- |
| Vue 前端 | <http://127.0.0.1:5173> | 题目、提交、任务、证据及实验看板 |
| Spring Boot | <http://127.0.0.1:8080> | 业务 API、结果持久化及报告 |
| FastAPI | <http://127.0.0.1:8001> | 内部分析服务 |

当前开发版无需登录。脚本采用共享上传与产物目录；[`.env.example`](.env.example) 是配置参考，不会自动加载。

### 配置覆盖

环境变量需在对应服务的终端设置。前后端地址和共享目录必须一致：

| 变量 | 用途 |
| --- | --- |
| `CODERISK_PYTHON` | 分析与测试脚本使用的 Python 可执行文件 |
| `CODERISK_UPLOAD_DIR` | 后端与分析服务共享的源码目录 |
| `CODERISK_ARTIFACT_DIR` | 产物目录 |
| `CODERISK_BACKEND_PORT` | 后端端口 |
| `CODERISK_ANALYSIS_BASE_URL` | 后端连接分析服务的地址 |
| `VITE_API_BASE_URL` | Vite 开发代理转发到的后端地址，重启开发服务后生效 |
| `SPRING_PROFILES_ACTIVE` | `local` 或 `mysql` |
| `CODERISK_LOCAL_DB_URL` | 本地 H2 数据库 URL |

默认 `local` 使用持久化 H2、MySQL 兼容模式，Flyway 自动应用现有 V1–V5 迁移。MySQL 8 使用 `CODERISK_DB_URL`、`CODERISK_DB_USERNAME`、`CODERISK_DB_PASSWORD`，初始化与配置见 [数据库说明](database/README.md)。H2 验证不能代替 MySQL 实库验证。

## 演示流程

1. 打开前端，在“题目”中创建题目，填写描述与输入输出约束。
2. 如有教师公开框架，登记模板语言、源码与来源；学生空位标记见 [模板规则](../coderisk_docs/proposal/VERSION_AND_NATURAL_SIMILARITY.md)。
3. 上传至少两份同语言源码，可选声明版本。初次演示推荐 Java 或 Python。
4. 创建并启动 `PICAS_STANDARD` 任务，查看完成状态与结果列表。
5. 打开代码对详情，核对分数、阈值、证据位置和解析限制。短代码或模板主导场景会另附复核提示。
6. 导出 HTML 报告。合成演示样本不能作为真实检测效果证据。

C/HTML 属于实验检测；HTML 不套用算法题画像。跨语言模式是单独实验功能，不属于生产标准评分。

## 测试与实验

```powershell
# 工程检查
./coderisk/scripts/run-all-tests.ps1

# 合成版本/模板回归：输出目录必须不存在
& ./coderisk/analysis-service-python/.venv/Scripts/python.exe coderisk/experiment/run_context_checks.py --output .tmp/context-demo
```

评测与绘图需额外安装实验依赖：

```powershell
& ./coderisk/analysis-service-python/.venv/Scripts/python.exe -m pip install -r coderisk/experiment/requirements.txt
& ./coderisk/analysis-service-python/.venv/Scripts/python.exe coderisk/experiment/run_fair_evaluation.py --output .tmp/fair-demo --allow-development --skip-jplag
```

以上评测使用合成开发数据并跳过 JPlag，用于检查工具链。正式数据、验证集选参、基线共同集合与排除规则见 [公平评测协议](../coderisk_docs/proposal/FAIR_EVALUATION.md)。旧 ConPlag 结果须按其冻结版本重现，不能跳过源码指纹检查。

实验看板读取本地产物；公平评测的自定义 `.tmp` 输出不会自动成为看板的最新运行。生成看板所需的历史 V3/V4 产物，请按 [研究运行指南](experiment/RUN_RESEARCH_V4.md) 操作，留意该指南使用的工作目录。

## 常见问题

| 现象 | 检查方式 |
| --- | --- |
| 分析服务未找到 Python 依赖 | 确认安装在脚本实际选用的虚拟环境中，可用 `CODERISK_PYTHON` 指定解释器 |
| 后端 Java 版本不符 | 在后端终端设置 `JAVA_HOME`，确认 JDK 21 与 Maven 可用 |
| 前端连接失败 | 检查后端是否启动、端口及 `VITE_API_BASE_URL`，更改后重启前端 |
| 分析服务找不到提交源码 | 检查两个服务是否使用同一个 `CODERISK_UPLOAD_DIR` |
| 端口被占用 | 先确认已有服务归属，再选择其它端口并同步相关服务地址 |
| 实验页面没有结果 | 克隆不包含本地运行产物，先按实验指南生成对应数据 |
| MySQL 连接被拒绝 | 核对账户、数据库与连接配置；初次演示可用默认 H2 |

更多边界和历史限制见 [KNOWN_ISSUES](KNOWN_ISSUES.md)。开发前阅读 [项目约定](../coderisk_docs/AGENTS.md)，评分实现遵循 [生产公式](../coderisk_docs/FORMULA_SPEC.md)。
