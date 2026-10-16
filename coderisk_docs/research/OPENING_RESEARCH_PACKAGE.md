# S0—S5 开题研究包：总导航与从零复现

日期：2026-10-11。本轮完成可自动的实现、有限验证、研究草稿与工具，**没有新正式benchmark、真人授权/标注、MySQL实库、真实LLM或新浏览器演示结论**。未推送/发布/提交Git；HEAD及预存暂存工作保持。

## 1. 阅读顺序与阶段状态

| 阶段 | 状态 | 产物与边界 |
| --- | --- | --- |
| S0 | DONE | [实际基线审计](OPENING_BASELINE_AUDIT.md)，状态/hash/测试/主张矩阵及旧产物保护 |
| S1 | DONE（草稿待学术审核） | [轨道/α/商集](ORBIT_ALPHA_EQUIVALENCE.md)、[义务/反例](GROUP_ACTION_PROOF_OBLIGATIONS.md)、[历史及新定义](GROUP_ACTION_INVARIANCE.md) |
| S2 | DONE（有限子集） | 独立手标oracle、性质/边界/API测试、Java头部遮蔽红→raw降级；不是全语言证明 |
| S3 | PARTIAL | [双维结果](INVARIANCE_DISCRIMINABILITY_REPORT.md)已实跑；正式效果BLOCKED，不改历史分数 |
| S4 | PARTIAL | [采集教程](REAL_DATA_ACTION_GUIDE.md)、[公平协议V2](FAIR_EVALUATION_PROTOCOL_V2.md)、[人工责任](HUMAN_REQUIRED_CHECKLIST.md)、一键前检；真人/参考数据待提供 |
| S5 | DONE（内容稿） | [开题初稿](../proposal/PROPOSAL_DRAFT.md)、[文献矩阵](../proposal/LITERATURE_MATRIX.md)、[答辩QA](OPENING_DEFENSE_QA.md)、README/报告/范围同步；学校模板/导师签署仍待用户 |

## 2. 关键实现与结果位置

`coderisk/experiment/group_action_oracle.py`：12自有hand-marked绑定gold、独立renderer/tokenizer/stdlib检查、明确边界；`group_action_properties.py`：三seed、完整C/gold/恒等/逆/复合、唯一源码/稳定子、4种机制和分数敏感性，immutableJSON/CSV/MD；`check_formal_readiness.py`：复用现有manifest/schema/loader/质量协议，检查资格/冻结/泄漏/独立/功能/模板/父版本及统计参考，不写标签。

生产仅 `analysis-service-python/app/analyzers/canonicalization.py::_canonicalize_java` 增加已知for/catch遮蔽降级；API、数据库、生产融合/动态公式不改。新增测试均在 `analysis-service-python/tests/test_group_action_*.py`、`test_opening_*readiness*.py`。详细文件哈希、改动清单及原始命令在新artifact中。

全量本地：`output/opening-research-20261011/{s0,properties-final,ablation,natural,readiness-final,conplag-readonly-r2}`；公开精选：[本轮证据目录](../../coderisk/experiment/evidence/opening-research-20261011/README.md)。旧目录不覆盖。自有gold不是91seed的新真实关系case，公开候选总量也未因本轮变成正式数据。

## 3. 从仓库根目录建立环境

以下使用**新虚拟环境**，不覆盖旧`.venv`或用户环境；Python3.12/Java21/Node/npm/Maven需先安装/加入PATH。实际用过的本机路径在S0，不要求他人照抄开发者盘符。先`--help`确认当前参数。

```powershell
# 当前目录须为含 coderisk/ 和 coderisk_docs/ 的仓库根目录。
python --version
java --version
node --version
mvn --version
python -m venv ./coderisk/analysis-service-python/.venv-opening
$Python = (Resolve-Path ./coderisk/analysis-service-python/.venv-opening/Scripts/python.exe).Path
New-Item -ItemType Directory -Force ./.tmp/research-temp | Out-Null
$env:TEMP = (Resolve-Path ./.tmp/research-temp).Path
$env:TMP = $env:TEMP
& $Python -m pip install -e './coderisk/analysis-service-python[dev]'
& $Python -m pip install -r ./coderisk/experiment/requirements.txt
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'matplotlib'
& $Python -m pytest ./coderisk/analysis-service-python -q -p no:cacheprovider `
  --basetemp ./.tmp/research-test-NEW --junitxml ./output/research-test-NEW.xml
