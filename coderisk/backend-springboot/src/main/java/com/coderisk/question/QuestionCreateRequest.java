package com.coderisk.question;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record QuestionCreateRequest(
        @NotBlank @Size(max = 120) String title,
        @Size(max = 20000) String description,
        @Size(max = 8000) String inputFormat,
        @Size(max = 8000) String outputFormat,
        @Size(max = 8000) String constraintsText,
        @Size(max = 16) String starterLanguage,
        @Size(max = 20000) String starterCode,
        @Size(max = 2000) String starterSource
) {
}
