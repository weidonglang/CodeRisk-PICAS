# Result review UI and publication verification · 2026-10-16

前端结果展示增强及用户授权的既有研究增量整理。**这是工程/展示验证，不是检测benchmark或真实关系标签。** 不更换生产公式、API、数据库结构，不提高V4 experimental生产权重。

## 改动和真实数据范围

全任务风险分布、当前页分数/阈值对比、数值可访问的详情刻度、规范化前后差值、阈值正负调整、证据筛选/定位、长代码滚动、源码排列/换行和映射搜索。风险等级、边际、总分全部来自原API，缺失值不伪造为0。

真实浏览器使用同日第一轮的隔离DataRoot，新增第5/6号UI_SELF自有测试题及静态提交；首次流程在选择器处退出，第6号完成所有步骤。未执行上传代码，没有真实学生、收费API或MySQL操作。截图为第6号实际分析结果，不是临时模拟结果。

## 已运行

| 验证 | 结果 |
| --- | --- |
| 全量Python | 591 passed，1既有Starlette/httpx warning，14.98s |
| Maven | 19通过，0失败/错误/跳过，H2；总9.665s |
| 前端单测 | 18通过，包含6项新增图表数据边界检查 |
| 开发脚本 | 26检查通过 |
| 类型检查/生产构建 | 1713模块，3.99s；旧PURE/chunk警告保留 |
| 真实自有服务端到端 | 41项通过，浏览器运行时错误0 |
| 真实详情/报告复验 | 5项通过：图表跳转、路由标题、任务报告下载、证据筛选及重置 |
| 临时拦截图表/交互 | 30项通过，不写库；含长源码、缺失、负调整、4种宽度 |
| 临时拦截旧状态 | 7项通过，不写库；含降级、离线和终态读取顺序 |
| CI离线synthetic入口 | 75行，JPlag显式SKIPPED，不是新基线评测 |

原运行目录 `output/result-review-20261016/`；五张最终桌面/手机截图和HTML下载在 `output/playwright/result-review-20261016/`。精选日志、JUnit与检查JSON在本目录，SHA-256索引只核归档字节。README中的截图复制到 `coderisk_docs/assets/` 的新文件，不覆盖旧截图。

## 命令

```powershell
# 从仓库根；替换成本机可用解释器/JDK，不依赖他人的临时环境目录。
python -m pytest -q -p no:cacheprovider --junitxml output/python.xml
mvn --batch-mode -f coderisk/backend-springboot/pom.xml test
npm --prefix coderisk/frontend-vue test
npm --prefix coderisk/frontend-vue run build
.\coderisk\scripts\test-dev-scripts.ps1
python coderisk/experiment/run_fair_evaluation.py --output output/fair-new --allow-development --skip-jplag
```

浏览器CLI脚本见 `coderisk/frontend-vue/tests/`；先执行工具 `--help`，仅使用自有隔离数据库。运行前创建截图目录，CLI成功退出还必须核对JSON中的checks和errors。数据写入/来源、失败与未运行项不能省略。

## 失败与局限

初次页面连接失败是服务未启动；首次真实流程因桌面/手机同文案测试选择不唯一退出，第二次限定桌面范围后通过。首次图表测试对Element Plus隐藏input直接check超时，改为点击可见label并核对状态后通过。详情复验点击被占位文字覆盖的内部input，且同会话另一轮导航使其detach；改操作可见wrapper并串行重跑5项通过。失败日志保留，不计作通过。

MySQL、真实LLM、真实授权关系标签、教师收益和正式统计效果仍NOT_RUN/受阻。75行synthetic只是已有CI流程回归；ConPlag不利比较和正式资格0继续保留。历史报告里的未推送/NOT_RUN按当时日期理解，本次发布不回填历史结果。

发布检查只验证本地文件/JSON/链接目标、常见凭据特征、归档哈希和待提交清单；不是完备安全审计或第三方授权认证。原始下载数据、数据库、密钥、jar/缓存、两份用户本机任务书不在发布范围。GitHub实际提交和CI状态以最后发布记录为准，不预写成功。

Git暂存检查保留测试工具的原生尾随空格/末尾空行，仅在`.gitattributes`对冻结归档log/xml设置`-whitespace`，不修改带hash的历史字节；源码及普通文档检查不放宽。

说明：[结果阅读指南](../../../../coderisk_docs/RESULT_PRESENTATION_GUIDE.md) · [启动手册](../../../../coderisk_docs/FRONTEND_AND_DEV_WORKFLOW.md) · [测试报告](../../../TEST_REPORT.md) · [MIT](../../../../LICENSE)。
