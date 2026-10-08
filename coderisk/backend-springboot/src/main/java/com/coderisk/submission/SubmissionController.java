package com.coderisk.submission;

import com.coderisk.common.web.ResponseFactory;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/questions/{questionId}/submissions")
public class SubmissionController {

    private final SubmissionService submissionService;
    private final ResponseFactory responses;

    public SubmissionController(SubmissionService submissionService, ResponseFactory responses) {
        this.submissionService = submissionService;
        this.responses = responses;
    }

    @PostMapping("/upload")
    public Object upload(
            @PathVariable long questionId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "") String studentId,
            @RequestParam(defaultValue = "") String languageVersion,
            HttpServletRequest request
    ) {
        return responses.ok(submissionService.store(questionId, file, studentId, languageVersion), request);
    }

    @GetMapping
    public Object list(@PathVariable long questionId, HttpServletRequest request) {
        return responses.ok(submissionService.listByQuestion(questionId), request);
    }
}
