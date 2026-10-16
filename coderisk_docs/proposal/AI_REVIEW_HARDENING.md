# AI 分工检查与边界修复记录

日期：2026-10-09。检查基于 `9d4e90f` 后的开发版本；本轮提交将保存最终源码。用户授权启用子智能体后，三个子智能体分别检查作用域、任务后端、数据流程，根代理整合、验证前端和同步文档。它们是同一会话中的 AI 执行者，不能等同真人复核，也不能据此宣称独立模型间一致性。

## 已完成的修复

| 范围 | 发现的问题 | 当前行为与验证 |
| --- | --- | --- |
| Python lambda | 默认值未正确遍历，变长参数遗漏 | 默认值查找外层，函数体查找参数；支持 `*args`、`**kwargs` 的受限规范化，自有改名/遮蔽回归 |
| Python 类与方法 | 方法裸名称误捕获类属性；嵌套类查找及定义期先读后绑定不可靠 | 方法体和嵌套类体跳过外层类命名空间，默认值保留定义期查找；类体先读后绑定、动态定义期绑定与自定义命名空间明确回退 |
| 不完整作用域 | 推导式、global/nonlocal、注解等仍生成似乎可靠的映射 | 整文件回退原始 Token，清空标识符；原因含类别、节点和原文行号，进入 `PARSER_WARNING`；规范化及映射权重为 0 |
| 结果分页 | 极大页码乘法溢出导致 500 | 以 `long` 计算偏移，超出范围返回空页；接口回归包含 page=2147483647 |
| 任务重启恢复 | 结果已提交但恢复标记未写入，失败历史永久显示待重试 | 启动恢复 RUNNING 时按已存结果同步 `resolved`，保留原错误、失败次数与时间；模拟崩溃窗口验证 |
| 同题并发 | 两个事务同时首次写题目画像，删除/插入发生冲突 | 锁已有 question 行后更新画像，加入结果保存事务；两线程独立事务锁等待验证，历史结果快照保留 |
| 最终页面刷新 | 状态和结果并行读取，FINISHED 与过期空结果可能组合，轮询停止 | 先读取任务状态，再并行读取结果、汇总和失败；浏览器控制最终写入时序，确认最后一对实际显示 |
| IR 来源核验 | 改元信息并重算自述哈希可能绕过校验 | 用固定哈希 ZIP 离线重建完整 467 份来源与关系，检查必需 manifest、库存、身份、争议标记、文本/字节哈希和两登记表 |
| 复核队列 | 按题/标签分块、争议放末尾、参考总在 A，透露类别 | 稳定全局哈希排序及 A/B 互换，裁决文件记录方向；输出必须是新目录，保留旧包；原始注释仍可能泄露类别，仍仅称分数盲审 |

类命名空间不延伸到方法体、推导式另有作用域，依据 [Python 3.12 名称解析规则](https://docs.python.org/3.12/reference/executionmodel.html#resolution-of-names)及[表达式规则](https://docs.python.org/3.12/reference/expressions.html#displays-for-lists-sets-and-dictionaries)。这是静态工具的受限实现；没有编译或执行上传/下载的源码来确认语义。

## 支持范围和代价

已修复的 Python 规范化仍非完整语言实现。推导式、global/nonlocal、赋值表达式、except-as、match 捕获、import 别名/通配、函数和变量注解、类型参数/type alias、类定义期的控制流/删除/增量赋值、先读后绑定、显式 metaclass 及直接动态命名空间操作暂回退。一个文件存在这些形式时，整个代码对的生产加权分数按既有规则回退原始 Token；基础 AST 仍可作为零权重展示信号。不会给不可靠名称绑定生成变量映射证据。

回退可能降低对改名的敏感性，不能解释为准确率提高；新的作用域检查将改变部分 Python 样本的评分路径。原四项融合权重及动态阈值公式未调优。冻结 ConPlag 探索记录仍绑定旧实现，不用于声称本轮算法效果；若重评必须使用新目录、标明数据已见，并另准备确认性保留集。

## 真人与 AI 复核登记

新工作台导出 `coderisk-blind-review-2`，包含 `reviewer_type=HUMAN|AI` 与 `reviewer_context`。AI 必填模型或智能体来源；第一次保存锁定 ID、类型与背景。合并器把旧导出记作 `UNSPECIFIED`，AI 参与的一致结果记 `AI_AGREED`；不同 ID 不能证明不同真人。`declared_human_review_count` 只是声明计数，`human_pair_identity_verified` 始终为 false，合并始终不自动赋予正式资格。

正式研究协议新增两位执行者类型都为 HUMAN、`independence_confirmed=true` 的要求，同时仍要求关系/功能依据、许可、来源家族、预注册划分及冻结配置。这些字段只是有责任人确认的声明，软件无法认证真实身份；实际执行者和独立性应由学生/导师核实。三份 AI 技术检查不填入两位真人标注栏，也未形成实质样本标注。

## 新复核材料与证据

新版仍为同一 52 对，新增数据数量为 0，IR-Plag 本地真人复核、正式资格、检测器评分仍均为 0。新版 review_id 含 A/B 方向，不能将旧导出直接合并到新清单；manifest/源码哈希不符会拒绝。旧 52 对和已有 43 对工作台均为历史材料，不覆盖。

新本地入口：`coderisk/data/public-datasets/irplag-20261009/review-v2/workbench.html`。公开仓库只保存元数据；裁决标签文件不要在独立复核前展示。可复现命令从仓库根目录运行，换用尚不存在的输出目录：

```powershell
python coderisk/experiment/acquire_irplag.py --verify-only --cache .tmp/irplag-source
python coderisk/experiment/prepare_irplag_review.py --output output/irplag-review-new --workbench-output coderisk/data/public-datasets/irplag-20261009/review-new --cache .tmp/irplag-source
```

工程验证和执行限制见 [本轮证据](../../coderisk/experiment/evidence/review-hardening-20261009/README.md)，复核元数据见 [新版清单](../../coderisk/experiment/evidence/irplag-review-v2-20261009/README.md)。浏览器时序脚本 [verify_task_result_browser.js](../../coderisk/experiment/verify_task_result_browser.js)需本地 Vue 端口 15173 和专用 Playwright CLI 会话；删除整行注释并把换行转换为空格后作为 `run-code` 参数，可避免 Windows 命令行的多行传参问题。

## 仍需完成

真实双人标注与分歧裁决、自然相似子集、参数冻结后的独立效果评测仍未完成。MySQL 实库并发、跨机器复现和真实目标负载仍待验证；当前持久化与锁测试使用 H2 MySQL 模式。Java 完整语法、Python 全作用域语义及 C/HTML 准确率均没有获得完整证明。毕设目前可展示实现、来源审计、失败案例和可复现工程记录；正式论文结论必须等待这些研究证据。
