package com.coderisk.result;

public record CodePairResponse(
        long resultId,
        long taskId,
        CodeSideResponse submissionA,
        CodeSideResponse submissionB
) {
}
