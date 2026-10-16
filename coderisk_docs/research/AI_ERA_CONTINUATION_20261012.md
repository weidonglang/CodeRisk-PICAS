# AI 时代价值验证任务：关机前续接记录

> 2026-10-12恢复后更新：用户已要求继续。本轮可自动部分已收口，最新全量591passed/1warning（61.37s）；恢复时1项夹具目录依赖失败保留并仅修测试。文档同步、193份精选产物归档及生产/历史/index/源码/输入哈希核验已完成，正式真实效果仍受阻。最新状态看 [交付报告](AI_ERA_FINAL_REPORT_20261012.md) 和 [证据核验](../../coderisk/experiment/evidence/ai-era-value-20261012/verification.json)。下面是关机前原始记录，不再代表当前暂停或尚未归档状态。

记录日期：2026-10-12。工作目录：`E:\ms`。状态：**用户要求暂停，已保存本地工作；主任务尚未最终验收，不应报告为全部完成。**

用户恢复时可说：“继续 AI 时代价值验证任务”。先阅读本记录并检查恢复后的工作区变化，再从剩余事项继续，不能从零重写项目。

## 1. 当前指令与边界

主任务来源：根目录 `CODEX_PICAS_下一阶段_AI时代价值验证与研究开发任务书.md`，按 V0—V5 实施，客观判断 PICAS 在 AI 辅助编程时代的增量价值，不预设必须成功。该任务书及 `coderisk_docs/AGENTS.md` 已阅读；恢复时核对任务书最终汇报格式即可。

必须保留生产架构、评分公式、数据库、历史实验和原有工作区修改；本轮新增逻辑离线隔离。不调用收费 API，不上传私有代码，不伪造来源标签、人审或功能验证，不自动提交、推送或修改 Git 历史。

本轮未修改生产源码、API、数据库或评分公式；生产权重仍为 raw 0.20 / AST 0.20 / canonical 0.45 / mapping 0.15，V4 experimental 权重仍为 0。此前规范化中的 Java 保守回退修改属于进入本轮之前的已有修改，不能认领为本轮成果，也不能撤销。

暂停时全部已知测试/实验命令均已结束，没有需要续轮轮询的 exec session。没有为本轮启动业务服务。关机后不要依赖 Python 环境变量、后台服务或终端会话仍在。

## 2. Git 与保护基线

- 分支：`main`。
- HEAD：`892e7ef4a0d2f016cc8b0713fc7b347bd9e1717f`，暂停前核对未改变。
- 原有 dirty/untracked 文件共 197 个，原有暂存修改很多；本轮未 stage、commit、push。
- 基线已记录 129 个生产保护文件和 1,492 个历史产物的哈希。
- 基线快照：`output/ai-era-value-20261012/baseline/snapshot.json`。
- 捕获脚本：`.tmp/ai-era-value-20261012/capture.mjs`。
- 原 index 备份：`.tmp/ai-era-value-20261012/index-before`。

**最终保护哈希比对、最终本地链接检查和证据归档还没完成。** 不得把保存了基线说成最终比对已经通过。恢复后如用户另有修改，应保留并记录，不 reset/revert/stage。

## 3. 已完成的代码与研究产物

新增离线包：`coderisk/experiment/ai_convergence/`。复用原 Research V4 数据读取、评分、实验指标、JPlag 执行和离线复核界面，没有另写一套生产算法。

主要文件：

