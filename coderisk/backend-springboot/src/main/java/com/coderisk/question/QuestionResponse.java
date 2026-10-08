package com.coderisk.question;

import java.time.OffsetDateTime;

public record QuestionResponse(
        long id,
        String title,
        String description,
        String inputFormat,
        String outputFormat,
        String constraintsText,
        String starterLanguage,
        String starterCode,
        String starterSource,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
) {
}
