package com.coderisk.question;

import com.coderisk.common.web.ResponseFactory;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/questions")
public class QuestionController {

    private final QuestionService questionService;
    private final QuestionFeatureService questionFeatureService;
    private final ResponseFactory responses;

    public QuestionController(
            QuestionService questionService,
            QuestionFeatureService questionFeatureService,
            ResponseFactory responses
    ) {
        this.questionService = questionService;
        this.questionFeatureService = questionFeatureService;
        this.responses = responses;
    }

    @PostMapping
    public Object create(
            @Valid @RequestBody QuestionCreateRequest createRequest,
            HttpServletRequest request
    ) {
        return responses.ok(questionService.create(createRequest), request);
    }

    @GetMapping
    public Object list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            HttpServletRequest request
    ) {
        return responses.ok(questionService.list(page, size), request);
    }

    @GetMapping("/{questionId}")
    public Object get(@PathVariable long questionId, HttpServletRequest request) {
        return responses.ok(questionService.get(questionId), request);
    }

    @PostMapping("/{questionId}/features/compute")
    public Object computeFeatures(
            @PathVariable long questionId,
            @RequestBody(required = false) Map<String, Object> config,
            HttpServletRequest request
    ) {
        return responses.ok(questionFeatureService.compute(questionId, config), request);
    }

    @GetMapping("/{questionId}/features/latest")
    public Object latestFeatures(@PathVariable long questionId, HttpServletRequest request) {
        return responses.ok(questionFeatureService.latest(questionId), request);
    }
}
