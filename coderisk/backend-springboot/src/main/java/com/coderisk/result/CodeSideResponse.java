package com.coderisk.result;

public record CodeSideResponse(
        long submissionId,
        String fileName,
        String language,
        String code
) {
}
