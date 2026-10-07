package com.coderisk.integration.analysis;

import java.util.Map;

public record ProblemScoreResult(
        long questionId,
        Map<String, Object> problemProfile,
        Map<String, Object> thresholdAdjustment
) {
}
