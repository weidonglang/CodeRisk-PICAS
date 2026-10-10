# 有限标识符改名正确性证据

2026-10-10 本机实际运行，基线 commit `3c8ac81cd1f9ef0f80a52505c621f6ce8b70abe5` 加未提交的第一阶段补丁；算法及公式文件 SHA-256 见 `summary.json`，不要将基线 commit 单独当作完整运行源码版本。

本目录仅含自有 synthetic correctness probes，不是真实学生数据或 benchmark。6 个 fixture、每例 48 个固定域唯一置换，288/288 完整 canonical token 相等，576 次逆/复合源码检查通过。formalEligiblePairs=0，不能据此计算检测准确率或声称减少误报。

| 文件 | 含义 |
| --- | --- |
| `fixtures.json` | 6 个自有 fixture，固定名称域与源码 |
| `variants.jsonl` | 全部 288 个变体、映射、源码及 equality/hash 记录 |
| `summary.json` | 版本、seed、UTC、sourceHashes、耗时及实际 javac 状态 |
| `REPORT.md` | runner 原样生成的简要汇总 |
| `research-invariance-red-r2.xml` | 修复前 18 项测试，14 fail / 4 pass；失败是预期红灯历史，不是最终回归状态 |
| `research-phase1-full-r1.xml` | 修复后当前完整工作树 318 pass；含其他未提交任务的既有测试，不宣称 clean HEAD 有 318 项 |
| `research-phase1-new-only-r1.xml` | 三个新增测试文件单独重跑，55 pass，1 条既有 warning |

记录由 `output/identifier-invariance-20261010-r2` 和实际 pytest 输出原样复制，不更改测试结果。Java 96 个变体中只对每个 Java fixture 的前 6 个进行 javac 21.0.11 编译，12/12 通过；没有执行代码，也没有声称全部 Java 变体编译过。运行总耗时 4.952237 秒，其中规范化探针约 0.390135 秒，仅代表本机自有小样例。

同批后端 Maven 本次 19 项 H2 测试成功（0 failure/error/skip，BUILD SUCCESS），前端 vue-tsc/Vite build 成功；Maven XML 留在本机 `target/surefire-reports`，不打包包含大量环境属性的日志。MySQL 实库、浏览器端到端与外部 JPlag 本轮没有重验。

复现命令、环境及支持边界见 [第一批交付](../../../../coderisk_docs/research/FIRST_BATCH_REPORT.md) 和 [群作用定义](../../../../coderisk_docs/research/GROUP_ACTION_INVARIANCE.md)。默认 output 必须使用新目录，避免覆盖历史；Java 编译为显式可选，未运行就记录 NOT_RUN。