mvn -f ./coderisk/backend-springboot/pom.xml test
npm --prefix ./coderisk/frontend-vue ci
npm --prefix ./coderisk/frontend-vue run build
```

虚拟环境路径若已存在，不重复创建覆盖，复用确认可用的环境或改新名。TEMP/TMP必须可写；首次sandbox临时目录错误不能解释成算法失败。matplotlib为现有离线图表依赖，非生产服务依赖；网络索引截断时记录失败再重试，安装版本由pip freeze保存，不从失败目录取图。

## 4. 本轮独立性质与实验复现

新RUN_ID避免覆盖，下面示例不得指向已存在的本轮目录。群探针只编译自有gold；不执行原始学生/公共代码。Java路径从JAVA_HOME查找，没javac可省参数，报告必须写未编译而不能假通过。

```powershell
$Run = 'opening-REPLACE-WITH-NEW-ID'
$Out = Join-Path './output' $Run
& $Python coderisk/experiment/group_action_properties.py --help
& $Python coderisk/experiment/check_formal_readiness.py --help
& $Python coderisk/experiment/group_action_properties.py `
  --output "$Out/properties" --seeds 20261011 73 901 --variants 48 `
  --javac "$env:JAVA_HOME/bin/javac.exe"
& $Python coderisk/experiment/similarity_ablation.py `
  --output "$Out/ablation" --allow-development
& $Python coderisk/experiment/diagnose_fusion.py --output "$Out/conplag-readonly"
& $Python coderisk/experiment/natural_similarity_calibration.py `
  --output "$Out/natural" --allow-development
& $Python coderisk/experiment/check_formal_readiness.py `
  --output "$Out/readiness" `
  --statistical-config coderisk/configs/experiments/natural_calibration_v1.json --require-ready
# 当前seed预期：最后一条退出2，FORMAL_BLOCKED /可信参考0；不是全部工具失败。
```

性质成功需run_manifest.status=COMPLETED、failedAssertions=0，编译记录真实PASSED（没传编译器则为空，不是PASS）；检查所有status分母、fixture唯一source和生产mode边界。ablation需run/config/source/data hash、scores/metrics/selection/coverage/failure/borderline/parser fallback均存在；allow-development formalEligiblePairs必须0。

当前q输出不应伪造数值：可信reference0时q unavailable且RULE_FALLBACK；Formal preflight退出2是正确门禁结果。真实新数据必须换config.datasetManifest/referenceManifest，走采集/双审/分组/冻结后**不加allow-development**，不能改默认seed文件假装真实集合。

业务服务启动、MySQL切换和前端演示沿用 [coderisk运行手册](../../coderisk/README.md) 与 [根README](../../README.md#快速启动)；实验脚本直接导入分析模块，可离线运行，不必先启动三个HTTP服务。本轮没有重做浏览器联调。

## 5. 图表如何用于开题/论文

`gold_bindings/fixture_summary/properties.csv`：实现/性质证据；`discrimination.csv`：特定信息损失例子；`rename_sensitivity.csv`：raw/融合的名字敏感性，不是真实准确率。`ablation/metrics.csv` COMMON主表、coverage/AVAILABLE诊断、failures/borderline/AP/low-FPR全保留。`conplag-readonly-r2/component_summary.csv`、冻结decision表/图/changed pair是已观察PUBLIC_PILOT描述，不是新holdout效果。自然校准allfallback不能用于q收益论证。

失败分析写“机制→实际指标/证据→标签来源→适用边界→不能推论”；威胁包括人工gold误标、Java近似parser/动态黑名单、合成构造偏差、公开单人标签/cohort/重复、pair依赖、共同支持选择偏差、冷启动与模板/短代码、参数可见性、工具版本/模板可比性。无真实数据/重复/群组区间时，不写显著效果。

建议本科论文目录：绪论与相关工作；需求/风险复核边界；架构/API/持久化；受限G/绑定规范化与有界题目规则；独立性质验证与公平实验设计；有授权数据的实际结果/失败/局限；总结与展望。当前可先用内容稿写前四章和实验方法，不填不存在的正式结果。

## 6. 验收及下一步

真实测试最终数值见 [TEST_REPORT](../../coderisk/TEST_REPORT.md)。当前HEAD/索引、252历史SHA、未计划修改的预存文件与生产公式应由新verification.json逐项确认。新报告带现有working-tree修改，不称cleanHEAD/GitHub已更新。

P0：按教程取得真实来源/授权/双审/功能/独立证据，导师核查理论/引用，冻结新题目集。P1：新集合比较误报与召回、真正MySQL/浏览器演示、更多独立Java绑定对照。P2：在可靠结果后才提新表示/融合实验、LLM授权/预算，继续生产隔离。
