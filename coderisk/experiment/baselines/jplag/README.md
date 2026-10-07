# JPlag Baseline Adapter

This directory contains the reproducible boundary for the real V4 Phase 1 JPlag baseline smoke run.

## Scope

1. `run-jplag.ps1` forwards explicit CLI arguments to a reviewed JPlag JAR.
2. `adapter.py` converts neutral JSON or JPlag native CSV into the CodeRisk baseline CSV contract.
3. `samples/java` contains three small synthetic submissions used only for the smoke run.
4. The V3 E1-E5 metrics remain unchanged; this run is a separate V4 Phase 1 baseline artifact.

## Run Boundary

Set `JPLAG_JAR` to a locally reviewed JPlag CLI JAR and pass arguments supported by that installed version:

```powershell
$env:JPLAG_JAR = "D:\tools\jplag.jar"
.\experiment\baselines\jplag\run-jplag.ps1 --help
```

JPlag CLI flags vary by release. Preserve the JAR version, SHA-256, Java version, and exact arguments in the run manifest.

## Verified V4 Phase 1 Run

JPlag `6.2.0` was selected because its official README requires Java 21. The newer `6.3.0` requires Java 25 and was not used with this machine's Java 21 runtime.

```powershell
$env:JPLAG_JAR = 'E:\ms\coderisk\data\tools\jplag\jplag-6.2.0-jar-with-dependencies.jar'
$env:JPLAG_JAVA = 'D:\DevEnvManager\envs\jdks\temurin-21\bin\java.exe'
.\experiment\baselines\jplag\run-jplag.ps1 `
  -l java -M RUN --csv-export `
  -r data\artifacts\baselines\jplag\JPLAG-6.2.0-20260621-R1\results `
  --overwrite -n -1 experiment\baselines\jplag\samples\java
```

The run parsed 3 submissions and compared 3 pairs. `submission-a/submission-b` scored `1.0`; both pairs involving the independent sample scored `0.0`. Raw and standardized outputs are under `data/artifacts/baselines/jplag/JPLAG-6.2.0-20260621-R1/`.

## Import Contract

Neutral input JSON:

```json
{
  "tool": "JPLAG",
  "toolVersion": "<installed version>",
  "comparisons": [
    {"caseId": "TEST-SIMPLE-IO-01-RENAME", "similarity": 0.91}
  ]
}
```

Run:

```powershell
python experiment\baselines\jplag\adapter.py --input jplag-neutral.json --output jplag-standard.csv
```

Native JPlag CSV:

```powershell
python experiment\baselines\jplag\adapter.py `
  --input results\results.csv --input-format jplag-csv --tool-version 6.2.0 `
  --output coderisk-standard.csv
```

Output columns are `caseId`, `method`, `methodVersion`, and `predictedScore`. The adapter consumes the official pairwise CSV export rather than reverse-engineering the `.jplag` archive.

## Research V4 manifest alignment

`experiment/research_v4_jplag.py` creates language-specific JPlag input directories, deduplicates submissions by problem and content hash, writes `alignment_manifest.csv`, and records unsupported pairs in `excluded_pairs.csv`. Native results are mapped back to Research V4 `pair_id` values before comparison with PICAS.

The verified synthetic seed run is `data/artifacts/baselines/jplag/PICAS-RESEARCH-V4-SEED-J1/`: 72 requested pairs were matched, with 19 exclusions (11 cross-language, 4 placeholders, 3 parser/unsupported-syntax cases, and 1 other non-eligible case). Java and Python executions both exited successfully under JPlag 6.2.0. These are seed workflow results, not evidence of real-data superiority.
