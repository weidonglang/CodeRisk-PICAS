# AI-era value experiment

**DEVELOPMENT_ONLY**

This runner never calls models; imported records are not authenticated by the tool.
Mock sessions, if present, are hand-written fixtures, not independent AI outputs.
Source history cannot be reconstructed from identical problem/code observations.

Pairs: 22; connected groups: 3; formal eligible: 0.

| Question | Method | Available / requested pairs | Mean | Median | P90 | P95 |
| --- | --- | --- | --- | --- | --- | --- |
| MOCK-count | RAW_ONLY | 6/6 | 0.1468 | 0.0976 | 0.2583 | 0.2625 |
| MOCK-count | AST_ONLY | 6/6 | 0.2059 | 0.0588 | 0.5588 | 0.7794 |
| MOCK-count | CANONICAL_ONLY | 3/6 | 0.5000 | 0.2500 | 0.8500 | 0.9250 |
| MOCK-count | NO_CANONICAL_FIXED | 6/6 | 0.1764 | 0.1022 | 0.3792 | 0.5063 |
| MOCK-count | PICAS_FIXED | 6/6 | 0.2654 | 0.1589 | 0.5529 | 0.7031 |
| MOCK-count | PICAS_RULE_DYNAMIC | 6/6 | 0.2654 | 0.1589 | 0.5529 | 0.7031 |
| MOCK-count | CANONICAL_MINUS_RAW | 3/6 | 0.2944 | 0.1500 | 0.6167 | 0.6750 |
| MOCK-maximum | RAW_ONLY | 6/6 | 0.0961 | 0.0606 | 0.2277 | 0.2701 |
| MOCK-maximum | AST_ONLY | 3/6 | 0.2012 | 0.1143 | 0.3657 | 0.3971 |
| MOCK-maximum | CANONICAL_ONLY | 1/6 | 0.1429 | 0.1429 | 0.1429 | 0.1429 |
| MOCK-maximum | NO_CANONICAL_FIXED | 3/6 | 0.1967 | 0.1177 | 0.3200 | 0.3453 |
| MOCK-maximum | PICAS_FIXED | 6/6 | 0.1023 | 0.0606 | 0.2462 | 0.2794 |
| MOCK-maximum | PICAS_RULE_DYNAMIC | 6/6 | 0.1023 | 0.0606 | 0.2462 | 0.2794 |
| MOCK-maximum | CANONICAL_MINUS_RAW | 1/6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| MOCK-sum | RAW_ONLY | 10/10 | 0.2502 | 0.0303 | 1.0000 | 1.0000 |
| MOCK-sum | AST_ONLY | 10/10 | 0.6308 | 1.0000 | 1.0000 | 1.0000 |
| MOCK-sum | CANONICAL_ONLY | 10/10 | 0.6762 | 1.0000 | 1.0000 | 1.0000 |
| MOCK-sum | NO_CANONICAL_FIXED | 10/10 | 0.4405 | 0.5152 | 1.0000 | 1.0000 |
| MOCK-sum | PICAS_FIXED | 10/10 | 0.6005 | 0.8061 | 1.0000 | 1.0000 |
| MOCK-sum | PICAS_RULE_DYNAMIC | 10/10 | 0.6005 | 0.8061 | 1.0000 | 1.0000 |
| MOCK-sum | CANONICAL_MINUS_RAW | 10/10 | 0.4260 | 0.1905 | 0.9697 | 0.9697 |

Scores above are descriptive, not FPR/F1 or proof of source relationship.
PICAS fixed and rule modes share the same score; only their operating thresholds differ.
Unknown relationship denominators remain N/A. Pair counts are not independent observations.
No orbit membership is inferred from canonical or n-gram equality.
JPlag uses current source hashes; see the baseline cohort, coverage and missing rows separately.

## Decision

INSUFFICIENT_EVIDENCE: no formal advantage or teacher-efficiency claim.
