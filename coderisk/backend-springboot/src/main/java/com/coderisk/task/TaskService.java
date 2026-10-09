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
import java.util.HashSet;
import java.util.Comparator;
import java.util.Set;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class TaskService {

    private static final Logger log = LoggerFactory.getLogger(TaskService.class);
    private static final int MAX_SUBMISSIONS = 100;
    private final Executor executor;
    private final long timeBudgetNanos;

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
            TaskRepository repository,
            @Qualifier("coderiskTaskExecutor") Executor executor,
            @Value("${coderisk.tasks.time-budget-seconds:900}") int timeBudgetSeconds
    ) {
        this.questionService = questionService;
        this.submissionService = submissionService;
        this.analysisClient = analysisClient;
        this.resultService = resultService;
        this.repository = repository;
        this.executor = executor;
        if (timeBudgetSeconds < 1 || timeBudgetSeconds > 7200) {
            throw new IllegalArgumentException("Task time budget must be 1–7200 seconds");
        }
        this.timeBudgetNanos = java.util.concurrent.TimeUnit.SECONDS.toNanos(timeBudgetSeconds);
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

    @EventListener(ApplicationReadyEvent.class)
    public void recoverInterruptedTasks() {
        int count = repository.recoverInterrupted();
        if (count > 0) log.warn("Marked {} interrupted tasks resumable after service restart", count);
    }

    public DetectionTaskResponse start(long taskId) {
        DetectionTaskResponse previous = get(taskId);
        if (!repository.claim(taskId)) return get(taskId);
        DetectionTaskResponse accepted = get(taskId);
        try {
            executor.execute(() -> execute(taskId));
        } catch (RejectedExecutionException exception) {
            repository.updateState(taskId, previous.status(), previous.finishedPairs(), previous.failedPairs(),
                    "TASK_CAPACITY_EXCEEDED: retry later", previous.finishedAt());
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "TASK_CAPACITY_EXCEEDED", "Task workers and queue are full; retry later");
        }
        return accepted;
    }

    private record PairKey(long a, long b) { }

    private void execute(long taskId) {
        long begin = System.nanoTime();
        try {
            DetectionTaskResponse task = get(taskId);
            QuestionResponse question = questionService.get(task.questionId());
            List<SubmissionResponse> submissions = submissionService.getAll(task.submissionIds());
            Set<PairKey> completed = new HashSet<>();
            for (ResultResponse result : resultService.findByTask(taskId)) {
                completed.add(new PairKey(result.submissionAId(), result.submissionBId()));
            }
            int finished = completed.size();
            int failed = 0;
            String lastFailure = "";
            repository.updateState(taskId, TaskStatus.RUNNING, finished, failed, "", null);
            for (int i = 0; i < submissions.size(); i++) {
                for (int j = i + 1; j < submissions.size(); j++) {
                    if (Thread.currentThread().isInterrupted()) throw new IllegalStateException("TASK_INTERRUPTED: retry unfinished pairs");
                    SubmissionResponse left = submissions.get(i), right = submissions.get(j);
                    if (completed.contains(new PairKey(left.id(), right.id()))) {
                        repository.resolveFailure(taskId, left.id(), right.id());
                        continue;
                    }
                    if (System.nanoTime() - begin >= timeBudgetNanos) {
                        throw new IllegalStateException("TASK_TIME_BUDGET_EXCEEDED: retry unfinished pairs");
                    }
                    try {
                        AnalyzeMockResult result = analysisClient.analyzePair(toAnalysisRequest(taskId, question, left, right));
                        resultService.saveMockResult(taskId, left, right, result);
                        finished++;
                        repository.resolveFailure(taskId, left.id(), right.id());
                    } catch (RuntimeException exception) {
                        failed++;
                        lastFailure = exception.getMessage() == null ? exception.getClass().getSimpleName() : exception.getMessage();
                        repository.recordFailure(taskId, left.id(), right.id(), lastFailure);
                        log.warn("Task {} analysis failed for pair {}/{}", taskId, left.id(), right.id());
                    }
                    repository.updateState(taskId, TaskStatus.RUNNING, finished, failed, lastFailure, null);
                }
            }
            finish(taskId, failed == 0 ? TaskStatus.FINISHED : finished == 0 ? TaskStatus.FAILED : TaskStatus.PARTIAL,
                    finished, lastFailure);
        } catch (RuntimeException exception) {
            log.error("Task {} stopped before completing all pairs", taskId, exception);
            int saved = resultService.findByTask(taskId).size();
            finish(taskId, saved > 0 ? TaskStatus.PARTIAL : TaskStatus.FAILED, saved, exception.getMessage());
        }
    }

    public List<TaskPairFailure> failures(long taskId) {
        get(taskId);
        return repository.failures(taskId);
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
        if (submissions.size() > MAX_SUBMISSIONS) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_TOO_MANY_SUBMISSIONS", "At most 100 submissions per task");
        }
        if (submissions.stream().map(SubmissionResponse::id).distinct().count() != submissions.size()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_DUPLICATE_SUBMISSION", "Submission IDs must be distinct");
        }
        boolean wrongQuestion = submissions.stream().anyMatch(submission -> submission.questionId() != questionId);
        if (wrongQuestion) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "TASK_SUBMISSION_QUESTION_MISMATCH", "All submissions must belong to the task question");
        }
        return submissions.stream().sorted(Comparator.comparingLong(SubmissionResponse::id)).toList();
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
                        question.constraintsText(),
                        question.starterLanguage(), question.starterCode(), question.starterSource()
                ),
                new AnalysisSubmission(submissionA.id(), submissionA.language(), submissionA.fileName(), submissionA.rawCodePath(), null, submissionA.languageVersion()),
                new AnalysisSubmission(submissionB.id(), submissionB.language(), submissionB.fileName(), submissionB.rawCodePath(), null, submissionB.languageVersion()),
                Map.of("mode", taskModeFor(taskId), "baseThreshold", 0.68)
        );
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
