package com.coderisk.task;

import com.coderisk.common.enums.TaskStatus;
import com.coderisk.common.enums.TaskMode;
import java.time.OffsetDateTime;

public record TaskSummary(
        long id,
        String taskName,
        TaskMode taskMode,
        TaskStatus status,
        int finishedPairs,
        int failedPairs,
        int totalPairs,
        OffsetDateTime createdAt
) {

    public static TaskSummary from(DetectionTaskResponse task) {
        return new TaskSummary(
                task.id(),
                task.taskName(),
                task.taskMode(),
                task.status(),
                task.finishedPairs(),
                task.failedPairs(),
                task.totalPairs(),
                task.createdAt()
        );
    }
}
