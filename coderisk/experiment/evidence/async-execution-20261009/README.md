# Local asynchronous execution evidence, 2026-10-09

`runtime.json` is an actual isolated persistent H2 + real FastAPI run on self-authored synthetic Python code. It records 10/20/50-submission tasks, rapid start responses, progress observations, repeated start responses, final counts, and a missing-file partial/retry scenario with an unchanged successful result ID and resolved failure history. Source implementation hashes are saved; no downloaded/student source is executed.

This establishes the local execution path, not detection accuracy, independent-machine reproducibility, sustained throughput, MySQL migration or an SLA. Single-instance startup recovery, queue capacity and time-budget behavior are separately checked by backend integration tests using a stubbed AnalysisClient. A time budget prevents starting new pairs; it does not forcibly terminate already-running analysis.

Browser checks inspected final status, resolved failure history and result pagination to the second page. `results-page.png` captures the latest recovery page. Development Vite briefly logged a suspended WebSocket; no claim of zero browser console errors is made.

Use `verify_async_runtime.py` with independently started isolated local services and a fresh output file. The script temporarily moves one of its own uploaded synthetic files only within the supplied upload root and restores it. See [configuration and limits](../../../../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md).
