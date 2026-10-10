# Offline Direct LLM comparison

**DEVELOPMENT_NOT_BENCHMARK**

Mode: mock. Pairs: 75. Imported/cached records: 0. Scored LLM pairs: 0.
No network adapter, paid call, source execution or production scoring change. Mock/dry-run scores are null, never model accuracy.
COMMON_THREE is the matched-source main table; COMMON_PICAS_JPLAG is a separate matched baseline subset. AVAILABLE_DIAGNOSTIC has unequal coverage.
Test thresholds are frozen from validation only. Missing/abstained/invalid scores are N/A, not negative examples or zero.
Imported latency/token/cost are provider-declared historical metadata, not measurements of new inference by this tool; new network calls/cost are always zero.
Cache checks integrity/context but cannot attest provider execution. Repeating one historical response does not establish model stability.
Exact quoted line ranges are verified; located evidence does not establish derivation or semantic equivalence.

| Method | Scope | Test N | F1 | FPR |
| --- | --- | ---: | ---: | ---: |
| PICAS_FIXED | COMMON_THREE | 0 | N/A | N/A |
| PICAS_RULE_DYNAMIC | COMMON_THREE | 0 | N/A | N/A |
| JPLAG | COMMON_THREE | 0 | N/A | N/A |
| DIRECT_LLM | COMMON_THREE | 0 | N/A | N/A |
| PICAS_FIXED | COMMON_PICAS_JPLAG | 38 | 0.7692 | 0.6250 |
| PICAS_RULE_DYNAMIC | COMMON_PICAS_JPLAG | 38 | 0.6667 | 0.2500 |
| JPLAG | COMMON_PICAS_JPLAG | 38 | 0.7826 | 0.3750 |
| PICAS_FIXED | AVAILABLE_DIAGNOSTIC | 40 | 0.7857 | 0.6250 |
| PICAS_RULE_DYNAMIC | AVAILABLE_DIAGNOSTIC | 40 | 0.6667 | 0.2500 |
| JPLAG | AVAILABLE_DIAGNOSTIC | 38 | 0.7826 | 0.3750 |
| DIRECT_LLM | AVAILABLE_DIAGNOSTIC | 0 | N/A | N/A |
