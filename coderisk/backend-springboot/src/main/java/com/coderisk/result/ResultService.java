package com.coderisk.result;

import com.coderisk.common.exception.ApiException;
import com.coderisk.integration.analysis.AnalyzeMockResult;
import com.coderisk.integration.analysis.MetricData;
import com.coderisk.submission.SubmissionResponse;
import com.coderisk.submission.SubmissionService;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class ResultService {

    private final SubmissionService submissionService;
    private final ResultRepository repository;

    public ResultService(SubmissionService submissionService, ResultRepository repository) {
        this.submissionService = submissionService;
        this.repository = repository;
    }

    public ResultResponse saveMockResult(
            long taskId,
            SubmissionResponse submissionA,
            SubmissionResponse submissionB,
            AnalyzeMockResult analysisResult
    ) {
        return repository.save(taskId, submissionA, submissionB, analysisResult);
    }

    public List<ResultResponse> findByTask(long taskId) {
        return repository.findByTask(taskId);
    }

    public ResultResponse get(long resultId) {
        ResultResponse response = repository.find(resultId);
        if (response == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "RESULT_NOT_FOUND", "Result not found: " + resultId);
        }
        return response;
    }

    public List<EvidenceResponse> evidenceForResult(long resultId) {
        get(resultId);
        return repository.evidence(resultId);
    }

    public List<MetricData> metricsForResult(long resultId) {
        get(resultId);
        return repository.metrics(resultId);
    }

    public Map<String, Object> thresholdAdjustment(long resultId) {
        get(resultId);
        return repository.threshold(resultId);
    }

    public List<Map<String, Object>> identifierMappings(long resultId) {
        get(resultId);
        return repository.mappings(resultId);
    }

    public CodePairResponse codePair(long resultId) {
        ResultResponse result = get(resultId);
        SubmissionResponse submissionA = submissionService.get(result.submissionAId());
        SubmissionResponse submissionB = submissionService.get(result.submissionBId());
        return new CodePairResponse(
                result.id(),
                result.taskId(),
                toCodeSide(submissionA),
                toCodeSide(submissionB)
        );
    }

    public DiffViewResponse diffView(long resultId) {
        ResultResponse result = get(resultId);
        SubmissionResponse submissionA = submissionService.get(result.submissionAId());
        SubmissionResponse submissionB = submissionService.get(result.submissionBId());
        return new DiffViewResponse(
                result.id(),
                result.taskId(),
                toCodeSide(submissionA),
                toCodeSide(submissionB),
                diffHighlights(result.id())
        );
    }

    public long count() {
        return repository.count();
    }

    public long highRiskCount() {
        return repository.highRiskCount();
    }

    private CodeSideResponse toCodeSide(SubmissionResponse submission) {
        return new CodeSideResponse(
                submission.id(),
                submission.fileName(),
                submission.language(),
                readCode(submission.rawCodePath())
        );
    }

    private String readCode(String rawCodePath) {
        try {
            return Files.readString(Path.of(rawCodePath));
        } catch (IOException | RuntimeException exception) {
            throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "CODE_READ_FAILED", "Failed to read submitted code");
        }
    }

    private List<DiffHighlightResponse> diffHighlights(long resultId) {
        return evidenceForResult(resultId).stream()
                .flatMap(evidence -> fragmentMaps(evidence.metadata()).stream()
                        .map(fragment -> new DiffHighlightResponse(
                                evidence.id(),
                                evidence.evidenceType().name(),
                                new LineRangeResponse(
                                        intValue(fragment.get("submissionAStartLine")),
                                        intValue(fragment.get("submissionAEndLine"))
                                ),
                                new LineRangeResponse(
                                        intValue(fragment.get("submissionBStartLine")),
                                        intValue(fragment.get("submissionBEndLine"))
                                ),
                                evidence.similarityScore()
                        )))
                .toList();
    }

    private List<Map<String, Object>> fragmentMaps(Map<String, Object> metadata) {
        Object fragments = metadata == null ? null : metadata.get("fragments");
        if (!(fragments instanceof List<?> list)) {
            return List.of();
        }
        return list.stream()
                .filter(Map.class::isInstance)
                .map(item -> typedFragmentMap((Map<?, ?>) item))
                .toList();
    }

    private Map<String, Object> typedFragmentMap(Map<?, ?> fragment) {
        Map<String, Object> typed = new java.util.LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : fragment.entrySet()) {
            if (entry.getKey() instanceof String key) {
                typed.put(key, entry.getValue());
            }
        }
        return typed;
    }

    private int intValue(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value instanceof String text) {
            try {
                return Integer.parseInt(text);
            } catch (NumberFormatException ignored) {
                return 0;
            }
        }
        return 0;
    }

}
