# S0 开题研究基线与主张审计

日期：2026-10-11。依据实际工作树，不把任务书的历史数字直接当成当前事实。

## 1. 状态及保护范围

实际任务书是根目录 `CODEX_PICAS_.md`；请求中的 `CODEX_PICAS_开题阶段完整研究任务书.md` 不存在。已阅读前者全部内容，不改名、不覆盖。分支 `main`，开始时 HEAD 为 `892e7ef4a0d2f016cc8b0713fc7b347bd9e1717f`。开始前有 **88 个已修改/未跟踪文件**，包含暂存的后端、前端、协议修改和未提交的数据工具。它们不是本轮新增成果。

本轮不提交、推送、发布、改写历史或改动暂存区。基线在 `output/opening-research-20261011/s0/baseline.json`：实际状态、索引 SHA、88 文件 SHA、选定源码 SHA、**252 个历史产物文件 SHA**。索引备份为 `.tmp/opening-research-20261011/index-before`。这些是本地证据，不发布学生代码。

保护的历史包括 identifier-invariance、ConPlag registration/pilot、similarity-ablation、natural-calibration、LLM、hybrid 归档。新实验全部使用新目录，不将重新运行的结果写回历史。

生产公式基线 SHA-256：`562fdb7d68757b811147f9e8d6587e52f8aad01647d002b858329e9ddedf7c20`。默认 Java/Python 可用四项权重继续为 raw 0.20、AST 0.20、canonical 0.45、mapping 0.15；V4 IR/摘要生产权重仍为 0。API、数据库、题目画像、风险等级公式本轮不修改。唯一生产源码变化是先红后绿的 Java 规范化保守降级，见第 4 节。

## 2. 实际环境与基线命令

本机可用 Python：`.tmp/language-venv/Scripts/python.exe`，3.12.14；旧服务 `.venv` 不可用。Java 为 Temurin 21.0.11，Maven 3.9.10；前端使用本机 `D:/node/npm.cmd`。快照工具使用的 bundled Node 版本不是 npm 所用 Node 的自动认证，最终环境证据另行记录。