- `protocol.py`：严格元数据模型、安全相对路径、SHA-256、脱敏错误、真实原始输出目录门禁；关系/AI 辅助类型/课程政策分别表达。
- `validate.py`：来源、session、题目及代码哈希、上游关系和 connected split 泄漏检查；不能从同题或模型不同自动推断独立关系。
- `ingest.py`：无网络本地采集快照，dry-run/validate-only、保留代码字节。
- `build_pairs.py`：原 loader 的适配器、同题代码对、未知关系保留、来源标签和功能有效性分离、正式指标门禁。
- `descriptive_stats.py`：分位数、缺失量、组件宏平均与配对 cluster bootstrap；少于 6 个组件默认不估计区间。
- `context.py`：只读题目/模板/有效 token/有限证据摘要，不修改评分，不判断 AI 来源或行为。
- `analyze.py`：六组冻结配置公平比较，逐样本分量、回退、分层、全 canonical 相等与 ngram 相等分离；数据/源码/配置/版本/依赖/随机种子追踪。
- `report.py`：CSV / JSON / Markdown / 描述性图，inspect-only 不覆盖历史。
- `jplag.py`：本地 JPlag 6.2.0 真运行、pair 对齐、哈希和参数门禁、共同有效 cohort；解析失败不补零。
- `prepare_review.py`：复用盲审 HTML、真实内容输出门禁、空白人工复核与教师效益记录；没有伪造真人。
- `export_public.py`：聚合字段白名单与小单元抑制；生成可分享摘要不等于授权发布。
- `examples/make_seed.py`：明确 synthetic/mock 的 13 份代码、12 个模拟生成 session、22 对；不冒充真实模型生成或 benchmark。
- `config.example.json`、`schema/*.schema.json`（6 个）、`budget.template.csv`、包内 `README.md`。

注意：原 `statistics.py` 因直接 CLI 与标准库同名冲突已改名为 `descriptive_stats.py`；恢复时不要重新引入同名模块。当前适配器只支持同语言 Java/Python；不能把原 V4 跨语言 IR 当成本轮公平比较的替代评分。

新增测试文件：

- `coderisk/analysis-service-python/tests/test_ai_convergence_protocol.py`
- `coderisk/analysis-service-python/tests/test_ai_convergence_analysis.py`
- `coderisk/analysis-service-python/tests/test_ai_convergence_privacy.py`

相对本轮修正环境后的 523 测试基线，新增 67 个测试；涵盖元数据/来源/路径/泄漏/正式指标门禁/共同 cohort/直接 CLI/只读评分/隐私输出等。

新增研究文档位于 `coderisk_docs/research/`：

- `AI_ERA_VALUE_AUDIT.md`
- `VALUE_CLAIM_EVIDENCE_MATRIX.csv`
- `AI_CONVERGENCE_PROTOCOL.md`
- `AI_CONTEXT_EXPLANATION_SPEC.md`
- `LIVE_GENERATION_PLAYBOOK.md`
- `PICAS_GO_NO_GO_DECISION.md`
- `PROPOSAL_AI_ERA_APPENDIX.md`
- `REPRODUCE_AI_CONVERGENCE.md`
- `TEST_AND_EVIDENCE_SUMMARY.md`

新证据目录 `coderisk/experiment/evidence/ai-era-value-20261012/` 已有 README 与 V0—V5/STATUS.md，但最终数据归档及其 README 预留引用的 `verification.json`、`artifact_hashes.json`、`failure_records.json` 尚不存在。不能把目录壳当成完成的证据包。

阶段实际状态：V0 完成；V1 离线完成；V2 部分完成（真实数据不足）；V3 离线完成；V4 工具完成但真人验证阻塞；V5 草案与审慎决策完成，最终同步/归档待完成。

## 4. 真实验证结果

所有日志位于 `output/ai-era-value-20261012/baseline/`。

| 验证 | 最终结果 | 文件 |
| --- | --- | --- |
| Python 全量 | **590 passed, 1 warning，46.24s，exit 0** | `python-release.log`、`python-release.xml` |
| Maven / H2 | **19 tests，0 failures/errors/skipped，BUILD SUCCESS**；测试 8.883s，总 16.356s | `maven.log`；原 Surefire 报告在 backend target 内 |
| 前端类型检查 + Vite | **构建成功，1699 modules，5.11s**；原有 PURE/chunk 警告 | `frontend.log` |

Python 的 1 个 warning 为 FastAPI/Starlette TestClient 的 httpx 弃用提示。后端覆盖中的 timeout/retry ERROR/WARN 为测试用例输出；不是 MySQL 实库验证。本轮未做浏览器主链路现场演示，不要将 build/test 说成浏览器 E2E。

保留的失败与修复过程：

