# CodeRisk / PICAS

CodeRisk is a problem-aware code similarity risk detection system for programming assignments. It outputs risk levels, dynamic thresholds, similarity metrics, evidence, and review suggestions. It must not directly conclude plagiarism.

## Current Scope

This repository provides a demonstrable V2 delivery loop, a reproducible V3 experiment loop, and an explicitly isolated Research V4 candidate scaffold:

- Spring Boot backend with unified `ApiResponse<T>`, JDBC persistence, Flyway migrations, question/submission/task/result APIs, evidence storage, and HTML report export.
- FastAPI analysis service with scope-aware Python/Java identifier normalization, canonical token similarity, identifier mapping evidence, rule-based problem profiles, and bounded dynamic thresholds.
- Problem profiles expose `DifficultyScore`, `SolutionSpaceScore`, `TemplateRiskScore`, and `NaturalSimilarityRisk`; production risk output follows `FORMULA_SPEC.md` and includes `riskMargin` plus calibrated display score.
- Vue 3 frontend with question creation, upload, task execution, risk result/evidence detail, report download, and a lightweight page backed by real experiment artifacts.
- Shared local folders for uploads, artifacts, experiments, and reports.
- A Research V4 synthetic seed manifest over 91 pairs: 80 same-language cases and 11 Java/Python experimental cases. Validation/test problem, source, and exact-code overlap are all rejected by the validator.
- Experimental Java/Python normalized IR plus lightweight control/data-flow summaries under `PICAS_CROSSLANG`; all three metrics have weight 0 and are excluded from `PICAS_STANDARD`.
- A manifest-aligned JPlag 6.2.0 seed run over 72 eligible same-language pairs, validation-only threshold calibration, unified CSV/JSON/Markdown paper tables, and explicit real-data coverage gaps.

Mock analysis is explicitly marked as mock data and must not be used as experiment evidence. The experiments are reproducibility smoke tests, not formal benchmarks. Complete CFG/DFG/PDG, advanced AST subtree matching, semantic equivalence, and AI rewrite enhancement are not claimed by this version.

## Repository Layout

```text
backend-springboot/        Spring Boot business service
analysis-service-python/   FastAPI analysis service
frontend-vue/              Vue 3 frontend
data/                      uploads, cleaned code, artifacts
database/                  database migrations and seed data
deploy/                    Docker Compose files
experiment/                datasets, configs, runs, reports, plots
tests/golden_cases/        early algorithm regression cases
demo_dataset/              demo data for presentation
```

## Local Run

Use Java 21 for the backend. Set `JAVA_HOME` to your installed JDK 21 directory when it is not already configured:

```powershell
$env:JAVA_HOME = "C:\path\to\jdk-21"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

For a local demo, the backend uses a persistent H2 database in MySQL compatibility mode. To run against MySQL 8, initialize the database and select the MySQL profile:

```powershell
Get-Content database\init_mysql.sql -Raw | `
  & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
$env:SPRING_PROFILES_ACTIVE = "mysql"
.\scripts\start-backend-dev.ps1
```

Run the backend:

```powershell
.\scripts\start-backend-dev.ps1
```

Run the analysis service:

```powershell
.\scripts\start-analysis-dev.ps1
```

Run the frontend:

```powershell
.\scripts\start-frontend-dev.ps1
```

Frontend URL: `http://127.0.0.1:5173`

Service URLs:

```text
Frontend: http://127.0.0.1:5173
Backend:  http://127.0.0.1:8080
Analysis: http://127.0.0.1:8001
```

The current development build does not require a login account.

## Demo Flow

1. Create a question from `/questions/create`.
2. Upload at least two Java or Python files.
3. Create and start a `PICAS_STANDARD` task.
4. Inspect the sorted result list, problem profile, dynamic threshold, evidence, code comparison, and identifier mappings.
5. Export the HTML risk report.
6. Open `/experiments` to inspect the latest real E1-E5 artifact summary.

Screenshot checklist: question form, upload list, finished task, result list, problem profile and threshold explanation, evidence/code comparison, report download confirmation, and experiment page. Capture desktop and 390px views without presenting mock data as experiment evidence.

## Minimal V3 Experiment

The committed dataset is synthetic and contains no real student submissions:

```powershell
python experiment\run_minimal_v3.py `
  --config configs\experiments\minimal_v3.json `
  --run-id PICAS-V4-READY-20260620-R2
```

Results are written to `data/artifacts/experiments/<run-id>/`. The latest run can also be inspected through `GET /api/experiments/latest` or the `/experiments` page.

