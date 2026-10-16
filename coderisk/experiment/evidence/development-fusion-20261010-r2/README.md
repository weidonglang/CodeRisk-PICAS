# Self-authored fusion development diagnostics

Client work date: 2026-10-10. See `manifest.json` for actual execution UTC time, Git base/dirty state and source fingerprints.

- `report.md` / `component_table.csv`: actual component scores and same-pair formula decomposition.
- `pair_diagnostics.json`: self-authored source text, raw/canonical/AST sequences, scoped bindings, fingerprint counts and production API-model results.
- `manifest.json`: 16 synthetic development probes, 7 contract checks, zero failed contracts. No fitting, public-test rescoring or core-metric eligibility.

Final generated record is this `-r2` directory. The initial sibling run is retained as historical evidence. Null contract results are observations, not successful invariance assertions. This is not a new formal benchmark, local human annotation or a proof of semantic equivalence.

Python full regression: 224 passed, one existing third-party deprecation warning. JUnit output is `E:/ms/output/intake-fusion-tests-20261010-r2.xml`. Research V4 validator still accepts 91 seed pairs with 85 workflow-eligible and no split overlaps. JPlag preparation remains 72 requested / 19 exclusions; no native tool execution in this increment.

Detailed findings and reproduction: [intake and fusion notes](../../../../coderisk_docs/proposal/INTAKE_AND_FUSION_DIAGNOSTICS.md).