- `python.log/xml`：522 通过、1 失败，中文 Git 文件名触发原诊断脚本 GBK 解码异常；启用 `PYTHONUTF8=1` 后 `python-r2.log/xml` 为 523 通过。
- `protocol-red.log/xml`：26 通过、10 失败，主要是 Windows CRLF 的 mock fixture 字节哈希问题；不能称为 10 个生产算法缺陷。
- `analysis-tests.log/xml`：50 通过、2 失败，模式字符串/降级原因描述修正。
- `analyze.log`、`cli-red.log/xml`：直接 CLI 的 stdlib 同名冲突；改名并新增独立 subprocess 回归。
- `privacy-red.log/xml`：1 个真实原始复核输出路径门禁反例；修复共享输出保护。
- `python-final.log/xml`（588）、`python-final-r2.log/xml`（589）为中间轮次，**最终使用 python-release 的 590**。
- 本地 jar manifest 初次 UTF-8 解码失败，改按 ASCII 键/Latin-1 检查确认 6.2.0；该工具异常没有独立 shell 日志，不伪造。
- formal 流程预期 exit 2 / FORMAL_BLOCKED，属于公开的数据门禁结果，不删除或隐藏。

## 5. 已运行实验及结论边界

根目录：`output/ai-era-value-20261012/`。

- **`analysis-release/` 是与最终代码对应的最新成功实验。** `analysis-final`、`analysis-aligned`、`analysis-r2` 是早期成功轮次，`analysis/` 是 CLI 失败目录，全部保留。
- `seed/`、`intake/`：13 个 synthetic artifacts、12 个 MOCK sessions、22 对、3 个题目；真实模型调用为 0。
- `jplag/`：本地真实执行 Java/Python，19 对准备/匹配成功；六组 PICAS 指标与 JPlag 全部可比的共同有效 cohort 为 14 对。解析失败等分母另列，缺失不计零。
- JPlag 冻结 minTokens=5、6.2.0，**没有 base-code 去除**；当前生产 PICAS 分数同样保留模板 token，不宣称完成去模板公平实验。
- canonical 可用 14/22；完整 C 相等 7/14、ngram 相等 7/14；仅 synthetic 描述，不能推断真实模型趋同率。
- 受控改名例 raw=0.030303，AST/canonical/mapping=1，Full=0.806061，rule threshold=0.820155；canonical 稳定不代表融合总分群不变，也不是有真实关系标签的漏报率结论。
- test 只有 2 个组件，区间 NOT_ESTIMABLE（门槛 6），不能用 pair 当独立单位虚增统计可信度。
- `formal/`：预期 FORMAL_BLOCKED；无正式 F1/FPR/准确率结论。
- `review/`：生成盲审与空白表格，真人参与/人审为 0；没有教师效益证据。
- `public-aggregates/`：来自早期 analysis-aligned；恢复后应基于 analysis-release 输出新目录，**不覆写旧产物**。
- 描述性图在 analysis-aligned 已可视检查非空/标签合理；最新图尚未单独检查。
- `properties/`：独立群作用工具 1738 次尝试、1728 次合法变体接受并通过、0 失败；unsupported 5、parser 2、uncertain 2、capture 1；6 个自编 Java 样例 javac 编译成功，未执行样例代码。该组与 AI seed 的 13 代码不同。
- `conplag-readonly/`：只读复核历史两组各 911 对（validation 284 / test 627），不重新拟合；v1 Full F1 0.554307 < NoCanon 0.598540；v2 Full 0.697368 < NoCanon 0.735202。保留融合未最优的事实，不粉饰。

当前决策：**INSUFFICIENT_EVIDENCE**；建议有条件 PIVOT 到方法边界/限制分析及可复核证据原型。停止 AI 来源认定或自动处分方向，暂停缺少有效数据的新指标堆积；不等于证明整个 PICAS 无用。

真实学生/模型新数据 0，真人审核 0，本轮 MySQL 实库/真实模型 API/真实功能执行/Dolos 为 NOT_RUN。仅 H2 fallback 测试已验证。

## 6. 恢复后按此顺序继续

