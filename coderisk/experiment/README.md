# PICAS Reproducible Experiments

## C/HTML and additional official sources (2026-10-08)

`acquire_multilang_dataset.py` imports a bounded, hash-pinned CodeNet prefix and commit-pinned MDN HTML files. `audit_multilang_sources.py` checks source integrity and parser/normalization coverage only. See [commands and limitations](../../coderisk_docs/proposal/MULTILANGUAGE_PROGRESS.md) and [frozen evidence](evidence/multilang-20261008/README.md). Upstream C language labels need review; no pair labels are inferred. The formal fair-evaluation runner and JPlag common cohort remain Java/Python; C/HTML protocol/baseline expansion is pending.

## Public real-data intake (2026-10-08)

`acquire_public_datasets.py` imports pinned official archives for AD2022 (1,526 real Java/Python coursework solutions) and ConPlag v3 (911 published labelled Java pairs). The importer preserves original files, published labels, licenses, byte/text hashes and upstream split membership. It creates a separate intake, not a formal Research V4 manifest. No detector scores are calculated and no annotations are invented.

See [Chinese intake report](../../coderisk_docs/proposal/PUBLIC_DATA_INTAKE.md), [source registry](public_dataset_sources.json) and [audit evidence](evidence/public-intake-20261008/README.md). Downloaded content stays under ignored `data/tools/public-datasets/` and `data/public-datasets/`; the repository includes the reproducible importer and audit metadata.

```powershell
# From the repository root; use a new output directory.
python coderisk/experiment/acquire_public_datasets.py --output coderisk/data/public-datasets/public-intake-new
python coderisk/experiment/acquire_public_datasets.py --verify-only --output coderisk/data/public-datasets/public-intake-new
```

This directory contains the reproducible V3 readiness experiment. It uses the real analysis pipeline and a 36-case synthetic dataset; it does not contain or claim to represent real student submissions.

## Research V4 handbooks

Use these files before adding data or writing paper claims:

```text
datasets/research-v4/DATA_COLLECTION_GUIDE.md
RUN_RESEARCH_V4.md
RESULT_INTERPRETATION_GUIDE.md
PAPER_MATERIALS_GUIDE.md
RESEARCH_V4_CHECKLIST.md
```

They explain where to put manual, verified AI-assisted, external, synthetic, and placeholder samples; how to run validation/calibration/JPlag/full experiments; how to read failure and borderline outputs; and how to keep synthetic seed results out of formal benchmark claims.

## Run

From the repository root:

```powershell
python experiment\run_minimal_v3.py `
  --config configs\experiments\minimal_v3.json `
  --run-id PICAS-V4-READY-20260620-R2
```

The runner emits a manifest, predictions, E1-E5 CSV files, failure and borderline cases, summary JSON, and a Markdown report under `data/artifacts/experiments/<run-id>/`. Every manifest records formula, algorithm and dataset versions, random seed, runtime metadata, and a Git commit or local source fingerprint.

The dataset covers `simple_io`, `array_loop`, `sort_template`, `dfs_graph`, and `dp_variant`. Validation and test problem IDs are disjoint, and the runner rejects problem/source leakage. Validation selects only the fixed-threshold baseline; the production dynamic formula is not tuned on test data.

## Scope

- E1: fixed thresholds versus PICAS dynamic thresholds
- E2: raw token versus canonical token similarity
- E3: token-only versus token+AST versus PICAS_STANDARD
- E4: PICAS-NoDT, PICAS-NoCanon, and PICAS-Full
- E5: false positive, false negative, borderline, and parser-fallback cases

The dataset is deliberately small. Results demonstrate that the pipeline is reproducible and expose current failure modes; they are not statistically significant benchmark claims.

The JPlag adapter contract is documented in `baselines/jplag/`. In addition to the 3-pair Phase 1 smoke artifact, `research_v4_jplag.py` prepares manifest-aligned inputs and maps native JPlag results back to `pair_id`. The current synthetic seed run aligns 72 pairs and records 19 exclusions with reasons.

## Research V4 aggregate

`datasets/research-v4/dataset.json` aggregates versioned seed shards and an initially empty manual supplement. The current 91-pair aggregate is entirely synthetic; four `AI_REWRITE` rows are explicit placeholders excluded from core metrics. It exists to exercise the workflow, not to support benchmark claims.

```powershell
python experiment\validate_research_v4_dataset.py --output-dir data\artifacts\experiments\SEED-VALIDATION
python experiment\research_v4_jplag.py --manifest experiment\datasets\research-v4\dataset.json --output-dir data\artifacts\baselines\jplag\<run-id>
python experiment\run_research_v4.py --config configs\experiments\research_v4.json --run-id <immutable-run-id>
```

The validator rejects problem/source/exact-code split leakage, unsafe paths, invalid enums, declared-hash mismatches, and unverified AI-assisted cases. The unified runner emits E1-E5, validation-only calibration, the Java/Python experimental matrix, aligned-baseline tables, failure/borderline analysis, and paper-ready CSV/JSON/Markdown in one immutable run directory. Test labels are never used for parameter selection.

If `python` is blocked by a WindowsApps alias, use:

```powershell
$PY = ".\analysis-service-python\.venv\Scripts\python.exe"
& $PY experiment\validate_research_v4_dataset.py --output-dir data\artifacts\experiments\SEED-VALIDATION
```
# 2026-10-09：数据复核与公开标签探索入口

数据质量登记使用 `review_public_data.py`，盲审材料与双人导出合并使用 `prepare_annotation_workbench.py`，保守划分提案使用 `propose_public_splits.py`。本机首批 HTML 位于忽略目录 `data/public-datasets/review-workbench-20261009-v2/review.html`，标签仍待人工复核；说明见 [复核文档](../../coderisk_docs/proposal/DATA_REVIEW_WORKBENCH.md)。

`run_published_conplag.py --prepare` 先冻结外部单人公开标签方案，再用 `--registration` 运行探索评测。`archive_conplag_pilot.py` 从保存的逐对分数复核统计、归档不含原始源码的证据并绘图。实际 911 对 Java 结果见 [探索报告](../../coderisk_docs/proposal/CONPLAG_PILOT_RESULTS.md)。这些工具独立于正式 `run_fair_evaluation.py` 的资格门禁，不能用于绕过双人标签、功能/来源核验及研究冻结要求。
