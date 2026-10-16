# Frozen similarity ablation

**DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK**

Existing same-language Java/Python features only. No production weighting or thresholds changed.

| Method | Common test N | Precision | Recall | F1 | FPR | Natural FPR | PR area (AP score) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RAW_ONLY | 36 | 0.5833 | 1.0000 | 0.7368 | 1.0000 | 1.0000 | 0.6134 |
| AST_ONLY | 36 | 0.8000 | 0.9524 | 0.8696 | 0.3333 | 0.7143 | 0.8736 |
| CANONICAL_ONLY | 36 | 0.9444 | 0.8095 | 0.8718 | 0.0667 | 0.1429 | 0.8996 |
| MAPPING_ONLY | 36 | 0.5833 | 1.0000 | 0.7368 | 1.0000 | 1.0000 | 0.6679 |
| RAW_AST_EQUAL | 36 | 0.7692 | 0.9524 | 0.8511 | 0.4000 | 0.8571 | 0.7020 |
| RAW_CANONICAL_EQUAL | 36 | 0.6897 | 0.9524 | 0.8000 | 0.6000 | 1.0000 | 0.6959 |
| RAW_MAPPING_EQUAL | 36 | 0.6774 | 1.0000 | 0.8077 | 0.6667 | 1.0000 | 0.6296 |
| AST_CANONICAL_EQUAL | 36 | 0.9444 | 0.8095 | 0.8718 | 0.0667 | 0.1429 | 0.9054 |
| AST_MAPPING_EQUAL | 36 | 0.7143 | 0.9524 | 0.8163 | 0.5333 | 1.0000 | 0.8614 |
| CANONICAL_MAPPING_EQUAL | 36 | 0.9444 | 0.8095 | 0.8718 | 0.0667 | 0.1429 | 0.8905 |
| ALL_EQUAL | 36 | 0.7143 | 0.9524 | 0.8163 | 0.5333 | 1.0000 | 0.7328 |
| PICAS_FIXED | 36 | 0.6667 | 0.9524 | 0.7843 | 0.6667 | 1.0000 | 0.7454 |
| PICAS_RULE_DYNAMIC | 36 | 0.7647 | 0.6190 | 0.6842 | 0.2667 | 0.5714 | 0.7454 |
| PICAS_DYNAMIC_OFFSET | 36 | 0.8182 | 0.8571 | 0.8372 | 0.2667 | 0.5714 | 0.7454 |

COMMON is the primary matched-support table; AVAILABLE is diagnostic only and must not be compared as equal coverage.
PR area is non-interpolated AP with tied scores grouped; it is not trapezoidal PR integration. Single-class/unknown labels are N/A.
LOW_FPR uses only validation to choose a feasible operating point. Report achieved test FPR, not a guaranteed population FPR.
Recall@K needs a declared complete labeled query pool; arbitrary sampled pairs cannot support retrieval recall.
Rename probes compare identical self pairs with legal renamed variants. They test score sensitivity, not accuracy or semantic equivalence.
Analysis time includes shared feature extraction and availability checks. Aggregation time excludes shared extraction; not a per-algorithm benchmark.
This run does not rescore ConPlag, retune its inspected test set, or merge historical JPlag outputs with new algorithm scores.
The historical Full-not-highest-F1 observation remains unchanged. Statistical independent-solution calibration and LLM baselines are not implemented here.
