# Stage 3 independent-solution calibration evidence

Actual offline execution on 2026-10-10, Windows, Python 3.12.14. DEVELOPMENT / SYNTHETIC SEED ONLY, not a benchmark. No production formula, canonicalizer, API, frontend, database, or V4 production weight changed.

## Inputs and results

- Frozen experiment config: `configs/experiments/natural_calibration_v1.json`, default VALIDATION_PROBLEMS_ONLY.
- Research V4 seed: 91 synthetic input pairs, 75 same-language Java/Python analyzed (35 validation, 40 test), 16 excluded. Formal eligible: 0.
- Empty PENDING reference manifest: 0 trusted disjoint reference pairs, 0 queries with q, alpha=null. No manual/external/HUMAN references were fabricated.
- All 75 statistical policy predictions use RULE_FALLBACK. CALIBRATABLE_ONLY has N=0 / N/A. Statistical benefit is NOT measured by this run.
- Test: 24 positives / 16 negatives, 7 NaturalSimilar. Validation-selected fixed threshold 0.3; unchanged rule threshold. Fixed F1/FPR/Recall: 0.7857/0.6250/0.9167. Rule and statistical-fallback: 0.6667/0.2500/0.5833. Rule recall loss remains visible.
- This table includes production fallback cases and is NOT the prior stage's COMMON test N=36. No historical ConPlag/JPlag score merge or inspected-test retuning.
- Seven parser/normalization fallback rows; 40 failure rows across all three method policies (same case can recur by method); nine rule/q borderline rows. These are diagnostic counts, not 40 unique failures or real-student decisions.

`run_manifest.json` records input/config/source hashes, versions, Git HEAD at execution, dirty working-tree state, seed, actual duration and claim limits. It was generated before the stage commit; the exact current runner hash is recorded and must not be inferred from Git HEAD alone. `configSha256` refers to the versioned input JSON bytes, not the pretty-printed `config.json` copy. `reference_audit.csv` is empty because there are zero references, not because an audit was skipped.

`queries.csv` contains score components, availability, template guards, q and fallback reasons. `predictions.csv` distinguishes INDEPENDENT_TAIL from RULE_FALLBACK. `metrics.csv` includes split and matched-support scope; filter `split=test` and `scope=ALL_TEST_POLICY` for the primary table. `failures.csv`, `borderline.csv`, `parser_fallbacks.csv`, `excluded.csv`, JSON selections/results and `REPORT.md` support interpretation. `mathematical_contracts.json` is a scalar algebra fixture, NOT code evaluation.

## Tests and red-to-green evidence

- Initial missing-new-module collection failure was expected scaffolding, NOT a production algorithm failure.
- `gates-red.xml`: 33 pass / 4 fail. Three implementation gaps: malformed registration handling, extra query identities leaking between validation/test, and cross-split reference panel author reuse. One failed file fixture exposed Windows newline/hash setup; the fixture was corrected to explicit byte writes.
- `hash-red.xml`: 2 fail / 37 deselected, reproduced the reference/query hash namespace and CRLF leakage gap before fixing it.
- `identity-red.xml`: 1 fail / 39 deselected, reproduced identity whitespace hiding author reuse; identity comparisons now strip surrounding whitespace.
- `reviewer-red.xml`: 1 fail / 39 deselected, reproduced the same reviewer ID with whitespace passing the two-reviewer gate; reviewer ID comparisons now strip surrounding whitespace too. These remain test-only declarations, not identity verification of actual people.
- `focused-green.xml`: 40 pass. Tests include empirical/smoothed upper tails, score/order-independent greedy matching, validation-only alpha, reference file/path/hash/authorship/authorization/review/freeze gates, template score invariance, parse fallback, split/panel identity isolation and actual seed integration.
- `full-green.xml`: 377 pass, one existing Starlette/httpx warning, full current working tree. Other uncommitted tasks are included, so this is not a clean-commit total.
- `isolated-green.xml`: 40 pass on a Git archive of HEAD plus only this stage's final source patch (tree `7b8c27a8d68e55dfdea3cb62b3a6f1c4ddb33928`, before final documentation/evidence updates). `isolated-metrics.csv` and `metrics.csv` are byte-identical, SHA-256 `9da7399cf99f87d973ff191cbce23b2e1691dd7c49476cfe150195d4af049ce4`. `isolated-run_manifest.json` records that snapshot's actual source hashes; its Git HEAD alone does not identify the temporary tree.
- The default formal-run integration test actually rejects the seed before creating output; development mode does not waive reference quality or leakage checks.
- Test-only mock HUMAN declarations are explicitly marked MOCK_TEST_ONLY and live in temporary fixtures, not the real dataset.

The unchanged production SHA-256 values match stages 1/2:

```text
FORMULA_SPEC.md   562fdb7d68757b811147f9e8d6587e52f8aad01647d002b858329e9ddedf7c20
canonicalization  1fd1cdc8d0253b65f03a3dd27db6969053e3ea3561dbb5943701beff54877008
token_similarity ab2c5866e2b617ed6536827409180af7fe3629994518922d7623ce13fcd7f65e
```

Backend/frontend/MySQL/browser/JPlag were NOT rerun in this stage (no affected runtime edit); earlier H2 19 tests/build results are historical only. MySQL still awaits valid credentials. No source execution, external upload or paid LLM call.

## Reproduction

PowerShell from the Git root, using the actual working local environment (the old project .venv is unavailable):

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/natural_similarity_calibration.py --help
& $Python coderisk/experiment/natural_similarity_calibration.py --output output/natural-calibration-new-run --allow-development
$env:TEMP = 'E:\ms\.tmp\intake-fusion-temp-20261010'
$env:TMP = $env:TEMP
& $Python -m pytest -q -p no:cacheprovider --basetemp .tmp/natural-calibration-new-tests --junitxml output/natural-calibration-new-tests.xml coderisk/analysis-service-python/tests/test_natural_similarity_calibration.py
```

Output and test directories must be new. For a new machine, provision a supported Python/dependencies per README and replace the executable path. Formal runs require real reviewed/authorized reference and query records plus config-matching preregistration. New-problem testing cannot use same-problem reference data while claiming reference/test problem-disjointness; choose and freeze the protocol honestly.

Full design and next-data requirements: [NATURAL_SIMILARITY_CALIBRATION.md](../../../../coderisk_docs/research/NATURAL_SIMILARITY_CALIBRATION.md).
