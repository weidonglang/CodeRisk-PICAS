package com.coderisk.common.config;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "coderisk")
public record CoderiskProperties(
        @NotBlank String appVersion,
        Upload upload,
        Artifacts artifacts,
        Analysis analysis
) {

    public record Upload(
            @NotBlank String rootPath,
            @Min(1) int maxFileSizeMb,
            List<String> allowedExtensions
    ) {
    }

    public record Artifacts(@NotBlank String rootPath) {
    }

    public record Analysis(
            @NotBlank String baseUrl,
            @Min(1) int timeoutSeconds
    ) {
    }
}
