package com.coderisk.result;

public record TaskResultSummary(
        long taskId,
        int totalResults,
        long lowCount,
        long mediumCount,
        long elevatedCount,
        long highCount,
        boolean containsMockData
) {
}
