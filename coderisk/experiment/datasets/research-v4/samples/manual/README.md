# Manual Samples

Use this folder for author-created, manually collected, or manually rewritten cases with clear authorization.

Suggested structure:

```text
samples/manual/P-MANUAL-001/
  A.java
  B.java
  README.md
```

Required metadata:

```text
source_type=manual
data_origin=MANUAL
synthetic=false
license_or_authorization filled
manual_check_status=VERIFIED
functional_check_status=PASSED when applicable
```

Manual samples can enter core metrics only after validation passes and `eligible_for_core_metrics=true`.
