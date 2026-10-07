package com.coderisk.system;

public record DashboardSummary(
        long questionCount,
        long submissionCount,
        long taskCount,
        long highRiskResultCount,
        String versionStage,
        String dataNotice
) {
}
