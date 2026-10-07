package com.coderisk.result;

import com.coderisk.common.enums.RiskLevel;
import java.time.OffsetDateTime;
import java.util.Map;

public record ResultResponse(
        long id,
        long taskId,
        long submissionAId,
        long submissionBId,
        String submissionAFileName,
        String submissionBFileName,
        double tokenSimilarity,
        double astSimilarity,
        double canonicalTokenSimilarity,
        double identifierMappingSimilarity,
        double weightedSimilarityScore,
        double dynamicThreshold,
        double riskMargin,
        double calibratedRiskScore,
        boolean exceedThreshold,
        double marginScale,
        String formulaVersion,
        String algorithmVersion,
        String metricConfigHash,
        RiskLevel riskLevel,
        Map<String, Object> problemProfile,
        Map<String, Object> thresholdAdjustment,
        String reasonSummary,
        boolean isMock,
        OffsetDateTime createdAt
) {
}
