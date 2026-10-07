package com.coderisk.integration.analysis;

public interface AnalysisClient {

    AnalyzeMockResult analyzePair(AnalyzeMockRequest request);

    AnalyzeMockResult analyzeMock(AnalyzeMockRequest request);

    ProblemScoreResult scoreProblem(ProblemScoreRequest request);
}
