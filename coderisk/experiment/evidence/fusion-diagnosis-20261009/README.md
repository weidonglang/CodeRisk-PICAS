# Frozen-score fusion diagnosis, 2026-10-09

This reuses 911 already-observed ConPlag pilot rows per source view and their validation-selected thresholds. It performs no new source scoring, fitting or formal evaluation.

`pair_decomposition.jsonl` records the exact score change versus the no-canonical baseline and the canonical/mapping terms. `component_summary.csv` separates views, splits and publisher labels; `frozen_decision_summary.csv` reproduces original threshold decisions. `changed_decision_cases.jsonl` contains all changed observed test decisions, not hand-picked success cases. `component_contributions.png` is generated from the component table. `manifest.json` pins every input and output and declares interpretive limits.

The 627-row PICAS cohort in each view differs from the 625-row template-free common JPlag cohort. Method thresholds differ; changes in predictions are not isolated causal effects. Published labels are not local independent double review. The observed test is diagnostic data, not a fresh holdout.

Reproduce from the root: `python coderisk/experiment/diagnose_fusion.py --output output/fusion-diagnosis`. See [interpretation](../../../../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md).
