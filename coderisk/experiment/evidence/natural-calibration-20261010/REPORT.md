# Independent-solution statistical calibration

**DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK**

q is an upper-tail frequency among reviewed independent solutions, NOT a plagiarism probability.
Scores and rule thresholds are read from PICAS_STANDARD unchanged; V4 production weights remain zero.
Reference protocol: VALIDATION_PROBLEMS_ONLY. Trusted disjoint pairs: 0. Queries with q: 0.

| Method | Test N | Precision | Recall | F1 | FPR | Natural FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FIXED | 40 | 0.6875 | 0.9167 | 0.7857 | 0.6250 | 1.0000 |
| RULE_DYNAMIC | 40 | 0.7778 | 0.5833 | 0.6667 | 0.2500 | 0.5714 |
| STATISTICAL_WITH_RULE_FALLBACK | 40 | 0.7778 | 0.5833 | 0.6667 | 0.2500 | 0.5714 |

ALL_TEST_POLICY is the primary same-query policy comparison (also exports validation diagnostics). CALIBRATABLE_ONLY is supplementary matched support.
Statistical decisions use q_smoothed <= alpha; all unavailable q or unavailable validation alpha use RULE_FALLBACK, not fixed fallback.
If all queries fall back, the statistical policy is exactly the rule policy: this is NOT evidence of statistical calibration benefit.
Default problem-disjoint testing is new-problem cold start. PREREGISTERED_CONTEXT_PANEL permits same-problem reference context and must NOT be called reference/test problem-disjoint.
Greedy author/source/family/hash-disjoint matching limits code-pair reuse, but does not prove IID/exchangeability or remove cohort bias.
The +1 smoothed tail is a conservative empirical estimate, not a guaranteed calibrated p-value, confidence interval, or semantic equivalence test.
Missing authors, relation reviews, authorization, template declaration, sufficient reference size, supported parsing, or effective length cause explicit unavailability.
Short/template-dominated solutions are declined; the scaffold does NOT demonstrate reduced false positives in those settings.
No test tuning, student code execution, external upload, LLM calls, or merged historical JPlag results. Synthetic seed runs support only workflow checks.
