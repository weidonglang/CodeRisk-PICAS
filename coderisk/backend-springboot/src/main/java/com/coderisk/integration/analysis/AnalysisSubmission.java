package com.coderisk.integration.analysis;

public record AnalysisSubmission(
        long id,
        String language,
        String fileName,
        String rawCodePath,
        String code
) {
}
