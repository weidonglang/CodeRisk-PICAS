# 开题 S0—S5 精选证据 · 2026-10-11

**SYNTHETIC_DEVELOPMENT / PUBLIC_PILOT_READONLY / FORMAL_BLOCKED 分别标记，不是正式benchmark。**

本目录只收自有gold、seed数值表、公开pilot的数值诊断及测试证据；不包含新增学生数据/真实授权/身份/模型响应。全量不可覆盖输出在根 `output/opening-research-20261011/`。未自动commit/push，不表示GitHub已更新。

## 输入与真实结果

| 目录 | 类型/输入 | 结果与边界 |
| --- | --- | --- |
| properties | 自有12手标gold，三seed×48 | 1,728接受全部通过；尝试总1,738，拒绝5/parser2/capture1/uncertain2不算成功，6次Java编译不执行 |
| ablation | 原91synthetic seed | 75分析、68共同支持、共同test36；14方法全保留，生产Full非最优 |
| natural | 原seed+独立参考manifest | 可信reference0、q可用0、全RULE_FALLBACK，不支持统计收益 |
| readiness | 现有schema/manifest+证据/冻结前检 | FORMAL_BLOCKED，91/ready0/formal0，require-ready退出2符合预期 |
| conplag-readonly | 历史两view各911公共标签 | 0重评分/拟合，已有test只描述；Full F1低于NoCanon负结果保留 |
| tests | 实际工作树Python、H2Maven、Vuebuild | 最终523/19/build通过；红测和TEMP/依赖失败保留，不是准确率/MySQL/E2E |

Python 额外按项目声明 Tree-sitter 0.25.2 的隔离覆盖运行，仍为523项通过；旧复用环境实装0.26.0的差异及真实导入路径保留在`tests/pinned-parser-runtime.log`。不能把旧环境的`pip-freeze.txt`当成已完全匹配锁定依赖。

`properties/fixture_summary.csv` 是唯一置换/源码与稳定子统计；1,728不是不同程序/独立作者。`discrimination.csv` 的两/三重复增量C不同但fingerprint/融合1，是自有信息损失机制，不能算真实FPR。`rename_sensitivity.csv` 显示raw/融合改名敏感性，不称总分群不变。

`ablation/metrics.csv`的COMMON主表与AVAILABLE/LOW_FPR诊断不能混算；Recall@K缺完整pool为N/A；`parser_fallbacks.csv`保留不支持。ConPlag两view仍是同911对不同背景，不是1,822独立pair。旧JPlag没有被重新运行或拼接新版scores。

## 版本与保护

`verification.json`记录HEAD/暂存条目、生产公式/API/schema和252旧artifact SHA保护、预存88文件的允许文档增量/未计划修改核查、链接检查及本轮文件SHA。`failure_records.json`区分真实环境/缺陷/预期门禁及完整日志是否存在。`artifact_hashes.json`核对本目录除自引用manifest以外的选定文件；本机环境在tests记录，不能单凭Git SHA复现dirty工作树。

源码/配置hash在各run_manifest中；源码以本轮工作树为准，而不是pip freeze里的旧editable VCS HEAD。图表依赖是现有experiment requirements，未改生产依赖。测试fixture的HUMAN/授权声明只用于UNIT_TEST_ONLY分支验证，不是实际关系标注。

## 从根目录复现

```powershell
$Python = (Resolve-Path ./coderisk/analysis-service-python/.venv-opening/Scripts/python.exe).Path
# 先按研究包准备新.venv-opening；本机实跑复用了.tmp/language-venv，不要求其他人有该路径。
& $Python coderisk/experiment/group_action_properties.py --output output/NEW-properties
& $Python coderisk/experiment/similarity_ablation.py --output output/NEW-ablation --allow-development
& $Python coderisk/experiment/diagnose_fusion.py --output output/NEW-readonly
& $Python coderisk/experiment/natural_similarity_calibration.py --output output/NEW-natural --allow-development
& $Python coderisk/experiment/check_formal_readiness.py --output output/NEW-readiness --require-ready
```

没传javac时编译记录为空，不冒称6次通过；实际本轮传了Java21编译器。详细从零安装、完整命令、支持边界、真人采集及论文取表见 [开题研究包](../../../../coderisk_docs/research/OPENING_RESEARCH_PACKAGE.md)、[双维报告](../../../../coderisk_docs/research/INVARIANCE_DISCRIMINABILITY_REPORT.md) 和 [测试报告](../../../TEST_REPORT.md)。
