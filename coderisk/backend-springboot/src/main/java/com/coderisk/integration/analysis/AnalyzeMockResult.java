package com.coderisk.integration.analysis;

import java.util.List;
import java.util.Map;

public record AnalyzeMockResult(
        Long taskId,
        long submissionAId,
        long submissionBId,
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
        String riskLevel,
        Map<String, Object> problemProfile,
        Map<String, Object> thresholdAdjustment,
        String reasonSummary,
        boolean isMock,
        List<MetricData> metrics,
        List<EvidenceData> evidence
) {
}
