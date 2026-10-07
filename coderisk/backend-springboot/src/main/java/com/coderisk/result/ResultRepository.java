package com.coderisk.result;

import static com.coderisk.persistence.JdbcTimes.offset;
import static com.coderisk.persistence.JdbcTimes.timestamp;

import com.coderisk.common.enums.EvidenceType;
import com.coderisk.common.enums.RiskLevel;
import com.coderisk.integration.analysis.AnalyzeMockResult;
import com.coderisk.integration.analysis.EvidenceData;
import com.coderisk.integration.analysis.MetricData;
import com.coderisk.persistence.JdbcJson;
import com.coderisk.question.QuestionFeatureRepository;
import com.coderisk.submission.SubmissionResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ResultRepository {

    private static final String ALGORITHM_VERSION = "picas-v2-rule-1.0";
    private static final String CROSSLANG_ALGORITHM_VERSION = "picas-v4-xl-ir0.1-sum0.2-exp";

    private final JdbcTemplate jdbc;
    private final JdbcJson json;
    private final QuestionFeatureRepository featureRepository;
    private final SimpleJdbcInsert resultInsert;
    private final SimpleJdbcInsert evidenceInsert;

    public ResultRepository(JdbcTemplate jdbc, JdbcJson json, QuestionFeatureRepository featureRepository) {
        this.jdbc = jdbc;
        this.json = json;
        this.featureRepository = featureRepository;
        this.resultInsert = new SimpleJdbcInsert(jdbc)
                .withTableName("analysis_result")
                .usingGeneratedKeyColumns("id");
        this.evidenceInsert = new SimpleJdbcInsert(jdbc)
                .withTableName("evidence")
                .usingGeneratedKeyColumns("id");
    }

    @Transactional
    public ResultResponse save(
            long taskId,
            SubmissionResponse submissionA,
            SubmissionResponse submissionB,
            AnalyzeMockResult analysis
    ) {
        Map<String, Object> profile = analysis.problemProfile() == null ? Map.of() : analysis.problemProfile();
        Map<String, Object> threshold = analysis.thresholdAdjustment() == null ? Map.of() : analysis.thresholdAdjustment();
        if (!profile.isEmpty()) {
            featureRepository.save(submissionA.questionId(), profile, threshold);
        }
        OffsetDateTime now = OffsetDateTime.now();
        List<EvidenceData> evidence = analysis.evidence() == null ? List.of() : analysis.evidence();
        List<MetricData> metrics = completeMetrics(analysis);
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("task_id", taskId);
        values.put("question_id", submissionA.questionId());
        values.put("submission_a_id", submissionA.id());
        values.put("submission_b_id", submissionB.id());
        values.put("language_pair", submissionA.language() + "-" + submissionB.language());
        values.put("weighted_similarity_score", analysis.weightedSimilarityScore());
        values.put("dynamic_threshold", analysis.dynamicThreshold());
        values.put("risk_margin", analysis.riskMargin());
        values.put("calibrated_risk_score", analysis.calibratedRiskScore());
        values.put("risk_level", safeRiskLevel(analysis.riskLevel()).name());
        values.put("exceed_threshold", analysis.exceedThreshold() ? 1 : 0);
        values.put("margin_scale", analysis.marginScale());
        values.put("formula_version", analysis.formulaVersion());
        values.put("algorithm_version", algorithmVersion(metrics));
        values.put("metric_config_hash", sha256(json.write(metrics)));
        values.put("threshold_explanation", text(threshold, "explanation"));
        values.put("threshold_adjustment_json", json.write(threshold));
        values.put("evidence_count", evidence.size());
        values.put("high_confidence_evidence_count", evidence.stream().filter(item -> item.similarityScore() >= 0.8).count());
        values.put("status", "FINISHED");
        values.put("reason_summary", analysis.reasonSummary());
        values.put("is_mock", analysis.isMock() ? 1 : 0);
        values.put("created_at", timestamp(now));
        values.put("updated_at", timestamp(now));
        long resultId = resultInsert.executeAndReturnKey(values).longValue();

        for (MetricData metric : metrics) {
            jdbc.update(
                    """
                    INSERT INTO similarity_metric
                    (result_id, metric_name, metric_value, metric_weight, metric_status, explanation, created_at)
                    VALUES (?, ?, ?, ?, 'VALID', ?, ?)
                    """,
                    resultId,
                    metric.name(),
                    metric.value(),
                    metric.weight(),
                    metric.explanation(),
                    timestamp(now)
            );
        }
        saveThreshold(resultId, analysis.formulaVersion(), threshold, now);
        for (EvidenceData item : evidence) {
            saveEvidence(resultId, item, now);
        }
        return find(resultId);
    }

    public ResultResponse find(long resultId) {
        List<ResultResponse> matches = jdbc.query(
                baseSelect() + " WHERE ar.id = ?",
                (rs, row) -> mapResult(rs),
                resultId
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    public List<ResultResponse> findByTask(long taskId) {
        return jdbc.query(
                baseSelect() + """
                 WHERE ar.task_id = ?
                 ORDER BY CASE ar.risk_level
                    WHEN 'HIGH' THEN 4 WHEN 'ELEVATED' THEN 3 WHEN 'MEDIUM' THEN 2 ELSE 1 END DESC,
                    ar.risk_margin DESC, ar.weighted_similarity_score DESC
                """,
                (rs, row) -> mapResult(rs),
                taskId
        );
    }

    public List<EvidenceResponse> evidence(long resultId) {
        return jdbc.query(
                """
                SELECT id, result_id, evidence_type, similarity_score, description, evidence_payload
                FROM evidence WHERE result_id = ? ORDER BY confidence DESC, id
                """,
                (rs, row) -> new EvidenceResponse(
                        rs.getLong("id"),
                        rs.getLong("result_id"),
                        safeEvidenceType(rs.getString("evidence_type")),
                        rs.getDouble("similarity_score"),
                        rs.getString("description"),
                        json.readMap(rs.getString("evidence_payload"))
                ),
                resultId
        );
    }

    public List<MetricData> metrics(long resultId) {
        return jdbc.query(
                """
                SELECT metric_name, metric_value, metric_weight, explanation
                FROM similarity_metric WHERE result_id = ? ORDER BY id
                """,
                (rs, row) -> new MetricData(
                        rs.getString("metric_name"),
                        rs.getDouble("metric_value"),
                        rs.getDouble("metric_weight"),
                        rs.getString("explanation")
                ),
                resultId
        );
    }

    public Map<String, Object> threshold(long resultId) {
        List<Map<String, Object>> matches = jdbc.query(
                """
                SELECT base_threshold, difficulty_adjustment, solution_space_adjustment,
                       template_risk_adjustment, natural_similarity_adjustment,
                       historical_distribution_adjustment, final_threshold, formula_version, explanation
                FROM threshold_adjustment WHERE result_id = ?
                """,
                (rs, row) -> {
                    Map<String, Object> value = new LinkedHashMap<>();
                    value.put("baseThreshold", rs.getDouble("base_threshold"));
                    value.put("difficultyAdjustment", rs.getDouble("difficulty_adjustment"));
                    value.put("solutionSpaceAdjustment", rs.getDouble("solution_space_adjustment"));
                    value.put("templateRiskAdjustment", rs.getDouble("template_risk_adjustment"));
                    value.put("naturalSimilarityAdjustment", rs.getDouble("natural_similarity_adjustment"));
                    value.put("historicalDistributionAdjustment", rs.getDouble("historical_distribution_adjustment"));
                    value.put("finalThreshold", rs.getDouble("final_threshold"));
                    value.put("formulaVersion", rs.getString("formula_version"));
                    value.put("explanation", rs.getString("explanation"));
                    return Map.copyOf(value);
                },
                resultId
        );
        return matches.isEmpty() ? Map.of() : matches.getFirst();
    }

    public List<Map<String, Object>> mappings(long resultId) {
        return jdbc.query(
                """
                SELECT mapping_type, name_a, name_b, canonical_name, scope_path,
                       occurrence_a, occurrence_b, confidence
                FROM identifier_mapping WHERE result_id = ? ORDER BY id
                """,
                (rs, row) -> {
                    Map<String, Object> value = new LinkedHashMap<>();
                    value.put("mappingType", rs.getString("mapping_type"));
                    value.put("kind", shortKind(rs.getString("mapping_type")));
                    value.put("submissionAName", rs.getString("name_a"));
                    value.put("submissionBName", rs.getString("name_b"));
                    value.put("canonicalName", rs.getString("canonical_name"));
                    value.put("scopePath", rs.getString("scope_path"));
                    value.put("occurrenceA", rs.getInt("occurrence_a"));
                    value.put("occurrenceB", rs.getInt("occurrence_b"));
                    value.put("confidence", rs.getDouble("confidence"));
                    return Map.copyOf(value);
                },
                resultId
        );
    }

    public long count() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM analysis_result", Long.class);
        return count == null ? 0 : count;
    }

    public long highRiskCount() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM analysis_result WHERE risk_level = 'HIGH'", Long.class);
        return count == null ? 0 : count;
    }

    private ResultResponse mapResult(java.sql.ResultSet rs) throws java.sql.SQLException {
        long resultId = rs.getLong("id");
        long questionId = rs.getLong("question_id");
        Map<String, Double> metricValues = new LinkedHashMap<>();
        for (MetricData metric : metrics(resultId)) {
            metricValues.put(metric.name(), metric.value());
        }
        Map<String, Object> storedProfile = featureRepository.latest(questionId);
        Map<String, Object> profile = storedProfile == null ? new LinkedHashMap<>() : new LinkedHashMap<>(storedProfile);
        profile.remove("thresholdAdjustment");
        return new ResultResponse(
                resultId,
                rs.getLong("task_id"),
                rs.getLong("submission_a_id"),
                rs.getLong("submission_b_id"),
                rs.getString("file_name_a"),
                rs.getString("file_name_b"),
                metricValues.getOrDefault("TOKEN_SIMILARITY", 0.0),
                metricValues.getOrDefault("AST_SIMILARITY", 0.0),
                metricValues.getOrDefault("CANONICAL_TOKEN_SIMILARITY", 0.0),
                metricValues.getOrDefault("IDENTIFIER_MAPPING_SIMILARITY", 0.0),
                rs.getDouble("weighted_similarity_score"),
                rs.getDouble("dynamic_threshold"),
                rs.getDouble("risk_margin"),
                rs.getDouble("calibrated_risk_score"),
                rs.getBoolean("exceed_threshold"),
                rs.getDouble("margin_scale"),
                rs.getString("formula_version"),
                rs.getString("algorithm_version"),
                rs.getString("metric_config_hash"),
                safeRiskLevel(rs.getString("risk_level")),
                Map.copyOf(profile),
                threshold(resultId),
                rs.getString("reason_summary") == null ? "" : rs.getString("reason_summary"),
                rs.getBoolean("is_mock"),
                offset(rs.getTimestamp("created_at"))
        );
    }

    private String baseSelect() {
        return """
                SELECT ar.*, sa.file_name AS file_name_a, sb.file_name AS file_name_b
                FROM analysis_result ar
                JOIN submission sa ON sa.id = ar.submission_a_id
                JOIN submission sb ON sb.id = ar.submission_b_id
                """;
    }

    private void saveThreshold(long resultId, String formulaVersion, Map<String, Object> threshold, OffsetDateTime now) {
        jdbc.update(
                """
                INSERT INTO threshold_adjustment (
                    result_id, base_threshold, difficulty_adjustment, solution_space_adjustment,
                    template_risk_adjustment, natural_similarity_adjustment,
                    historical_distribution_adjustment, final_threshold, formula_version, explanation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                resultId,
                number(threshold, "baseThreshold"),
                number(threshold, "difficultyAdjustment"),
                number(threshold, "solutionSpaceAdjustment"),
                number(threshold, "templateRiskAdjustment"),
                number(threshold, "naturalSimilarityAdjustment"),
                number(threshold, "historicalDistributionAdjustment"),
                number(threshold, "finalThreshold"),
                formulaVersion,
                text(threshold, "explanation"),
                timestamp(now)
        );
    }

    private void saveEvidence(long resultId, EvidenceData item, OffsetDateTime now) {
        Map<String, Object> metadata = item.metadata() == null ? Map.of() : item.metadata();
        Map<String, Object> fragment = firstMap(metadata.get("fragments"));
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("result_id", resultId);
        values.put("evidence_type", safeEvidenceType(item.evidenceType()).name());
        values.put("confidence", item.similarityScore());
        values.put("similarity_score", item.similarityScore());
        values.put("code_a_start_line", integer(fragment, "submissionAStartLine"));
        values.put("code_a_end_line", integer(fragment, "submissionAEndLine"));
        values.put("code_b_start_line", integer(fragment, "submissionBStartLine"));
        values.put("code_b_end_line", integer(fragment, "submissionBEndLine"));
        values.put("title", safeEvidenceType(item.evidenceType()).name());
        values.put("description", item.description());
        values.put("evidence_payload", json.write(metadata));
        values.put("visualizable", metadata.containsKey("fragments") ? 1 : 0);
        values.put("created_at", timestamp(now));
        evidenceInsert.executeAndReturnKey(values);
        if (safeEvidenceType(item.evidenceType()) == EvidenceType.IDENTIFIER_MAPPING) {
            for (Map<String, Object> mapping : mapList(metadata.get("mappings"))) {
                jdbc.update(
                        """
                        INSERT INTO identifier_mapping
                        (result_id, mapping_type, name_a, name_b, canonical_name, scope_path,
                         occurrence_a, occurrence_b, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        resultId,
                        text(mapping, "mappingType"),
                        text(mapping, "submissionAName"),
                        text(mapping, "submissionBName"),
                        text(mapping, "canonicalName"),
                        text(mapping, "scopePath"),
                        integer(mapping, "occurrenceA"),
                        integer(mapping, "occurrenceB"),
                        number(mapping, "confidence"),
                        timestamp(now)
                );
            }
        }
    }

    private List<Map<String, Object>> mapList(Object value) {
        if (!(value instanceof List<?> list)) {
            return List.of();
        }
        List<Map<String, Object>> result = new ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map<?, ?> raw) {
                Map<String, Object> typed = new LinkedHashMap<>();
                raw.forEach((key, nested) -> typed.put(String.valueOf(key), nested));
                result.add(typed);
            }
        }
        return result;
    }

    private Map<String, Object> firstMap(Object value) {
        List<Map<String, Object>> items = mapList(value);
        return items.isEmpty() ? Map.of() : items.getFirst();
    }

    private int integer(Map<String, Object> values, String key) {
        Object value = values.get(key);
        return value instanceof Number number ? number.intValue() : 0;
    }

    private double number(Map<String, Object> values, String key) {
        Object value = values.get(key);
        return value instanceof Number number ? number.doubleValue() : 0.0;
    }

    private String text(Map<String, Object> values, String key) {
        Object value = values.get(key);
        return value == null ? "" : value.toString();
    }

    private RiskLevel safeRiskLevel(String value) {
        try {
            return RiskLevel.valueOf(value);
        } catch (RuntimeException exception) {
            return RiskLevel.LOW;
        }
    }

    private EvidenceType safeEvidenceType(String value) {
        try {
            return EvidenceType.valueOf(value);
        } catch (RuntimeException exception) {
            return EvidenceType.REVIEW_NOTE;
        }
    }

    private String shortKind(String mappingType) {
        return switch (mappingType) {
            case "VARIABLE" -> "VAR";
            case "FUNCTION" -> "FUNC";
            case "PARAMETER" -> "PARAM";
            default -> mappingType;
        };
    }

    private String canonicalMetricName(String value) {
        return switch (value) {
            case "TokenSimilarity" -> "TOKEN_SIMILARITY";
            case "BasicASTStructureSimilarity" -> "AST_SIMILARITY";
            case "CanonicalTokenSimilarity" -> "CANONICAL_TOKEN_SIMILARITY";
            case "IdentifierMappingSimilarity" -> "IDENTIFIER_MAPPING_SIMILARITY";
            default -> value;
        };
    }

    private List<MetricData> completeMetrics(AnalyzeMockResult analysis) {
        Map<String, MetricData> metrics = new LinkedHashMap<>();
        if (analysis.metrics() != null) {
            for (MetricData metric : analysis.metrics()) {
                String name = canonicalMetricName(metric.name());
                metrics.put(name, new MetricData(name, metric.value(), metric.weight(), metric.explanation()));
            }
        }
        metrics.putIfAbsent("TOKEN_SIMILARITY", new MetricData("TOKEN_SIMILARITY", analysis.tokenSimilarity(), 0.0, "Raw token similarity."));
        metrics.putIfAbsent("AST_SIMILARITY", new MetricData("AST_SIMILARITY", analysis.astSimilarity(), 0.0, "Basic AST similarity."));
        metrics.putIfAbsent("CANONICAL_TOKEN_SIMILARITY", new MetricData("CANONICAL_TOKEN_SIMILARITY", analysis.canonicalTokenSimilarity(), 0.0, "Canonical token similarity."));
        metrics.putIfAbsent("IDENTIFIER_MAPPING_SIMILARITY", new MetricData("IDENTIFIER_MAPPING_SIMILARITY", analysis.identifierMappingSimilarity(), 0.0, "Identifier mapping similarity."));
        return List.copyOf(metrics.values());
    }

    private String algorithmVersion(List<MetricData> metrics) {
        boolean hasExperimentalIr = metrics.stream()
                .anyMatch(metric -> "CROSSLANG_IR_SIMILARITY".equals(metric.name()));
        return hasExperimentalIr ? CROSSLANG_ALGORITHM_VERSION : ALGORITHM_VERSION;
    }

    private String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return "sha256:" + HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("SHA-256 unavailable", exception);
        }
    }
}