1. 检查 Git 状态和用户新增修改；阅读本记录、任务书汇报要求，保留原有暂存内容，不重建架构。
2. 修正文档中的最新实验目录：`PICAS_GO_NO_GO_DECISION.md`、`REPRODUCE_AI_CONVERGENCE.md` 的 analysis-final 改为 analysis-release；`TEST_AND_EVIDENCE_SUMMARY.md` 填入最终 590/1 warning/46.24s、+67 测试。
3. 小范围同步根 README、文档导航、ROADMAP、VERSION_MATRIX、EXPERIMENT_PLAN、TEST_PLAN、PAPER_OUTLINE、TEST_REPORT、KNOWN_ISSUES 和开题材料链接。此轮尚未同步完成；保留现有截图、MIT、数据规模、历史结果和有价值内容。
4. 需要时基于 analysis-release 生成新 public aggregate/review 目录并核图；不覆写旧 experiment run。
5. 完成基线与现状比对：HEAD/index/staged 不变、129 生产文件不变、1492 历史产物不变；记录原 197 dirty 文件的增量，区分有意文档编辑与先前修改。禁止通过回滚“修好”比对。
6. 核本地 Markdown 链接；不要将未检验远程页面或 future artifacts 当作存在。
7. 向新证据目录归档经过筛选的最新 CSV/JSON/MD/PNG/manifests、JPlag 原生结果/日志、群作用/ConPlag 只读结果、formal 门禁、空白 review、真实测试日志/JUnit。不要复制 jar、大量缓存、私有真实源代码或凭据。
8. 生成真实 `failure_records.json`、`verification.json`、`artifact_hashes.json` 和改动摘要；hash index 排除自身（Windows 用 basename 判断），避免自引用和循环哈希。保持旧实验不可变。
9. 运行 `git diff --check`，若为本轮代码修补再跑受影响测试。没有新算法变更时不为凑记录重跑收费/外部操作。
10. 最终中文按任务书 **0—10** 结构汇报，含约 200—300 字导师陈述；区分实现/条件证明/观察/NOT_RUN，客观报告不足。不要自动 commit/push。

## 7. 本机复现环境（重启后重新设置）

```powershell
Set-Location 'E:\ms'
$Python = 'E:\ms\.tmp\language-venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = 'E:\ms\.tmp\opening-tree-sitter-0252-20261011'
$env:TEMP = 'E:\ms\.tmp\ai-era-temp-20261012'
$env:TMP = $env:TEMP
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'matplotlib'
$env:JAVA_HOME = 'D:\DevEnvManager\envs\jdks\temurin-21'
$env:PATH = "D:\node;$env:JAVA_HOME\bin;D:\maven\apache-maven-3.9.10\bin;$env:PATH"
& $Python -m pytest -q -p no:cacheprovider
& 'D:\maven\apache-maven-3.9.10\bin\mvn.cmd' -f coderisk/backend-springboot/pom.xml test
& 'D:\node\npm.cmd' --prefix coderisk/frontend-vue run build
```

Python 3.12.14，隔离 Tree-sitter 0.25.2；Java 21.0.11 / Maven 3.9.10。若路径/依赖被用户修改先检查，不默认重装或覆盖环境。

完整离线命令已在 `coderisk_docs/research/REPRODUCE_AI_CONVERGENCE.md`。先 `--help`；每次选全新 run ID。`--formal` 对当前 seed 预期非零退出 2，不能包装成功性能评估。真实数据许可、模型调用授权、人审、导师确认操作见 `LIVE_GENERATION_PLAYBOOK.md`，均不可替用户代做。

## 8. 已核对的参考文献（无需为恢复重新爬取）

- 用户参考：[Correctness, Convergence, and AI-Generated Code Detection](https://arxiv.org/abs/2610.00863)，v1 2026-10-01；已读摘要/方法/讨论/限制。支持讨论题目层面的结构趋同与预检，不能当作个体 AI 来源或 PICAS 有效性的证明。
- [Argus](https://arxiv.org/html/2609.36073v1)，v1 2026-09-28；按预印本引用，页面会议模板占位不冒充正式会议证据。
- [MultiAIGCD](https://link.springer.com/article/10.1007/s00521-026-12336-0)，2026-08-22；出版社摘要/元数据/许可已核，论文许可不自动等于数据许可。
- [JPlag 官方仓库](https://github.com/jplag/JPlag)、[Dolos 官方运行说明](https://dolos.ugent.be/docs/running.html)。本轮只做 JPlag 真运行，Dolos 未运行。

没有下载论文全文或新外部学生代码，没有网络抓包级的零网络证明；准确表述为工具无模型网络调用、本轮真实模型调用 0。

## 9. 关机保存说明

本记录及代码、日志、产物均在本机文件系统；不是仅保留在聊天或运行中的终端。没有 Git 提交/推送，不保证尚未发生的最终验收。此刻停工，等待用户重启后继续。
