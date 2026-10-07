package com.coderisk.report;

public record ReportCreateRequest(
        String format,
        boolean includeLowRiskPairs,
        boolean includeCodeSnippets,
        boolean includeThresholdExplanation
) {
}
