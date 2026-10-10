# Offline hybrid candidate review

**DEVELOPMENT_NOT_BENCHMARK**

Status: BLOCKED_INCOMPLETE_QUERY_POOLS
Pairs: 75; complete queries: 0; selected K: None; selected: 0.
Candidate K is selected on validation only. Recall is macro recall over positive queries in the declared finite pool, not a population guarantee.
Missing/unsupported candidates must not be dropped. Non-selected means unassessed, never independent.
Mock/dry-run have no model metrics. Real import needs a reviewed matched baseline, complete pools and authorized sources.
End-to-end review-queue metrics include every pool member, including candidate-stage misses. Located quotes do not validate reasoning.
No network calls, source execution, paid inference or production changes. Final judgment requires human review.

| Split | K | Positive queries | Recall@K | Status |
| --- | ---: | ---: | ---: | --- |
| validation | 1 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| validation | 3 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| validation | 5 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| validation | 10 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| test | 1 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| test | 3 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| test | 5 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
| test | 10 | 0 | N/A | COMPLETE_LABELED_QUERY_POOL_REQUIRED |
