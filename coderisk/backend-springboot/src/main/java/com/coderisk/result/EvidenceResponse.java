package com.coderisk.result;

import com.coderisk.common.enums.EvidenceType;
import java.util.Map;

public record EvidenceResponse(
        long id,
        long resultId,
        EvidenceType evidenceType,
        double similarityScore,
        String description,
        Map<String, Object> metadata
) {
}
