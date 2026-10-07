# Run Research V4

本文档给出从补数据到生成 Research V4 结果的完整 PowerShell 流程。当前推荐使用仓库内分析服务 venv 解释器；如果你的本机 `python` 命令可用，可以把 `$PY` 替换成 `python`。

## 0. 准备环境

从项目根目录执行：

```powershell
cd E:\ms\coderisk
$PY = ".\analysis-service-python\.venv\Scripts\python.exe"
$env:JAVA_HOME = "D:\DevEnvManager\envs\jdks\temurin-21"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

如参数记不清，先看帮助：

```powershell
& $PY experiment\validate_research_v4_dataset.py --help
& $PY experiment\add_research_v4_case.py --help
& $PY experiment\calibrate_dynamic_threshold.py --help
& $PY experiment\run_research_v4.py --help
& $PY experiment\research_v4_jplag.py --help
```

## 1. 启动三项服务

Research V4 实验脚本本身不依赖前后端服务，但端到端演示需要启动：

```powershell
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd E:\ms\coderisk; .\scripts\start-backend-dev.ps1"
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd E:\ms\coderisk; .\scripts\start-analysis-dev.ps1"
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd E:\ms\coderisk; .\scripts\start-frontend-dev.ps1"
```

健康检查：

```powershell
Invoke-WebRequest http://127.0.0.1:8080/actuator/health
Invoke-WebRequest http://127.0.0.1:8001/internal/health
Invoke-WebRequest http://127.0.0.1:5173
```

MySQL 边界：当前已验证 H2 fallback 和 Flyway；如无有效 MySQL 凭据，不要声称 MySQL 实库验证完成。

## 2. 添加新 case

先把代码文件放入合适目录，例如：

```text
experiment/datasets/research-v4/samples/manual/P-MANUAL-001/A.java
experiment/datasets/research-v4/samples/manual/P-MANUAL-001/B.java
```

预览 manifest entry，不追加：

```powershell
& $PY experiment\add_research_v4_case.py `
  --pair-id MANUAL-JAVA-RENAME-001 `
  --problem-id P-MANUAL-ARRAY-001 `
  --problem-type array_loop `
  --problem-group G2 `
  --dataset-split validation `
  --source-id SRC-MANUAL-ARRAY-001 `
  --source-type manual `
  --experiment-label TRANSFORMED `
  --case-type VARIABLE_RENAME `
  --language-a java `
  --language-b java `
  --code-a samples/manual/P-MANUAL-001/A.java `
  --code-b samples/manual/P-MANUAL-001/B.java `
  --title "Array loop manual sample" `
  --description "Traceable manual pair for variable rename testing." `
  --license-or-authorization "author-created sample for CodeRisk Research V4" `
  --manual-check-status VERIFIED `
  --functional-check-status PASSED `
  --eligible-for-core-metrics
```

检查输出里的 `pending_confirmation_fields`。只有它为空时，才追加：

```powershell
& $PY experiment\add_research_v4_case.py `
  --pair-id MANUAL-JAVA-RENAME-001 `
  --problem-id P-MANUAL-ARRAY-001 `
  --problem-type array_loop `
  --problem-group G2 `
  --dataset-split validation `
  --source-id SRC-MANUAL-ARRAY-001 `
  --source-type manual `
  --experiment-label TRANSFORMED `
  --case-type VARIABLE_RENAME `
  --language-a java `
  --language-b java `
  --code-a samples/manual/P-MANUAL-001/A.java `
  --code-b samples/manual/P-MANUAL-001/B.java `
  --title "Array loop manual sample" `
  --description "Traceable manual pair for variable rename testing." `
  --license-or-authorization "author-created sample for CodeRisk Research V4" `
  --manual-check-status VERIFIED `
  --functional-check-status PASSED `
  --eligible-for-core-metrics `
  --append
```

AI-assisted case 必须额外提供：

```powershell
  --model-name "model/provider/version" `
  --prompt-template "prompt text or prompt file path" `
  --temperature 0.2 `
  --generation-time "2026-07-05T12:00:00+08:00"
```

未达到 `manual_check_status=VERIFIED` 和 `functional_check_status=PASSED` 的 AI_REWRITE 会被挡在核心指标外。

## 3. 校验数据集与泄漏

```powershell
$VALIDATION_DIR = "data\artifacts\experiments\RESEARCH-V4-DATASET-CHECK-$(Get-Date -Format yyyyMMdd-HHmmss)"
& $PY experiment\validate_research_v4_dataset.py `
  --manifest experiment\datasets\research-v4\dataset.json `
  --output-dir $VALIDATION_DIR
```

重点查看：

```text
$VALIDATION_DIR\validation_report.md
$VALIDATION_DIR\validation_report.json
$VALIDATION_DIR\case_index.csv
$VALIDATION_DIR\coverage_gaps.csv
$VALIDATION_DIR\dataset_statistics.csv
```

成功标准：

```text
valid=true
problemOverlap=[]
sourceOverlap=[]
exactCodeOverlapCases=[]
新增数据没有 pending / placeholder 误入核心指标
```

## 4. 运行 Research V4 完整实验

使用新的不可变 run id：

```powershell
$RUN_ID = "PICAS-RESEARCH-V4-MANUAL-$(Get-Date -Format yyyyMMdd-HHmmss)"
& $PY experiment\run_research_v4.py `
  --config configs\experiments\research_v4.json `
  --run-id $RUN_ID
