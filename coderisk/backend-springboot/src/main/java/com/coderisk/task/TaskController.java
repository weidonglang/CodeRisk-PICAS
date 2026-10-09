package com.coderisk.task;

import com.coderisk.common.web.ResponseFactory;
import com.coderisk.common.enums.RiskLevel;
import com.coderisk.report.ReportCreateRequest;
import com.coderisk.report.ReportService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestParam;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskService taskService;
    private final ResponseFactory responses;
    private final ReportService reportService;

    public TaskController(TaskService taskService, ResponseFactory responses, ReportService reportService) {
        this.taskService = taskService;
        this.responses = responses;
        this.reportService = reportService;
    }

    @PostMapping
    public Object create(@Valid @RequestBody TaskCreateRequest createRequest, HttpServletRequest request) {
        return responses.ok(taskService.create(createRequest), request);
    }

    @PostMapping("/{taskId}/start")
    public Object start(@PathVariable long taskId, HttpServletRequest request) {
        return responses.ok(taskService.start(taskId), request);
    }

    @GetMapping("/{taskId}")
    public Object get(@PathVariable long taskId, HttpServletRequest request) {
        return responses.ok(taskService.get(taskId), request);
    }

    @GetMapping("/{taskId}/failures")
    public Object failures(@PathVariable long taskId, HttpServletRequest request) {
        return responses.ok(taskService.failures(taskId), request);
    }

    @GetMapping("/recent")
    public Object recent(HttpServletRequest request) {
        return responses.ok(taskService.recent(), request);
    }

    @GetMapping("/{taskId}/results")
    public Object results(
            @PathVariable long taskId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) RiskLevel riskLevel,
            HttpServletRequest request
    ) {
        return responses.ok(taskService.resultPage(taskId, page, pageSize, riskLevel), request);
    }

    @GetMapping("/{taskId}/results/summary")
    public Object resultSummary(@PathVariable long taskId, HttpServletRequest request) {
        return responses.ok(taskService.resultSummary(taskId), request);
    }

    @PostMapping("/{taskId}/reports")
    public Object generateReport(
            @PathVariable long taskId,
            @RequestBody ReportCreateRequest createRequest,
            HttpServletRequest request
    ) {
        return responses.ok(reportService.generate(taskId, createRequest), request);
    }

    @GetMapping("/{taskId}/reports")
    public Object reports(@PathVariable long taskId, HttpServletRequest request) {
        return responses.ok(reportService.list(taskId), request);
    }
}
