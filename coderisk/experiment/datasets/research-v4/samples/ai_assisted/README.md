# AI-Assisted Samples

Use this folder for AI-assisted rewrites whose original source and generated rewrite are both traceable.

Required extra metadata:

```text
source_type=ai_assisted
case_type=AI_REWRITE
model_name
prompt_template
temperature
generation_time
manual_check_status=VERIFIED
functional_check_status=PASSED
```

An AI-assisted case evaluates whether structural similarity remains after assisted rewriting. It is not evidence that the system detects AI-generated code.

If any provenance or verification field is missing, keep the case out of core metrics or put it under `samples/placeholders/`.