```

输出目录：

```text
data/artifacts/experiments/<RUN_ID>/
```

如果提示目录已存在，换一个新的 run id。实验输出是不可变产物，不要覆盖旧结果。

## 5. 单独运行动态阈值校准

完整 runner 已自动运行校准。若要单独复现：

```powershell
$RUN_ID = "PICAS-RESEARCH-V4-SEED-20260624-R2"
& $PY experiment\calibrate_dynamic_threshold.py `
  --predictions data\artifacts\experiments\$RUN_ID\same_language\predictions.csv `
  --output-dir data\artifacts\experiments\$RUN_ID\calibration-rerun `
  --run-id $RUN_ID `
  --formula-version FORMULA_SPEC_V1 `
  --algorithm-version picas-v2-rule-1.0 `
  --dataset-version coderisk-research-v4-seed-1.0 `
  --random-seed 20260624
```

校准纪律：

```text
validation 选择参数
test 只评估一次
testSetUsedForSelection=false
productionFormulaChanged=false
```

不要把 seed 上选出的 offset 写回生产公式。

## 6. 运行 JPlag 对齐

只准备输入目录和对齐表：

```powershell
$JPLAG_RUN = "PICAS-RESEARCH-V4-JPLAG-$(Get-Date -Format yyyyMMdd-HHmmss)"
& $PY experiment\research_v4_jplag.py `
  --manifest experiment\datasets\research-v4\dataset.json `
  --output-dir data\artifacts\baselines\jplag\$JPLAG_RUN
```

执行真实 JPlag 并对齐 PICAS 预测：

```powershell
$PICAS_RUN = "PICAS-RESEARCH-V4-SEED-20260624-R2"
$JPLAG_RUN = "PICAS-RESEARCH-V4-JPLAG-$(Get-Date -Format yyyyMMdd-HHmmss)"
& $PY experiment\research_v4_jplag.py `
  --manifest experiment\datasets\research-v4\dataset.json `
  --output-dir data\artifacts\baselines\jplag\$JPLAG_RUN `
  --jplag-jar data\tools\jplag\jplag-6.2.0-jar-with-dependencies.jar `
  --java D:\DevEnvManager\envs\jdks\temurin-21\bin\java.exe `
  --execute `
  --picas-predictions data\artifacts\experiments\$PICAS_RUN\same_language\predictions.csv
```

JPlag 输出：

```text
data/artifacts/baselines/jplag/<JPLAG_RUN>/alignment_manifest.csv
data/artifacts/baselines/jplag/<JPLAG_RUN>/excluded_pairs.csv
data/artifacts/baselines/jplag/<JPLAG_RUN>/baseline_results.csv
data/artifacts/baselines/jplag/<JPLAG_RUN>/jplag_vs_picas.csv
data/artifacts/baselines/jplag/<JPLAG_RUN>/run_manifest.json
```

如新增 JPlag run，要把 `configs/experiments/research_v4.json` 的 `jplagAlignedManifest` 和 `jplagAlignedResults` 指向新目录，再重跑完整实验。

## 7. 结果目录怎么看

完整 runner 输出：

```text
run_manifest.json
metrics_summary.json
research_report.md
dataset_validation/
same_language/
cross_language/
calibration/
baseline_analysis/
paper_tables/
case_analysis/
baseline_registry.csv
```

常用文件：

```text
paper_tables/table_dataset_statistics.csv
paper_tables/table_fixed_vs_dynamic.csv
paper_tables/table_raw_vs_canonical.csv
paper_tables/table_fusion.csv
paper_tables/table_ablation.csv
paper_tables/table_cross_language.csv
paper_tables/table_dynamic_threshold_calibration.csv
paper_tables/table_baseline_comparison.csv
paper_tables/table_jplag_vs_picas.csv
case_analysis/failure_cases.csv
case_analysis/borderline_cases.csv
case_analysis/common_structure_cases.csv
case_analysis/unsupported_syntax_cases.csv
case_analysis/failure_analysis.md
```

实验成功的基本标准：

```text
run_manifest.json 存在
dataset_validation/validation_report.json 里 valid=true
run_manifest.json 里 productionFormulaChanged=false
run_manifest.json 里 experimentalMetricsProductionWeight=0.0
paper_tables/ 表格非空
case_analysis/ 有失败和边界样例输出
```

## 8. 更新文档和论文材料

每次正式 run 后，至少更新：

```text
TEST_REPORT.md
coderisk_docs/EXPERIMENT_PLAN.md
coderisk_docs/PAPER_OUTLINE.md
experiment/datasets/research-v4/DATA_CARD.md
```

更新时必须写清楚：

```text
数据来源比例
manual / ai_assisted / external 数量
validation/test 是否 problem-disjoint
校准是否只用 validation
JPlag 排除数量和原因
哪些结论只是 exploratory
```

## 9. 常见错误

`python.exe` 拒绝访问：

```text
使用 $PY = ".\analysis-service-python\.venv\Scripts\python.exe"
```

run id 已存在：

```text
换一个新的不可变 run id，不覆盖旧目录。
```

`pending_confirmation_fields` 非空：

```text
补齐 title、description、license_or_authorization，AI case 还要补模型、prompt、生成时间和验证状态。
```

problem/source/hash overlap：

```text
重新划分 split，保证同题、同源代码家族、完全相同代码只出现在一个 split。
```

JPlag 排除过多：

```text
优先补 Java-Java / Python-Python，同语言、可解析、eligible 的样例。
```

MySQL credential 失败：

```text
记录为 MySQL 实库待验证；不要把 H2 fallback 冒充 MySQL 验证。
```
