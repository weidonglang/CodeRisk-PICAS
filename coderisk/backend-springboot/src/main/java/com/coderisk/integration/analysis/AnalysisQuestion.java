package com.coderisk.integration.analysis;

public record AnalysisQuestion(
        long id,
        String title,
        String description,
        String inputFormat,
        String outputFormat,
        String constraintsText,
        String starterLanguage,
        String starterCode,
        String starterSource
) {
}
