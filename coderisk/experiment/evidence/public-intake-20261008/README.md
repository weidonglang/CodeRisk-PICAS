# Public dataset intake evidence — 2026-10-08

These are acquisition and data-integrity artifacts, not model evaluation results. The active local intake is `E:/ms/coderisk/data/public-datasets/public-intake-20261008/`; downloaded code is excluded from Git and can be reconstructed using `experiment/acquire_public_datasets.py`.

| File | Meaning |
| --- | --- |
| `source_registry.json` | Official URLs, authors, licenses, pinned archive sizes/checksums |
| `zenodo-record.json` | Retrieved official ConPlag v3 API metadata, including license and published MD5 |
| `intake_summary.json` | Actual parsed counts, upstream overlap details, pending eligibility |
| `file_inventory.json` | SHA256 and byte sizes of 5,193 imported data/provenance files; paths relative to the local intake |
| `raw_submission_variants.json` | Ten ConPlag submission IDs with different raw file contents |
| `split_proposal.json` | Unregistered, review-required ConPlag group split proposal |
| `proposal_audit.json` | Proposed-split overlap checks and original published-label counts |
| `intake_tests.txt` | Actual standard-library regression test output |
| `verification_record.json` | Actual intake integrity/reconstruction checks and source fingerprints |
| `evidence_hashes.json` | Hashes of these evidence files, excluding this hash catalogue itself |

AD2022 attribution: Fynn Petersen-Frey, Marcus Soll, Louis Kobras, Melf Johannsen, Peter Kling, Chris Biemann; University of Hamburg; [official source](https://www.inf.uni-hamburg.de/en/inst/ab/lt/resources/data/ad-lrec), [LREC 2022 publication](https://aclanthology.org/2022.lrec-1.101/). The dataset has CC BY-NC 4.0 terms, independent of the repository code license. Original license/README and CSV files are preserved in the local intake.

ConPlag attribution: Evgeniy Slobodkin and Alexander Sadovnikov; Sirius.Courses; [Zenodo v3, DOI 10.5281/zenodo.7332790](https://zenodo.org/records/7332790), [2023 publication](https://arxiv.org/abs/2303.10763). Zenodo API metadata declares CC BY 4.0. Imported source bytes are preserved in pair-specific directories. Raw and template-free files are views of the same 911 pairs.

The intake preserves the original published verdicts. It neither asserts local double review nor supplies invented problem profiles. Current project core-metric eligibility is zero; a separate external-label protocol or completed course annotations must be established before the appropriate formal run. No downloaded code was executed and no detector scores were computed.

Reconstruction uses UTF-8 JSONL indices. Code extraction from the AD2022 CSV preserves the field contents, including embedded line endings; the original CSV bytes are also retained. ConPlag code files retain archive bytes exactly. The file inventory records byte hashes, while pair indices also contain universal-newline UTF-8 hashes matching the existing experiment loader.

The proposed ConPlag split has 284 validation pairs (87 published positive, 197 negative), 627 test pairs (164 positive, 463 negative), and 21 connected groups. Problem, submission-family, raw text-hash and template-free text-hash overlaps are all zero in the audit. This is a proposal, not evidence of preregistration or a final independent test set.

See [Chinese report](../../../../coderisk_docs/proposal/PUBLIC_DATA_INTAKE.md) for scope, source limitations and reconstruction commands. Earlier failed import directories are not part of this evidence bundle.
