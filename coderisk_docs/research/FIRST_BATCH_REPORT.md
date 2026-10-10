# 开题研究第一批交付记录

日期：2026-10-10；仅阶段 0 精准审计与阶段 1 有限规范化。不实现新的相似指标、统计阈值、LLM 或混合检测。

## 改动与风险

| 改动文件 | 内容 | 风险与验收 |
| --- | --- | --- |
| `canonicalization.py` | 内部直接函数关键字参数绑定；动态名称整文件回退；Java 局部声明点；失败时不生成内部伪映射 | 可改变受影响代码的 canonical 可用性/分数，但不改变公式；先写失败测试再修复 |
| `token_similarity.py` | 纳入既有未提交的 reason→PARSER_WARNING 衔接依赖 | 不增加 API 字段，不改权重；5 项新增 API 回归 |
| `test_identifier_invariance.py` | 22 项合法/不支持变换、库名、声明点、总分边界 | 保留红灯记录，55 项新增测试包含本文件 |
| `test_generated_identifier_renaming.py` | 28 项固定域合法置换、逆/复合、拒绝条件与输出冻结 | 合成正确性样本不混入 Research V4 关系标签 |
| `test_research_invariance_api.py` | 5 项 reason/evidence/原文行列/权重回归 | 不伪造 canonical/映射证据 |
| `experiment/identifier_renaming.py` | 可复现自有变体工具，源码哈希与可选 javac 编译 | 不执行代码，不下载学生数据；有限检查不是独立符号表 oracle |
| 研究文档、根 README、规格/路线/开题导航 | 状态纠偏、条件群命题、证据和阻塞说明 | 保留现有架构、截图、启动、数据登记与历史负结果 |

第一阶段提交同时包含此前已有的 `test_python_scope_boundaries.py`、`test_python_fallback_api.py` 及相关规范化基线。它们是新补丁的直接依赖，不夹带其他后端/前端/数据接收暂存改动。精确初始差异见 [审计](IMPLEMENTATION_AUDIT.md)。

## 测试与复现

[实际归档](../../coderisk/experiment/evidence/identifier-invariance-20261010/README.md)：

| 验证 | 结果 |
| --- | --- |
| 初始 red-r2 | 18 项：14 fail / 4 pass；修复前运行 |
| 新增测试三文件 | 55 pass（22+28+5） |
| 当前工作树 Python 全量 | 318 pass，1 条既有 Starlette/httpx warning，0 fail/skip |
| 合法置换探针 | 288/288 C 相同；576 个逆/复合检查通过 |
| Java 编译 | 12/12 pass，覆盖 2 个 fixture 的前 6 变体；不是全部 96 Java 变体编译 |
| Maven | 19 pass，0 fail/error/skip，BUILD SUCCESS；Java 21 + H2 + Flyway V5 |
| npm build | vue-tsc 与 Vite 成功，1699 modules；保留既有 chunk/annotation warning |

本机 Python 为 `E:\ms\.tmp\language-venv\Scripts\python.exe` 3.12.14；旧 Store-Python venv 不可用。正常环境可使用根 README 依赖安装后的 venv；先检查 `--help`。从根目录 PowerShell 运行：

```powershell
$Python = '.\coderisk\analysis-service-python\.venv\Scripts\python.exe'
& $Python -m pytest -q -p no:cacheprovider
& $Python coderisk/experiment/identifier_renaming.py --help
& $Python coderisk/experiment/identifier_renaming.py `
  --output output/identifier-invariance-new-run `
  --seed 20261010 --variants-per-case 48 `
  --java-compiler "$env:JAVA_HOME/bin/javac.exe"
# output 必须是新目录；不提供 java-compiler 会明确记为 NOT_RUN。
Push-Location coderisk/backend-springboot
mvn test
Pop-Location
npm --prefix coderisk/frontend-vue run build
```

本机实际全量命令额外使用 `--basetemp .tmp/research-phase1-full-r1 --junitxml output/research-phase1-full-r1.xml`、`-p no:cacheprovider` 和可写 TEMP。受限进程导致第一次 Maven attach pipe 及 npm realpath 检查失败；在批准的普通本机执行权限下重跑成功。不以旧报告充当新验证。

`FORMULA_SPEC.md` SHA-256 仍为 `562fdb7d68757b811147f9e8d6587e52f8aad01647d002b858329e9ddedf7c20`；标准融合系数、动态阈值及 V4 权重 0 未改。API、数据库、前端代码均无本批新编辑；HTTP 分析回归及 H2 后端测试不等于新浏览器端到端验收。MySQL 缺有效凭据，仍待实库验证。

## 证明、观察与下一步阻塞

条件群命题与证明草图见 [群作用范围](GROUP_ACTION_INVARIANCE.md)。已证的是在固定域、固定保护名称、绑定图正确且遍历结构不变的假设下规范 token 不变；实现证据只是有限测试。未证明所有接受语法、完整 Java 绑定、任意动态 Python、加权总分不变或语义等价。新算法源码哈希保存在 summary，历史结果不能自动迁移到新版。

后续优先级：

1. **可信数据**：完成独立关系的真人双审、题目/source/hash 隔离、自然相似与模板标签。不能把同题不同提交当作独立负例；PoolC 许可、XLCoST 预分词/题目映射、公开关系复核仍受限。
2. **独立消融**：冻结单项/两两/全融合配置，validation 调参、test 冻结。补 PR-AUC、固定 FPR 下 Recall、变换前后变化/耗时；标签不足标不可计算。保留 ConPlag Full 没有获得最高 F1 的探索事实，不在旧 test 上优化。
3. **统计校准**：只在有可信独立解答时构造 `q_p(s)=Pr(S_independent,p>=s)`；需处理共享源码导致的 pair 依赖、样本不足/新题/短代码和模板。q 不是抄袭概率；不改生产规则阈值。
4. **LLM/混合**：本批未实现。默认 dry-run，许可、学生隐私、预算、冻结提示词和可比较基线先成立，混合还须验证候选 Recall@K。

本批达到有限规范化的可运行研究起点，不代表已完成整个研究实施计划。没有新增准确率、误报改善或方法优越性结论。
