package com.coderisk.submission;

import com.coderisk.common.enums.LanguageSupportLevel;
import com.coderisk.common.enums.ParserStatus;
import java.time.OffsetDateTime;

public record SubmissionResponse(
        long id,
        long questionId,
        String studentId,
        String language,
        String languageVersion,
        LanguageSupportLevel supportLevel,
        String fileName,
        long fileSizeBytes,
        String rawCodePath,
        ParserStatus parserStatus,
        OffsetDateTime createdAt
) {
}
