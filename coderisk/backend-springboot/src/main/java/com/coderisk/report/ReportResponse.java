package com.coderisk.report;

import java.time.OffsetDateTime;

public record ReportResponse(
        long reportId,
        long taskId,
        String status,
        String format,
        String fileName,
        String downloadUrl,
        OffsetDateTime createdAt
) {
}
