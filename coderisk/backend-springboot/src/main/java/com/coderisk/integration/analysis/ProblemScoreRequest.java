package com.coderisk.integration.analysis;

import java.util.Map;

public record ProblemScoreRequest(
        AnalysisQuestion question,
        Map<String, Object> config
) {
}
