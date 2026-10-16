# 前端与本地启动流程 · 2026-10-16

本轮仅调整 Vue 展示和 Windows 开发脚本，不改变生产相似度、阈值、API 或数据库结构。研究能力与数据资格仍以原研究文档为准，不因界面更新升级为正式效果。

同日第二轮继续增强结果展示：全任务分布、当前页对比图、详情同刻度阈值图、正负阈值调整条、证据筛选/长源码定位、源码布局及映射搜索。最新前端18单测、真实流程41+详情5+图表30+模拟状态7项检查通过；下文12项/41+7是第一轮记录。[阅读图表与结果](RESULT_PRESENTATION_GUIDE.md)，[第二轮证据](../coderisk/experiment/evidence/result-review-20261016/README.md)。

## 界面变化

- 工作区：固定侧栏、面包屑、当前页标识、键盘跳转正文；窄屏底部保留文字导航，结果详情正确归属检测任务。
- 工作台：真实统计、最近任务、最近题目、服务配置和语言范围。局部请求失败不会抹掉其他已加载模块；未加载数字显示 `-`，不伪造为0。
- 题目管理：服务端分页，搜索明确限定本页；新建表单输入输出并排，模板登记折叠，字段长度与后端契约一致。
- 提交：文件选择区、已选文件/体积、上传成功反馈和清空文件输入；上传/初始化期间避免启动不完整任务。
- 任务：中文状态、运行中/已完成/需处理筛选、最近任务搜索、成功覆盖进度及失败数。
- 结果：补全中风险统计，本页文件名与风险筛选，保留后端排序、原分量及报告下载。
- 详情：综合分/阈值/边际/风险置于首屏；四个分量条不替代原指标。证据与源码、题目与阈值、标识符映射、背景复核、实验性指标分别展示。可选择证据定位原文高亮、复制源码；窄屏用逐条证据列表替代截断的大表格。
- 运行状态：读取真实后端版本、语言和模式。后端连接每30秒检查一次，也可手动重试；分析服务地址仅是配置值，不冒充探活，数据库类型未暴露就明确未知。
- 错误：超时、连接失败、用户输入错误分别显示；5xx不直接展示内部诊断信息。未提供分数显示 `-`，不把缺失值当0。

所有高亮和分量来自原 API；实验性IR/摘要保持生产权重0，不生成AI来源判断或自动纪律结论。

## 一键启动

从仓库根目录执行，需先安装分析服务依赖、前端依赖及JDK21+/Maven/Node。不会自动安装/升级依赖、修改全局环境或下载模型。

```powershell
Set-Location E:\ms
# 只检查运行环境和可用端口，不启动服务，也不验证数据库凭据。
.\coderisk\scripts\start-dev.ps1 -CheckOnly
# 正常启动：分析服务 → 后端 → 前端；逐个等待就绪。
.\coderisk\scripts\start-dev.ps1
# 仅停止本脚本托管且身份匹配的进程，保留数据与日志。
.\coderisk\scripts\stop-dev.ps1
```

若当前终端执行策略禁止脚本，可只为这个进程使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\coderisk\scripts\start-dev.ps1
```

不需要修改系统级执行策略。默认 `local` 是H2持久化开发库，**不是MySQL验证**。默认端口5173/8080/8001；占用时在附近寻找可用端口并保持代理/分析地址一致，实际URL以终端输出为准。`-StrictPorts`禁止自动换端口，但不会停止占用者。

### 指定环境与隔离数据

```powershell
.\coderisk\scripts\start-dev.ps1 `
  -Python 'E:\ms\.tmp\language-venv\Scripts\python.exe' `
  -JavaHome 'D:\DevEnvManager\envs\jdks\temurin-21' `
  -DataRoot 'E:\ms\output\my-dev-session'
```

Python优先显式 `-Python` / `CODERISK_PYTHON`，随后探测可用项目venv、本地恢复环境和系统Python，要求3.11+及已安装依赖。显式指定无效时不偷偷换解释器。

JDK优先显式 `-JavaHome` / `CODERISK_JAVA_HOME`，否则检查JAVA_HOME/PATH及可识别安装目录。本机JAVA_HOME原指向Temurin17，而21已安装；脚本可为**当前项目进程**选择21，不改系统/用户持久化环境。显式无效JDK会报错，不替换用户指定值。

