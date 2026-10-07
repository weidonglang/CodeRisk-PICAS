package com.coderisk.result;

import com.coderisk.common.web.ResponseFactory;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/results")
public class ResultController {

    private final ResultService resultService;
    private final ResponseFactory responses;

    public ResultController(ResultService resultService, ResponseFactory responses) {
        this.resultService = resultService;
        this.responses = responses;
    }

    @GetMapping("/{resultId}")
    public Object get(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.get(resultId), request);
    }

    @GetMapping("/{resultId}/evidence")
    public Object evidence(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.evidenceForResult(resultId), request);
    }

    @GetMapping("/{resultId}/metrics")
    public Object metrics(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.metricsForResult(resultId), request);
    }

    @GetMapping("/{resultId}/threshold-adjustment")
    public Object thresholdAdjustment(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.thresholdAdjustment(resultId), request);
    }

    @GetMapping("/{resultId}/identifier-mappings")
    public Object identifierMappings(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.identifierMappings(resultId), request);
    }

    @GetMapping("/{resultId}/code-pair")
    public Object codePair(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.codePair(resultId), request);
    }

    @GetMapping("/{resultId}/diff-view")
    public Object diffView(@PathVariable long resultId, HttpServletRequest request) {
        return responses.ok(resultService.diffView(resultId), request);
    }
}
