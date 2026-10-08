package com.coderisk.task;

import com.coderisk.common.enums.RiskLevel;
import com.coderisk.common.enums.TaskMode;
import com.coderisk.common.enums.TaskStatus;
import com.coderisk.common.exception.ApiException;
import com.coderisk.common.response.PageResult;
import com.coderisk.integration.analysis.AnalysisClient;
import com.coderisk.integration.analysis.AnalysisQuestion;
import com.coderisk.integration.analysis.AnalysisSubmission;
import com.coderisk.integration.analysis.AnalyzeMockRequest;
import com.coderisk.integration.analysis.AnalyzeMockResult;
import com.coderisk.question.QuestionResponse;
import com.coderisk.question.QuestionService;
import com.coderisk.result.ResultResponse;
import com.coderisk.result.ResultService;
import com.coderisk.result.TaskResultSummary;
import com.coderisk.submission.SubmissionResponse;
import com.coderisk.submission.SubmissionService;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class TaskService {

    private final QuestionService questionService;
    private final SubmissionService submissionService;
    private final AnalysisClient analysisClient;
    private final ResultService resultService;
    private final TaskRepository repository;

    public TaskService(
            QuestionService questionService,
            SubmissionService submissionService,
            AnalysisClient analysisClient,
            ResultService resultService,
            TaskRepository repository
    ) {
        this.questionService = questionService;
        this.submissionService = submissionService;
        this.analysisClient = analysisClient;
        this.resultService = resultService;
        this.repository = repository;
    }

    public DetectionTaskResponse create(TaskCreateRequest request) {
        QuestionResponse question = questionService.get(request.questionId());
        List<SubmissionResponse> submissions = resolveSubmissions(question.id(), request.submissionIds());
        if (submissions.size() < 2) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_REQUIRES_TWO_SUBMISSIONS", "At least two submissions are required");
        }
        List<String> languages = submissions.stream().map(SubmissionResponse::language).distinct().toList();
        if (languages.size() > 1 && languages.stream().anyMatch(language -> List.of("c", "html").contains(language))) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_LANGUAGE_DOMAIN_MISMATCH",
                    "C and HTML tasks require same-language submissions; create separate tasks for different languages");
        }
        List<Long> submissionIds = submissions.stream().map(SubmissionResponse::id).toList();
        return repository.save(
                question.id(),
                normalizeTaskName(request.taskName(), question.title()),
                request.taskMode() == null ? TaskMode.PICAS_STANDARD : request.taskMode(),
                submissionIds
        );
    }

    public DetectionTaskResponse start(long taskId) {
        DetectionTaskResponse task = get(taskId);
        if (task.status() == TaskStatus.FINISHED) {
            return task;
        }
        repository.updateState(task.id(), TaskStatus.RUNNING, 0, 0, "", null);

        QuestionResponse question = questionService.get(task.questionId());
        List<SubmissionResponse> submissions = submissionService.getAll(task.submissionIds());
        int finished = 0;
        int failed = 0;
        String lastFailure = "";
        List<List<SubmissionResponse>> pairs = pairs(submissions);
        for (List<SubmissionResponse> pair : pairs) {
            try {
                AnalyzeMockResult analysisResult = analysisClient.analyzePair(toAnalysisRequest(task.id(), question, pair.get(0), pair.get(1)));
                resultService.saveMockResult(task.id(), pair.get(0), pair.get(1), analysisResult);
                finished++;
                repository.updateState(task.id(), TaskStatus.RUNNING, finished, failed, "", null);
            } catch (RuntimeException exception) {
                failed++;
                lastFailure = exception.getMessage();
            }
        }

        TaskStatus finalStatus = failed == 0 ? TaskStatus.FINISHED : finished == 0 ? TaskStatus.FAILED : TaskStatus.PARTIAL;
        return finish(taskId, finalStatus, finished, lastFailure);
    }

    public DetectionTaskResponse get(long taskId) {
        DetectionTaskResponse response = repository.find(taskId);
        if (response == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "TASK_NOT_FOUND", "Task not found: " + taskId);
        }
        return response;
    }

    public List<TaskSummary> recent() {
        return repository.recent(20).stream()
                .map(TaskSummary::from)
                .toList();
    }

    public List<ResultResponse> results(long taskId) {
        get(taskId);
        return resultService.findByTask(taskId);
    }

    public PageResult<ResultResponse> resultPage(long taskId, int page, int pageSize, RiskLevel riskLevel) {
        int safePage = Math.max(page, 1);
        int safePageSize = Math.min(Math.max(pageSize, 1), 100);
        List<ResultResponse> filtered = results(taskId).stream()
                .filter(result -> riskLevel == null || result.riskLevel() == riskLevel)
                .toList();
        int fromIndex = Math.min((safePage - 1) * safePageSize, filtered.size());
        int toIndex = Math.min(fromIndex + safePageSize, filtered.size());
        return new PageResult<>(filtered.subList(fromIndex, toIndex), filtered.size(), safePage, safePageSize);
    }

    public TaskResultSummary resultSummary(long taskId) {
        List<ResultResponse> results = results(taskId);
        long low = countLevel(results, RiskLevel.LOW);
        long medium = countLevel(results, RiskLevel.MEDIUM);
        long elevated = countLevel(results, RiskLevel.ELEVATED);
        long high = countLevel(results, RiskLevel.HIGH);
        boolean containsMock = results.stream().anyMatch(ResultResponse::isMock);
        return new TaskResultSummary(taskId, results.size(), low, medium, elevated, high, containsMock);
    }

    public long count() {
        return repository.count();
    }

    private List<SubmissionResponse> resolveSubmissions(long questionId, List<Long> submissionIds) {
        List<SubmissionResponse> submissions;
        if (submissionIds == null || submissionIds.isEmpty()) {
            submissions = submissionService.listByQuestion(questionId);
        } else {
            submissions = submissionService.getAll(submissionIds);
        }
        boolean wrongQuestion = submissions.stream().anyMatch(submission -> submission.questionId() != questionId);
        if (wrongQuestion) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_SUBMISSION_QUESTION_MISMATCH", "All submissions must belong to the task question");
        }
        return submissions;
    }

    private AnalyzeMockRequest toAnalysisRequest(
            long taskId,
            QuestionResponse question,
            SubmissionResponse submissionA,
            SubmissionResponse submissionB
    ) {
        return new AnalyzeMockRequest(
                taskId,
                new AnalysisQuestion(
                        question.id(),
                        question.title(),
                        question.description(),
                        question.inputFormat(),
                        question.outputFormat(),
                        question.constraintsText()
                ),
                new AnalysisSubmission(submissionA.id(), submissionA.language(), submissionA.fileName(), submissionA.rawCodePath(), null),
                new AnalysisSubmission(submissionB.id(), submissionB.language(), submissionB.fileName(), submissionB.rawCodePath(), null),
                Map.of("mode", taskModeFor(taskId), "baseThreshold", 0.68)
        );
    }

    private List<List<SubmissionResponse>> pairs(List<SubmissionResponse> submissions) {
        List<List<SubmissionResponse>> pairs = new ArrayList<>();
        for (int i = 0; i < submissions.size(); i++) {
            for (int j = i + 1; j < submissions.size(); j++) {
                pairs.add(List.of(submissions.get(i), submissions.get(j)));
            }
        }
        return pairs;
    }

    private String normalizeTaskName(String taskName, String questionTitle) {
        if (taskName == null || taskName.isBlank()) {
            return questionTitle + " detection";
        }
        return taskName.trim();
    }

    private DetectionTaskResponse finish(
            long taskId,
            TaskStatus status,
            int finishedPairs,
            String failureReason
    ) {
        int failedPairs = Math.max(0, get(taskId).totalPairs() - finishedPairs);
        repository.updateState(
                taskId,
                status,
                finishedPairs,
                failedPairs,
                failureReason == null ? "" : failureReason,
                OffsetDateTime.now()
        );
        return get(taskId);
    }

    private long countLevel(List<ResultResponse> results, RiskLevel level) {
        return results.stream().filter(result -> result.riskLevel() == level).count();
    }

    private String taskModeFor(long taskId) {
        return get(taskId).taskMode().name();
    }
}
