package com.coderisk.system;

import com.coderisk.common.web.ResponseFactory;
import com.coderisk.question.QuestionService;
import com.coderisk.result.ResultService;
import com.coderisk.submission.SubmissionService;
import com.coderisk.task.TaskSummary;
import com.coderisk.task.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final ResponseFactory responses;
    private final QuestionService questionService;
    private final SubmissionService submissionService;
    private final TaskService taskService;
    private final ResultService resultService;

    public DashboardController(
            ResponseFactory responses,
            QuestionService questionService,
            SubmissionService submissionService,
            TaskService taskService,
            ResultService resultService
    ) {
        this.responses = responses;
        this.questionService = questionService;
        this.submissionService = submissionService;
        this.taskService = taskService;
        this.resultService = resultService;
    }

    @GetMapping("/summary")
    public Object summary(HttpServletRequest request) {
        DashboardSummary summary = new DashboardSummary(
                questionService.count(),
                submissionService.count(),
                taskService.count(),
                resultService.highRiskCount(),
                "V2 delivery + V3 minimal experiment",
                "JDBC persistence, token/AST/canonical analysis, dynamic thresholds, evidence, and HTML reports enabled"
        );
        return responses.ok(summary, request);
    }

    @GetMapping("/recent-tasks")
    public Object recentTasks(HttpServletRequest request) {
        return responses.ok(taskService.recent(), request);
    }
}
