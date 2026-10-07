package com.coderisk.question;

import com.coderisk.integration.analysis.AnalysisClient;
import com.coderisk.integration.analysis.AnalysisQuestion;
import com.coderisk.integration.analysis.ProblemScoreRequest;
import com.coderisk.integration.analysis.ProblemScoreResult;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class QuestionFeatureService {

    private final QuestionService questionService;
    private final AnalysisClient analysisClient;
    private final QuestionFeatureRepository repository;

    public QuestionFeatureService(
            QuestionService questionService,
            AnalysisClient analysisClient,
            QuestionFeatureRepository repository
    ) {
        this.questionService = questionService;
        this.analysisClient = analysisClient;
        this.repository = repository;
    }

    public Map<String, Object> compute(long questionId, Map<String, Object> config) {
        QuestionResponse question = questionService.get(questionId);
        ProblemScoreResult scored = analysisClient.scoreProblem(new ProblemScoreRequest(
                new AnalysisQuestion(
                        question.id(),
                        question.title(),
                        question.description(),
                        question.inputFormat(),
                        question.outputFormat(),
                        question.constraintsText()
                ),
                config == null ? Map.of() : config
        ));
        return repository.save(
                questionId,
                scored.problemProfile() == null ? Map.of() : scored.problemProfile(),
                scored.thresholdAdjustment() == null ? Map.of() : scored.thresholdAdjustment()
        );
    }

    public Map<String, Object> latest(long questionId) {
        questionService.get(questionId);
        Map<String, Object> existing = repository.latest(questionId);
        return existing == null ? compute(questionId, Map.of()) : existing;
    }
}
