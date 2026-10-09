package com.coderisk.task;

import java.time.OffsetDateTime;

public record TaskPairFailure(long submissionAId, long submissionBId, String message,
                              int attempts, boolean resolved, OffsetDateTime lastAttemptAt) { }
