# ConPlag 公开标签探索证据

运行前冻结目录：`../conplag-registration-20261009`。本目录的原始 JSON 和 CSV 来自实际分析器及 JPlag 输出，客户端日期 2026-10-09。全部均为探索性外部标签结果，正式指标资格没有改变。

- `run_summary.json`：911 对两个视图、全集合/共同集合的测试统计、缺失数量及运行版本。
- `protocol_snapshot.json`：本次实际使用的运行前方案与实现哈希。
- `version_*/picas_scores.jsonl`：逐对生产一致的评分、消融、结构/规范化回退信息。
- `version_*/jplag_scores.jsonl`：请求的每对原生分数；缺失保持 null。
- `version_*/evaluation.json`：验证扫描、选参、测试表、15 题目分组 bootstrap 区间、排除清单。
- `version_*/jplag/*/native/java/`：原生结果 CSV、stdout/stderr，可核对导入分数；未保存包含源码的 input 或报告包。
- `metric_tables.csv`：36 行验证/测试统计，归档时已从逐对分数重新计算核对。
- `test_comparison.png/svg/pdf`：同一测试集合的 F1、FPR 与题目抽样区间；不表示显著性检验。
- `artifact_inventory.json`：归档生成的 141 个结果文件哈希；本说明为后加解释文件，不在该库存中。`run_start.json` 的 RUNNING 是启动事件，最终状态以 `run_summary.json` 为准。

复现归档（使用新输出目录）：

```powershell
python coderisk/experiment/archive_conplag_pilot.py --input coderisk/data/public-datasets/conplag-pilot-20261009 --output coderisk/experiment/evidence/conplag-pilot-replay
```

Matplotlib 等绘图依赖由 `experiment/requirements.txt` 安装。使用冻结运行器重新计算前须准备被忽略的公开下载数据和相同注册依赖，流程见运行前说明。结果解读与完整方法边界见 [中文报告](../../../../coderisk_docs/proposal/CONPLAG_PILOT_RESULTS.md)。
