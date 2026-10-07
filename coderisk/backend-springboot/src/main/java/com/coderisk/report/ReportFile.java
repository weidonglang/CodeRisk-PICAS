package com.coderisk.report;

import java.time.OffsetDateTime;

public record ReportFile(
        long id,
        long taskId,
        String status,
        String format,
        String fileName,
        String filePath,
        String fileHash,
        OffsetDateTime createdAt
) {
}
