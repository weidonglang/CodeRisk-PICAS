package com.coderisk.integration.analysis;

import java.util.Map;

public record EvidenceData(
        String evidenceType,
        double similarityScore,
        String description,
        Map<String, Object> metadata
) {
}