`-DataRoot`显式指定时统一覆盖上传、产物和local H2路径，便于隔离演示；省略时沿用已有目录环境配置及 `coderisk/data`。路径允许空格，不允许分号（H2 URL分隔符）。启动不会删除或重置旧数据库；现有Flyway迁移仍按原应用运行。

MySQL须本人提供有效配置后显式 `-Profile mysql`，参考 [数据库手册](../coderisk/database/README.md)。预检通过、H2测试或看到配置地址均不等于MySQL实库验证。不要将密码写入脚本、Git或终端示例。

### 日志与停止

每次启动在 `.tmp/coderisk-dev/sessions/<UTC时间-随机ID>/` 保存三个服务的stdout/stderr和 `session.json`；`.tmp/coderisk-dev/current.json`指向当前会话，均为本地忽略文件。

已运行的同一托管会话不会重复启动，保留原配置；更改数据目录、运行环境或端口须先停止再启动，不会热切换。不同数据库profile会明确拒绝复用。部分会话存活时会提示先停止；失败时只清理本轮已登记进程。停止前同时检查PID、启动时刻和命令SHA-256，PID复用或指纹不符不会被杀。不同PowerShell对JSON日期的解析差异已纳入回归。不要在服务运行时删除或编辑会话记录。

```powershell
# 只停止一个已知旧托管会话；目录必须位于本项目的控制目录。
.\coderisk\scripts\stop-dev.ps1 -SessionDirectory 'E:\ms\.tmp\coderisk-dev\sessions\<实际ID>'
```

手工三终端脚本仍可用，并支持 `-CheckOnly` 与端口参数；它们不属于托管会话，`stop-dev`不会任意停止它们。此工具是单机开发辅助，不是生产进程管理器。请勿同时并发启动多个启动命令。

## 验证命令

```powershell
npm --prefix coderisk/frontend-vue test
npm --prefix coderisk/frontend-vue run build
.\coderisk\scripts\test-dev-scripts.ps1
.\coderisk\scripts\run-all-tests.ps1 -Python '<可用Python>' -JavaHome '<JDK21目录>'
```

浏览器回归脚本位于 `coderisk/frontend-vue/tests/ui-smoke.js` 与 `ui-states.js`，格式为Playwright CLI `run-code --filename`，从根目录执行，并先创建 `output/playwright/ui-refresh-20261016/`。前者会创建明确标注UI_SELF_AUTHORED的自有联调题目和提交，只应对测试数据库运行；后者仅临时拦截专用浏览器请求，结束后移除，不写数据库。两者都不执行上传代码，不是检测benchmark。

本机复用了Codex已安装的Playwright CLI与临时Chrome会话，未安装新npm依赖。不要用真实学生数据、个人浏览器资料或收费模型来通过UI测试。脚本或CLI版本变化先运行 `--help`。部分CLI错误仍返回进程码0，因此必须同时核对返回JSON和checks，不只看shell退出码。

## 本轮真实验证

运行记录在 `output/ui-refresh-20261016/`，图片在 `output/playwright/ui-refresh-20261016/`。Python591通过（1既有warning，67.33s）、Maven19通过（总13.672s，H2）、前端12项单测和26项脚本检查通过；最终生产构建1706模块/4.02s，旧PURE/chunk警告保留。汇总见 [TEST_REPORT](../coderisk/TEST_REPORT.md)。

最终真实浏览器自有流程41检查：题目验证/创建、两份源码上传、任务完成、报告下载、证据/映射/背景，以及七类页面在1440/768/390/320宽度下无整页横向溢出；7项模拟状态检查分页/离线/缺失/实验性/最终刷新顺序。隔离库重启前后3题/6提交/3任务及结果快照一致；之后最后一轮UI测试再新增1题/2提交/1任务。修复后重复启动返回原5173地址，不新增进程。

失败记录没有隐藏：首次构建realpath权限/Chrome沙箱启动失败，改用获许可的本机执行完成验证；测试选择器/起始视口/工具VM全局对象不兼容及过宽API模拟已修正。首次幂等测试因JSON日期转换误开第二组，已按PID/时间/指纹确认关闭；该组使用默认local配置，未创建题目、上传或任务，**不声称默认数据库文件逐字节未变化**。正常联调及重启验证使用独立DataRoot，没有删除或覆盖旧研究产物。

当前默认数据库不是此次研究的正式数据集，UI_SELF样例不得计入真实人工来源或正式指标。MySQL、真实模型与教师效益没有因本轮验证而完成。
