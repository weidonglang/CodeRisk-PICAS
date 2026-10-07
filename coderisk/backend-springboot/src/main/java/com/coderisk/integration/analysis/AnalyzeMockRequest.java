package com.coderisk.integration.analysis;

import java.util.Map;

public record AnalyzeMockRequest(
        Long taskId,
        AnalysisQuestion question,
        AnalysisSubmission submissionA,
        AnalysisSubmission submissionB,
        Map<String, Object> config
) {
}