从根目录执行：

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
New-Item -ItemType Directory -Force ./.tmp/opening-temp-local | Out-Null
$env:TEMP = (Resolve-Path ./.tmp/opening-temp-local).Path
$env:TMP = $env:TEMP
& $Python -m pytest coderisk/analysis-service-python -q -p no:cacheprovider
& D:/maven/apache-maven-3.9.10/bin/mvn.cmd -f coderisk/backend-springboot/pom.xml test
& D:/node/npm.cmd --prefix coderisk/frontend-vue run build
```

具体运行参数、JUnit 和日志在 S0 目录。首次 Python **8 failed / 423 passed**：标准临时目录的 sandbox 权限错误，不是八个算法缺陷；不删除权限外目录。设置工作区 TEMP/TMP 后 **431 passed / 1 warning，31.64 秒**。Maven **19 passed，BUILD SUCCESS**，H2 集成而非 MySQL。前端类型检查/Vite build 通过。Starlette/httpx、H2/Flyway、Mockito agent、前端大 chunk 是保留的环境/依赖警告。

本轮离线图表最初缺 matplotlib；安装首次又遇临时目录权限，第二次遇包索引 JSON 截断。失败日志保留，按既有 `experiment/requirements.txt` 在可写 TEMP 中重试；最终是否成功以新运行 manifest 为准，不把失败目录视为完整结果。

最终全量回归为 **523 passed / 1 warning，43.77 秒**，比可运行基线新增 92 项。复用虚拟环境的 Tree-sitter 实装 0.26.0 与 `pyproject.toml` 锁定的 0.25.2 不同，因此另将 0.25.2 安装到隔离 `.tmp/opening-tree-sitter-0252-20261011`，通过 `PYTHONPATH` 覆盖并打印真实导入路径，再执行全量：**523 passed / 1 warning，32.47 秒**。旧虚拟环境、项目依赖声明均未改。对应日志 `python-final-r2.*`、`pinned-parser-runtime.log`、`python-pinned-parser.*`；这是有限环境兼容验证，不是所有依赖组合保证。最终 Maven 仍为 19 项 H2 测试通过，前端构建通过。离线 ConPlag 诊断重试完成，无新评分/拟合。

## 3. 实现与论断矩阵

源码路径以下均相对 `coderisk/`；测试位于 `analysis-service-python/tests/`。

| 主张 | 源码/函数与测试证据 | 已支持的结论 | 缺口与措施 |
| --- | --- | --- | --- |
| 受限作用域规范化 | `app/analyzers/canonicalization.py`：`_PythonIndexer`、`_Scope`、`_canonicalize_java`；identifier/invariance 测试 | 已实现且有限验证 | 旧生成准入复用生产索引，不独立；本轮手写绑定 oracle + stdlib symtable |
| 群作用不变性 | `experiment/identifier_renaming.py`：`permutations`、`rename`；历史 288 探针 | 固定域条件草图与有限观察 | 并非完整实现证明；补轨道、商集、前提和逐项证明义务 |
| α-等价 | 作用域角色序列；新增 `test_group_action_noninvariance.py` | 少量捕获规避局部改名可同 C | 统一拼写轨道不是所有局部 α-等价；不声称 C 是完整判定器 |
| 结构相似 | `token_similarity.py`：`sequence_similarity`/`_fingerprints`；`ast_similarity.py` | 节点类型 n-gram 集合重合 | 非树编辑距离/CFG；重复次数可能丢失，新增实际碰撞记录 |
| 融合与画像阈值 | `analyze_token_pair`、`problem_profile.py`；健康/评分/证据 API 测试 | 工程可用、有界分数及风险边际 | 不是群不变总分；效果不保证，保留 ConPlag Full 非最优 |
| 自然相似统计校准 | `experiment/natural_similarity_calibration.py`：`load_references`、`query_tail` | 隔离工具、门禁、冷启动已实现 | 可信独立参考为 0；q 不是抄袭概率，真实误报改善 BLOCKED |
| 跨语言研究表示 | IR/轻量摘要现有模块、experimental 测试和报告 | limited experimental | 不支持完整语义等价，生产权重 0 |
| AI/混合检测 | `llm_baseline.py`、`hybrid_review.py` 的 mock/导入/门禁测试 | 离线工具已实现 | 真实 LLM、完整候选池与效果未验证，绝非 AI 代码检测 |
| 持久化/报告/证据 | Spring repositories、SystemControllerTest、Vue 结果页，现存链路 | H2 后端测试及构建可回归 | MySQL 实库和本轮浏览器端到端 NOT_RUN |
| 数据规模 | 六份登记清单与 readme-data-refresh 快照 | 92,513 公开/候选登记；91 seed；历史 ConPlag 911 探索 | 正式资格 0；不同提交/同题/不同 repo 不自动是独立负例 |

## 4. 具体 P0 缺陷及最小增量

1. **同源 oracle**：旧生成器用于准入的 canonical 标识符位置来自被测索引器；两者共享错误可能共同通过。新 `group_action_oracle.py` 不导入任何 app 模块。手工 marker 决定绑定身份，渲染只计算精确坐标；Python `ast/symtable` 作额外核对，Java 使用手写 golden 与 bounded javac，不能由编译通过证明语义。
2. **Java for/catch 头部遮蔽**：`class Main { int value=7; int f(){for(int value=0;value<1;value++){} return value;} }` 的末尾 value 是字段，旧 brace 索引误附着循环局部。先运行 **2 failed /17 passed** 并保存 `normalization-red.*`；再在 `_canonicalize_java` 中对已识别头部声明的同名可见绑定保守 raw 回退，给出 `JAVA_HEADER_SHADOW_BINDING_UNSUPPORTED` 和行号。基本/增强 for 与 catch 有测试；不是完整 header 作用域实现。
3. **证据与声明差距**：提案仍把统计/LLM 全部写作未实现；同步为“工具已实现/可信效果受阻”。广义交换/重排等仍是设计，不删除历史计划，但标当前未实现。
4. **正式前检不足**：既有 schema/loader 检查路径/hash/split，formal gate 检查双人复核。增加其上层一键 preflight，检查被排除样例的原因、空正式池、负例两来源家族、独立依据、功能/模板/父版本；不创建新标签协议。

## 5. 旧结论保护与验收

新性质探针是自有 synthetic correctness，不是真实数据；新消融是 seed development，不与历史 ConPlag/JPlag 列表混算。ConPlag 原历史 Full F1 0.5543、NoCanon 0.5985、JPlag 0.6133，仍按原 test 627/共同支持说明；模板排除等其他行必须用各自支持集，不能混列证明优劣。

最终通过 `verification.json` 核查上述 252 历史 SHA、88 预存文件、公式/API/schema、HEAD/索引。对确需同步的预存文档只增量编辑并列明，不恢复/覆盖暂存修改。仅本地文件链接通过不等于 clean HEAD/GitHub 已含这些文件；本轮没有上传。

总导航：[开题研究包](OPENING_RESEARCH_PACKAGE.md)。
