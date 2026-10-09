# IR-Plag intake, 2026-10-09

Pinned public-author archive and per-source metadata; **no raw source redistribution, detector scores or actual local human labels**.

- `manifest.json`: source commit, ZIP/README/license SHA-256, paper DOI, inventory, scope and restrictions.
- `source_registry.jsonl`: 467 logical Java sources / 453 distinct byte hashes, original/independent/derived provenance. Paths map to ignored local intake files, not files shipped here.
- `published_pairs.jsonl`: 355 publisher-instructed derivation pairs, 105 publisher-claimed independent-creation reference pairs. Ten independently-labelled pairs affected by the author's published dispute are quarantined. The local experiment label remains UNCERTAIN and formal eligibility remains false for all pairs.
- `quality_summary.json`: exact duplicate groups, reference-pair duplicates and previous-intake overlap audit. Do not treat repeated variants as independent statistical observations.
- `blind_batch.jsonl`: 52 deterministic, score-blind review items. No actual reviews have been supplied.
- `publisher_labels_for_adjudicator.jsonl`: labels for the adjudicator; must be withheld during independent review. Published source identifiers may still reveal upstream categories; this is not a guarantee of full blinding.
- `review_preparation.json`: local workbench/manifest paths and hashes. Raw source text is displayed safely as text by the ignored workbench, never run.

All seven tasks share a conservative global leakage block because contributors recur across tasks. No random within-dataset validation/test split or new held-out performance claim has been made. Originals are reference implementations, not common starter templates. Possible output defects and consent/license distinctions are preserved.

Reproduce from the repository root with `acquire_irplag.py`, `prepare_irplag_review.py` and `audit_irplag.py`. See [Chinese provenance and commands](../../../../coderisk_docs/proposal/NEXT_THREE_PROGRESS.md).
