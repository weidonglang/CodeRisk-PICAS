# 公平评测流程与复现说明 v1

当前交付是可运行协议及合成数据开发验证。正式数据按 [数据规范](DATA_PROTOCOL.md) 收集，不能把本次开发结果作为真实教学效果证明。

## 1. 新入口及其与历史脚本的关系

新入口为 `coderisk/experiment/run_fair_evaluation.py`，配置为 `coderisk/configs/experiments/fair_v1.json`。历史 `run_research_v4.py` 保留用于既有流程；其中 E3/E4 的固定阈值和重加权不作为新版规范化消融的依据。

新流程读取同一 manifest，先执行来源、分集、哈希及来源家族泄漏检查；只保留已标注可评估的 Java/Python 同语言代码对。降级案例在 PICAS 全样本表中保留；外部工具共同集合另表评价，记录排除及缺失原因。

正式运行默认要求非合成、预注册、双人标注一致与配置冻结记录。`--allow-development` 是显式开发模式，输出带 `DEVELOPMENT / SYNTHETIC SEED` 标记；若将来用于非合成试运行，该标记仍表示开发用途，具体来源以 manifest 为准。

## 2. 方法定义

| 方法名 | 分数 | 阈值选择 |
| --- | --- | --- |
| `FULL_FIXED` | 当前四项综合分 | 验证集选择固定阈值 |
| `FULL_DYNAMIC` | 同一综合分 | 题目阈值 + 验证集选择的 offset，再限于[0.50,0.95] |
| `FULL_DYNAMIC_PRODUCTION` | 同一综合分 | offset固定为0，展示原始生产规则 |
| `NO_CANONICAL_FIXED` | 0.50×原始Token + 0.50×基础结构 | 验证集选择固定阈值 |
| `NO_CANONICAL_DYNAMIC` | 同上 | 验证集选择动态 offset |
| `RAW_FIXED` | 原始Token | 验证集选择固定阈值 |
| `CANONICAL_FIXED` | 规范化Token；不可用时降级原始Token | 验证集选择固定阈值 |
| `JPLAG_FIXED` | JPlag averageSimilarity | 共同验证集选择固定阈值 |

规范化消融同时移除规范化 Token 的0.45权重和标识符映射的0.15权重；保留的0.20/0.20按比例归一为0.50/0.50。解析/规范化不可用时，各 PICAS 方法保留原始 Token 降级路径，并输出降级子组。

`FULL_FIXED` 对比 `FULL_DYNAMIC` 用于题目阈值；`FULL_FIXED` 对比 `NO_CANONICAL_FIXED` 是规范化信号组合的主要消融；动态版本作为交互检查。分别调优阈值的结果表示该预定义方法经验证集校准后的表现，不能解释为其他条件完全不变的单项因果效应。

当前不调优融合权重、题目系数或 JPlag 最小匹配长度。若要搜索这些参数，需另建配置并只使用验证集，记录搜索预算与多次尝试；不得看测试结果后回填“预注册”。

## 3. 参数选择规则

固定阈值从0到1按0.05步长枚举，额外包含 `1.000001` 作为全部判负控制。动态 offset 从−0.20到0.20按0.02步长枚举。

先最大化验证集 F1，再优先较低 FPR；仍平局时，动态阈值优先绝对值较小的 offset，固定阈值优先较高值。动态绝对值仍平局时选较高 offset。规则和候选集保存在配置与 `selected_parameters.json`。验证集缺任一类别则拒绝选择参数。

`RAW_FIXED` 若选0阈值，就意味着这个数据和目标下验证集选择了“全部判正”的退化策略。必须报告混淆矩阵，不能只用召回率掩盖误报。主目标也可在新研究协议中改成固定误报预算下的召回，但不能在测试后临时换目标。

## 4. JPlag 公平对齐

此次固定 JPlag 6.2.0、Java 21、`min-tokens=5`、UTF-8、`averageSimilarity`、输出全部比较、输出最低阈值0。关闭额外 normalize、match-merging 和模板排除。版本号之外还保存 JAR SHA-256 和实际命令；不因发现新版本自动升级基线。

