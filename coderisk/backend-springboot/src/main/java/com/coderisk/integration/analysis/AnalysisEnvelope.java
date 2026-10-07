package com.coderisk.integration.analysis;

public record AnalysisEnvelope<T>(
        boolean success,
        String errorCode,
        String message,
        String analysisVersion,
        String configVersion,
        T result
) {
}
