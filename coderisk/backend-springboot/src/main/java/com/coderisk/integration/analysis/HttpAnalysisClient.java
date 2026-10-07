package com.coderisk.integration.analysis;

import com.coderisk.common.config.CoderiskProperties;
import com.coderisk.common.exception.ApiException;
import java.time.Duration;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class HttpAnalysisClient implements AnalysisClient {

    private final RestClient restClient;

    public HttpAnalysisClient(CoderiskProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        int timeoutMillis = (int) Duration.ofSeconds(properties.analysis().timeoutSeconds()).toMillis();
        requestFactory.setConnectTimeout(timeoutMillis);
        requestFactory.setReadTimeout(timeoutMillis);
        this.restClient = RestClient.builder()
                .baseUrl(properties.analysis().baseUrl())
                .requestFactory(requestFactory)
                .build();
    }

    @Override
    public AnalyzeMockResult analyzePair(AnalyzeMockRequest request) {
        return postForResult("/internal/analyze/pair", request);
    }

    @Override
    public AnalyzeMockResult analyzeMock(AnalyzeMockRequest request) {
        return postForResult("/internal/analyze/mock", request);
    }

    @Override
    public ProblemScoreResult scoreProblem(ProblemScoreRequest request) {
        AnalysisEnvelope<ProblemScoreResult> envelope = restClient.post()
                .uri("/internal/problem/score")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {
                });
        if (envelope == null || !envelope.success() || envelope.result() == null) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "PROBLEM_SCORE_FAILED", "Analysis service could not score the problem");
        }
        return envelope.result();
    }

    private AnalyzeMockResult postForResult(String uri, AnalyzeMockRequest request) {
        AnalysisEnvelope<AnalyzeMockResult> envelope = restClient.post()
                .uri(uri)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {
                });
        if (envelope == null) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "ANALYSIS_SERVICE_EMPTY_RESPONSE", "Analysis service returned empty response");
        }
        if (!envelope.success()) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "ANALYSIS_FAILED", envelope.message());
        }
        return envelope.result();
    }
}