输入按语言交给工具，结果按问题 ID 与代码哈希生成的提交 ID 对齐，再只保留 manifest 中指定的代码对。额外跨题比较不进入评价。方法对比在共同验证集重新选三种方法的阈值，随后评价共同测试集；不能把75对范围内的 PICAS 指标和72对共同范围内的 JPlag 指标直接拼在一起。

缺失比较不是零相似。`baseline_results.csv` 和 `unmatched.csv` 记录缺失、运行失败及预先排除情况；`native/*/stdout.txt`、`stderr.txt` 和原始结果 CSV 可追踪原因。

本次覆盖72/75对，3对被现有适配器按 `UNSUPPORTED_SYNTAX` 排除，属于预先排除而不是 JPlag 实测解析失败。完整对齐清单还包含跨语言和不确定样本的排除记录。

模板排除实验尚未实现于此协议。后续如开展，应保存共同模板，明确双方如何剔除模板并另报结果；JPlag 开启模板去除、PICAS保持原码的结果不能直接声称完全受控。工具参数依据 [JPlag 官方说明](https://github.com/jplag/JPlag) 及本地6.2.0 `--help` 核查。

## 5. 输出与统计

- `scores.csv`：代码对级原始信号、动态阈值、分集、来源组、降级状态。
- `picas/validation_sweep.csv`：验证集候选参数及混淆矩阵。
- `picas/selected_parameters.json`：最终参数和选择规则。
- `picas/metrics.csv`：验证/测试分开，输出 N、TP、FP、TN、FN、Precision、Recall、F1、FPR、自然相似子集数与误报率。
- `picas/subgroups.csv`：语言、题目类型、改写类别、正常/降级子组。
- `picas/predictions.csv` 与 `failures.csv`：逐对阈值、预测和错误，方便复核。
- `picas/intervals.csv`：按题目/来源连通组进行1000次有放回抽样，输出百分位区间和有效抽样次数；包含动态减固定的配对差值。
- `jplag/`：原始工具记录、共同数据、独立调参和对应统计。
- `comparison.png/svg`：供阅读和后续制图使用，明确开发集身份。
- `run_manifest.json`：配置、数据、源码哈希，Git基点与脏工作区标记，机器、依赖、版本和正式数据阻塞原因。

分母为零的统计记为 JSON `null`、CSV空值、报告 `N/A`。区间固定已经选出的参数，不包含调参不确定性；独立组很少时区间不稳，不能只看是否跨0宣称显著改进。

## 6. 复现命令

在项目目录 `E:\ms\coderisk` 使用已建分析服务虚拟环境。图表依赖安装在项目虚拟环境中：

```powershell
& .\analysis-service-python\.venv\Scripts\python.exe -m pip install -r .\experiment\requirements.txt
& .\analysis-service-python\.venv\Scripts\python.exe .\experiment\run_fair_evaluation.py --config .\configs\experiments\fair_v1.json --output .\data\artifacts\experiments\FAIR-DEV-NEW --allow-development --java D:\DevEnvManager\envs\jdks\temurin-21\bin\java.exe --jplag-jar .\data\tools\jplag\jplag-6.2.0-jar-with-dependencies.jar
```

输出目录必须不存在；每次使用新名称。别的电脑须换成本机 Java 21+ 与相同哈希的 JAR 路径。`--skip-jplag` 只能验证 PICAS 流程，报告将明确标记跳过。正式运行改为真实数据配置并去掉 `--allow-development`。

可复现含义是相同源码、依赖、数据、配置下分数、选择参数、混淆矩阵和抽样统计一致。完成时间、日志路径和机器描述随环境变化；PNG/SVG字节跨绘图库或字体版本也可能不同，应以原始 CSV 为准。

## 7. 当前结果如何用于开题

可以写“已完成并运行验证集调参、规范化消融、JPlag共同集合比较及图表生成流程”。不能写“已经证明对真实学生作业效果优于 JPlag”。开发结果包含无收益和退化方法，应作为改进实验设计的线索，不把旧测试分区继续当作新的独立测试证据。
