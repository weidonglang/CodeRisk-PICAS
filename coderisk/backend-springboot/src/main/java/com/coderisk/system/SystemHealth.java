package com.coderisk.system;

import java.time.OffsetDateTime;

public record SystemHealth(
        String status,
        String appVersion,
        String service,
        OffsetDateTime checkedAt,
        String analysisBaseUrl
) {
}
