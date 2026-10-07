package com.coderisk.task;

import com.coderisk.common.enums.TaskMode;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record TaskCreateRequest(
        @NotNull Long questionId,
        @Size(max = 120) String taskName,
        List<Long> submissionIds,
        TaskMode taskMode
) {
}
