# CodeRisk 运行与演示手册

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

默认 `local` 使用持久化 H2、MySQL 兼容模式，Flyway 自动应用 V1–V4 迁移。MySQL 8 使用 `CODERISK_DB_URL`、`CODERISK_DB_USERNAME`、`CODERISK_DB_PASSWORD`，初始化与配置见 [数据库说明](database/README.md)。H2 验证不能代替 MySQL 实库验证。

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
