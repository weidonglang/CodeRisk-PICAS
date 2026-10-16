# Non-Java public intake evidence

Client work date: 2026-10-10. These are metadata-only snapshots from actual pinned downloads and offline reconstruction. No downloaded source code is copied into this evidence directory.

- PoolC: 598,736 rows in the first train shard scanned; 30,000 balanced public-label Python pairs retained; 29,280 unique source texts. 1,319 fail Python 3 syntax parsing. License metadata is empty; this local pool is quarantined and excluded from formal metrics.
- XLCoST mirror: 57,661 seven-language tokenized program records; 30,893 unlabelled exact-title candidates, 20,713 without Java. These are not raw source or officially map-verified parallel pairs.
- `collection_summary.json` separates raw Python and tokenized program records, published labels and unlabelled candidates. It does not assert problem/source-family isolation or globally independent examples.
- `verification.json` records independently reconstructed counts, file/pin/verifier hashes, Python version and JUnit identity. Full regression: 263 tests, zero failures/errors/skips, one preexisting third-party warning. No production scoring, language-support expansion, Maven/frontend/JPlag/MySQL verification was performed in this increment.
- `poolc/` and `xlcost/` preserve the exact intake manifests and audit summaries. Their source files and pair indices remain in Git-ignored `data/public-datasets/`.

From `E:\ms`, reproduce verification without downloads:

```powershell
$PY = '.\.tmp\language-venv\Scripts\python.exe'
& $PY coderisk\experiment\acquire_nonjava_datasets.py poolc --verify-only
& $PY coderisk\experiment\acquire_nonjava_datasets.py xlcost --verify-only
# After a fresh successful full pytest run, write metadata-only evidence to a new directory:
& $PY coderisk\experiment\record_nonjava_intake_evidence.py --junit output\nonjava-all-tests-20261010-r2.xml --output output\nonjava-evidence-replay
```

Full provenance, language counts, quality limitations, license observations and intake/replay commands: [data card](../../../../coderisk_docs/proposal/NONJAVA_PUBLIC_INTAKE.md).
