package com.coderisk.question;

import static com.coderisk.persistence.JdbcTimes.timestamp;

import com.coderisk.persistence.JdbcJson;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class QuestionFeatureRepository {

    private final JdbcTemplate jdbc;
    private final JdbcJson json;

    public QuestionFeatureRepository(JdbcTemplate jdbc, JdbcJson json) {
        this.jdbc = jdbc;
        this.json = json;
    }

    @Transactional
    public Map<String, Object> save(long questionId, Map<String, Object> profile, Map<String, Object> threshold) {
        String version = text(profile, "featureVersion", "pf-rule-v1.0");
        jdbc.update("DELETE FROM problem_feature WHERE question_id = ? AND feature_version = ?", questionId, version);
        OffsetDateTime now = OffsetDateTime.now();
        jdbc.update(
                """
                INSERT INTO problem_feature (
                    question_id, feature_version, description_length, io_field_count, input_output_complexity,
                    constraint_count, sample_count, reference_line_count, reference_function_count,
                    reference_cyclomatic_complexity, api_call_count, data_structure_count, data_structure_score,
                    algorithm_template_score, difficulty_score, solution_space_score, template_risk_score,
                    natural_similarity_risk, recommended_base_threshold, confidence, explanation_json,
                    threshold_adjustment_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                questionId,
                version,
                integer(profile, "descriptionLength"),
                integer(profile, "ioFieldCount"),
                Math.min(1.0, decimal(profile, "ioFieldCount") / 8.0),
                integer(profile, "constraintCount"),
                integer(profile, "sampleCount"),
                integer(profile, "referenceLineCount"),
                integer(profile, "referenceFunctionCount"),
                decimal(profile, "referenceCyclomaticComplexity"),
                integer(profile, "apiCallCount"),
                integer(profile, "dataStructureCount"),
                Math.min(1.0, decimal(profile, "dataStructureCount") / 5.0),
                decimal(profile, "templateRiskScore"),
                decimal(profile, "difficultyScore"),
                decimal(profile, "solutionSpaceScore"),
                decimal(profile, "templateRiskScore"),
                decimal(profile, "naturalSimilarityRisk"),
                decimal(profile, "recommendedBaseThreshold"),
                decimal(profile, "confidence"),
                json.write(profile.getOrDefault("explanation", Map.of())),
                json.write(threshold),
                timestamp(now),
                timestamp(now)
        );
        return latest(questionId);
    }

    public Map<String, Object> latest(long questionId) {
        List<Map<String, Object>> matches = jdbc.query(
                """
                SELECT * FROM problem_feature WHERE question_id = ? ORDER BY updated_at DESC LIMIT 1
                """,
                (rs, row) -> {
                    Map<String, Object> result = new LinkedHashMap<>();
                    result.put("questionId", rs.getLong("question_id"));
                    result.put("featureVersion", rs.getString("feature_version"));
                    result.put("descriptionLength", rs.getInt("description_length"));
                    result.put("ioFieldCount", rs.getInt("io_field_count"));
                    result.put("constraintCount", rs.getInt("constraint_count"));
                    result.put("sampleCount", rs.getInt("sample_count"));
                    result.put("referenceLineCount", rs.getInt("reference_line_count"));
                    result.put("referenceFunctionCount", rs.getInt("reference_function_count"));
                    result.put("referenceCyclomaticComplexity", rs.getDouble("reference_cyclomatic_complexity"));
                    result.put("apiCallCount", rs.getInt("api_call_count"));
                    result.put("dataStructureCount", rs.getInt("data_structure_count"));
                    result.put("difficultyScore", rs.getDouble("difficulty_score"));
                    result.put("solutionSpaceScore", rs.getDouble("solution_space_score"));
                    result.put("templateRiskScore", rs.getDouble("template_risk_score"));
                    result.put("naturalSimilarityRisk", rs.getDouble("natural_similarity_risk"));
                    result.put("recommendedBaseThreshold", rs.getDouble("recommended_base_threshold"));
                    result.put("confidence", rs.getDouble("confidence"));
                    result.put("explanation", json.readMap(rs.getString("explanation_json")));
                    result.put("thresholdAdjustment", json.readMap(rs.getString("threshold_adjustment_json")));
                    return Map.copyOf(result);
                },
                questionId
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    private int integer(Map<String, Object> values, String key) {
        Object value = values.get(key);
        return value instanceof Number number ? number.intValue() : 0;
    }

    private double decimal(Map<String, Object> values, String key) {
        Object value = values.get(key);
        return value instanceof Number number ? number.doubleValue() : 0.0;
    }

    private String text(Map<String, Object> values, String key, String fallback) {
        Object value = values.get(key);
        return value == null ? fallback : value.toString();
    }
}