The V3 runner evaluates only the `test` split. The `validation` split selects the fixed-threshold baseline; it does not modify the production dynamic-threshold formula. The JPlag 6.2.0 smoke artifact is stored separately under `data/artifacts/baselines/jplag/` and is not mixed into E1-E5.

## Research V4

If the Windows `python` alias is blocked, use the analysis-service virtualenv interpreter:

```powershell
$PY = ".\analysis-service-python\.venv\Scripts\python.exe"
```

```powershell
python experiment\run_v4_phase1_crosslang.py --run-id PICAS-V4-PHASE1-XL-20260621-R1
python experiment\run_v4_phase2_crosslang.py --run-id PICAS-V4-PHASE2-XL-20260623-R2
python experiment\validate_research_v4_dataset.py --output-dir data\artifacts\experiments\SEED-VALIDATION
python experiment\run_research_v4.py --config configs\experiments\research_v4.json --run-id PICAS-RESEARCH-V4-SEED-20260624-R2
```

Phase 2 compares raw token, language-specific AST, canonical token, normalized IR, lightweight control summary, and lightweight data-flow summary. Its fixed composite is experiment-only and does not alter production scoring. See `coderisk_docs/IR_SPEC.md` and the generated failure-case files.

The Research V4 manifest is under `experiment/datasets/research-v4/`. The aggregate contains 91 synthetic seed pairs; 4 AI rewrite records are explicit `placeholder` rows and are excluded from core metrics. The seed reaches the workflow-size target but remains a reproducible pre-experiment scaffold, not a formal benchmark. The validator reports remaining real-data requirements: 20 manual, 8 verified AI-assisted, and 8 external pairs. AI-assisted cases are eligible only when model/prompt provenance, manual review, and functional checks are recorded.

The 7 legacy cross-language cases received split metadata during Phase 3 after Phase 2 inspection. No threshold or weight was tuned from that split, but its metrics are exploratory rather than confirmatory test estimates. Newly supplied manual cases must declare `split_preregistered=true` before analysis.

To add a traceable case, place both code files below `experiment/datasets/research-v4/samples/`, preview its metadata with `experiment/add_research_v4_case.py`, fill every reported confirmation field, then append it to `pairs/manual_pairs.json`. Re-run the validator before JPlag preparation or the unified runner. See the dataset `DATA_CARD.md` for the exact contract.

Research V4 workflow guides:

- `experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md`: what data to collect, where to place it, how to avoid leakage, and what to prioritize next.
- `experiment/RUN_RESEARCH_V4.md`: copyable PowerShell commands from data validation to calibration, JPlag alignment, full runner output, and report updates.
- `experiment/RESULT_INTERPRETATION_GUIDE.md`: how to read FPR/Recall/F1, raw vs canonical, ablations, JPlag comparison, common-structure false positives, and unsupported-syntax false negatives.
- `experiment/PAPER_MATERIALS_GUIDE.md`: which CSV/Markdown artifacts can support paper tables, limitations, threats to validity, and future-work writing.
- `experiment/RESEARCH_V4_CHECKLIST.md`: pre-data, post-data, pre-run, post-run, paper, defense, and software-copyright checks.

## Database Profiles

- `local`: persistent H2 file database in MySQL compatibility mode. Override with `CODERISK_LOCAL_DB_URL`.
- `mysql`: MySQL 8 using `CODERISK_DB_URL`, `CODERISK_DB_USERNAME`, and `CODERISK_DB_PASSWORD`.

On the current verified machine, MySQL 8.0 is running but the available `root` and example `coderisk` credentials are rejected. The H2 fallback, Flyway V1/V2 migrations, service restart persistence, and report downloads are verified. MySQL live E2E remains an explicit credential-dependent verification item.

Common checks are documented in `database/README.md`.

## Verification

From workspace root:

```powershell
.\scripts\run-all-tests.ps1
```

Or run each layer separately:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest
```

Backend and frontend checks:

```powershell
cd backend-springboot
mvn test

cd ..\analysis-service-python
.\.venv\Scripts\python -m pytest

cd ..\frontend-vue
npm run build
```

## Development Rules

- Use `ApiResponse<T>` for backend external APIs.
- Use `AnalysisEnvelope<T>` for internal analysis service APIs.
- Keep Java and Python as `STABLE`; C remains `EXPERIMENTAL`.
- Do not execute uploaded code.
- Do not write mock data as real experiment results.
- Do not show "plagiarism confirmed" style conclusions in UI, API, reports, or docs.
