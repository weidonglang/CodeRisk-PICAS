# Synthetic development fusion diagnostics

Self-authored probes after observing ConPlag. No held-out accuracy, fitting, or benchmark claim.

Full - no-canonical = .45*(C-.5*(R+A)) + .15*(M-.5*(R+A)); fallback uses raw on both sides.

| Pair | Raw | AST | Canonical | Mapping | Full | No-canonical | Delta | Contract |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DEV-PY-IDENTICAL | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | True |
| DEV-PY-RENAME | 0.030303 | 1.000000 | 1.000000 | 1.000000 | 0.806061 | 0.515151 | 0.290910 | True |
| DEV-PY-FORMAT | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | True |
| DEV-PY-UNUSED-LOCAL | 0.681818 | 0.909091 | 0.275862 | 0.800000 | 0.562320 | 0.795454 | -0.233134 | None |
| DEV-PY-UNUSED-FUNCTION | 0.708333 | 0.833333 | 0.051282 | 0.200000 | 0.361410 | 0.770833 | -0.409423 | None |
| DEV-PY-REORDER | 0.500000 | 0.809524 | 0.500000 | 1.000000 | 0.636905 | 0.654762 | -0.017857 | None |
| DEV-PY-COMMON | 0.700000 | 0.695652 | 0.700000 | 1.000000 | 0.744130 | 0.697826 | 0.046304 | None |
| DEV-PY-EXTERNAL-NAMES | 0.454545 | 1.000000 | 0.454545 | 1.000000 | 0.645455 | 0.727272 | -0.081817 | None |
| DEV-PY-SCOPE-FALLBACK | 0.230769 | 0.133333 | 0.000000 | 0.000000 | 0.230769 | 0.230769 | 0.000000 | True |
| DEV-PY-PARSE-FALLBACK | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | True |
| DEV-JAVA-RENAME | 0.172414 | 1.000000 | 1.000000 | 1.000000 | 0.834483 | 0.586207 | 0.248276 | True |
| DEV-JAVA-UNUSED-LOCAL | 0.825000 | 0.727273 | 0.431373 | 0.833333 | 0.629572 | 0.776137 | -0.146564 | None |
| DEV-JAVA-UNUSED-FUNCTION | 0.772727 | 0.750000 | 0.218750 | 0.333333 | 0.452983 | 0.761364 | -0.308381 | None |
| DEV-JAVA-REORDER | 0.764706 | 1.000000 | 0.621622 | 1.000000 | 0.782671 | 0.882353 | -0.099682 | None |
| DEV-JAVA-COMMON | 0.837838 | 1.000000 | 0.837838 | 1.000000 | 0.894595 | 0.918919 | -0.024324 | None |
| DEV-JAVA-PARSE-FALLBACK | 0.297297 | 0.000000 | 0.000000 | 0.000000 | 0.297297 | 0.297297 | 0.000000 | True |

Null contract means descriptive observation, not a passed invariance test.
All production thresholds/weights are unchanged. Sources are inspected as text, never executed.
