package com.coderisk.task;

import com.coderisk.common.enums.TaskStatus;
import com.coderisk.common.enums.TaskMode;
import java.time.OffsetDateTime;
import java.util.List;

public record DetectionTaskResponse(
        long id,
        long questionId,
        String taskName,
        TaskMode taskMode,
        TaskStatus status,
        int totalSubmissions,
        int totalPairs,
        int finishedPairs,
        int failedPairs,
        double progress,
        List<Long> submissionIds,
        String failureReason,
        OffsetDateTime createdAt,
        OffsetDateTime finishedAt
) {
}
