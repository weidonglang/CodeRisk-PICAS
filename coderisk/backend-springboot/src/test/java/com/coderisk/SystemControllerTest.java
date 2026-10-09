package com.coderisk;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.not;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.coderisk.integration.analysis.AnalysisClient;
import com.coderisk.integration.analysis.AnalyzeMockResult;
import com.coderisk.integration.analysis.EvidenceData;
import com.coderisk.integration.analysis.MetricData;
import com.coderisk.integration.analysis.ProblemScoreResult;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(properties = {
        "coderisk.upload.root-path=target/test-uploads",
        "coderisk.artifacts.root-path=target/test-artifacts",
        "coderisk.tasks.workers=1", "coderisk.tasks.queue-capacity=1", "coderisk.tasks.time-budget-seconds=1"
})
@AutoConfigureMockMvc
class SystemControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @MockBean
    private AnalysisClient analysisClient;

    @Autowired
    private com.coderisk.task.TaskService taskService;

    @Test
    void healthReturnsUnifiedResponse() throws Exception {
        mockMvc.perform(get("/api/system/health").header("X-Trace-Id", "test-trace"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Trace-Id", "test-trace"))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("OK"))
                .andExpect(jsonPath("$.data.status").value("UP"))
                .andExpect(jsonPath("$.traceId").value("test-trace"));
    }

    @Test
    void languagesExposeStableAndExperimentalSupportLevels() throws Exception {
        mockMvc.perform(get("/api/system/languages"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(5)))
                .andExpect(jsonPath("$.data[0].language").value("java"))
                .andExpect(jsonPath("$.data[0].supportLevel").value("STABLE"))
                .andExpect(jsonPath("$.data[2].language").value("c"))
                .andExpect(jsonPath("$.data[2].supportLevel").value("EXPERIMENTAL"))
                .andExpect(jsonPath("$.data[3].language").value("html"))
                .andExpect(jsonPath("$.data[4].language").value("cpp"));
    }

    @Test
    void taskModesMarkCrossLanguageIrAsExperimental() throws Exception {
        mockMvc.perform(get("/api/system/task-modes"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(6)))
                .andExpect(jsonPath("$.data[3].code").value("PICAS_STANDARD"))
                .andExpect(jsonPath("$.data[3].stable").value(true))
                .andExpect(jsonPath("$.data[4].code").value("PICAS_CROSSLANG"))
                .andExpect(jsonPath("$.data[4].stable").value(false));
    }

    @Test
    void questionsCanBeCreatedAndListedWithUnifiedResponse() throws Exception {
        String body = """
                {
                  "title": "Array Sum",
                  "description": "Read n numbers and output the sum.",
                  "inputFormat": "n followed by n integers",
                  "outputFormat": "sum",
                  "constraintsText": "1 <= n <= 100"
                }
                """;

        mockMvc.perform(post("/api/questions").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.title").value("Array Sum"));

        mockMvc.perform(get("/api/questions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(greaterThanOrEqualTo(1)))
                .andExpect(jsonPath("$.data.items[0].title").value("Array Sum"));
    }

    @Test
    void uploadCreateTaskStartAndQueryResults() throws Exception {
        long questionId = createQuestion("Loop Sum");
        long javaSubmissionId = uploadSubmission(questionId, "alice", "Main.java", "class Main {}");
        long pythonSubmissionId = uploadSubmission(questionId, "bob", "main.py", "print(1)");
        when(analysisClient.analyzePair(any())).thenReturn(new AnalyzeMockResult(
                3001L,
                javaSubmissionId,
                pythonSubmissionId,
                1.0,
                0.0,
                1.0,
                0.0,
                1.0,
                0.80,
                0.20,
                1.0,
                true,
                0.40,
                "FORMULA_SPEC_V1",
                "HIGH",
                Map.of(
                        "featureVersion", "pf-rule-v1.0",
                        "difficultyScore", 0.25,
                        "solutionSpaceScore", 0.20,
                        "templateRiskScore", 0.65,
                        "naturalSimilarityRisk", 0.78,
                        "recommendedBaseThreshold", 0.80
                ),
                Map.of("baseThreshold", 0.68, "finalThreshold", 0.80, "formulaVersion", "FORMULA_SPEC_V1"),
                "相似风险较高，建议人工复核。",
                false,
                List.of(new MetricData("TokenSimilarity", 1.0, 1.0, "token")),
                List.of(new EvidenceData("TOKEN_MATCH", 1.0, "token overlap", Map.of(
                        "isMock", false,
                        "fragments", List.of(Map.of(
                                "tokens", List.of("class", "Main"),
                                "submissionAStartLine", 1,
                                "submissionAEndLine", 1,
                                "submissionBStartLine", 1,
                                "submissionBEndLine", 1
                        ))
                )))
        ));

        String taskBody = """
                {
                  "questionId": %d,
                  "taskName": "Loop Sum Token",
                  "submissionIds": [%d, %d]
                }
                """.formatted(questionId, javaSubmissionId, pythonSubmissionId);
        MvcResult taskResult = mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content(taskBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("PENDING"))
                .andExpect(jsonPath("$.data.totalPairs").value(1))
                .andReturn();
        long taskId = objectMapper.readTree(taskResult.getResponse().getContentAsString()).path("data").path("id").asLong();

        startAndAwait(taskId);

        MvcResult resultsResponse = mockMvc.perform(get("/api/tasks/%d/results".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.items", hasSize(1)))
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.pageSize").value(20))
                .andExpect(jsonPath("$.data.totalPages").value(1))
                .andExpect(jsonPath("$.data.items[0].isMock").value(false))
                .andExpect(jsonPath("$.data.items[0].riskLevel").value("HIGH"))
                .andExpect(jsonPath("$.data.items[0].tokenSimilarity").value(1.0))
                .andExpect(jsonPath("$.data.items[0].canonicalTokenSimilarity").value(1.0))
                .andExpect(jsonPath("$.data.items[0].dynamicThreshold").value(0.80))
                .andExpect(jsonPath("$.data.items[0].riskMargin").value(0.20))
                .andExpect(jsonPath("$.data.items[0].formulaVersion").value("FORMULA_SPEC_V1"))
                .andExpect(jsonPath("$.data.items[0].algorithmVersion").value("picas-v2-rule-1.0"))
                .andExpect(jsonPath("$.data.items[0].metricConfigHash", containsString("sha256:")))
                .andExpect(jsonPath("$.data.items[0].problemProfile.naturalSimilarityRisk").value(0.78))
                .andReturn();
        long resultId = objectMapper.readTree(resultsResponse.getResponse().getContentAsString())
                .path("data").path("items").get(0).path("id").asLong();

        mockMvc.perform(get("/api/tasks/%d/results/summary".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalResults").value(1))
                .andExpect(jsonPath("$.data.containsMockData").value(false));

        mockMvc.perform(get("/api/results/%d/evidence".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(1)))
                .andExpect(jsonPath("$.data[0].evidenceType").value("TOKEN_MATCH"))
                .andExpect(jsonPath("$.data[0].metadata.fragments[0].submissionAStartLine").value(1));

        mockMvc.perform(get("/api/results/%d/metrics".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(4)))
                .andExpect(jsonPath("$.data[0].name").value("TOKEN_SIMILARITY"));

        mockMvc.perform(get("/api/results/%d/threshold-adjustment".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.finalThreshold").value(0.80))
                .andExpect(jsonPath("$.data.formulaVersion").value("FORMULA_SPEC_V1"));

        mockMvc.perform(get("/api/results/%d/identifier-mappings".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(0)));

        mockMvc.perform(get("/api/results/%d/code-pair".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.submissionA.fileName").value("Main.java"))
                .andExpect(jsonPath("$.data.submissionA.code").value("class Main {}"))
                .andExpect(jsonPath("$.data.submissionB.fileName").value("main.py"))
                .andExpect(jsonPath("$.data.submissionB.code").value("print(1)"));

        mockMvc.perform(get("/api/results/%d/diff-view".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.codeA.fileName").value("Main.java"))
                .andExpect(jsonPath("$.data.codeB.fileName").value("main.py"))
                .andExpect(jsonPath("$.data.highlights", hasSize(1)))
                .andExpect(jsonPath("$.data.highlights[0].aRange.startLine").value(1))
                .andExpect(jsonPath("$.data.highlights[0].bRange.startLine").value(1));

        Integer resultRows = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM analysis_result WHERE task_id = ?", Integer.class, taskId);
        Integer metricRows = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM similarity_metric WHERE result_id = ?", Integer.class, resultId);
        Integer evidenceRows = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM evidence WHERE result_id = ?", Integer.class, resultId);
        Integer thresholdRows = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM threshold_adjustment WHERE result_id = ?", Integer.class, resultId);
        org.junit.jupiter.api.Assertions.assertEquals(1, resultRows);
        org.junit.jupiter.api.Assertions.assertEquals(4, metricRows);
        org.junit.jupiter.api.Assertions.assertEquals(1, evidenceRows);
        org.junit.jupiter.api.Assertions.assertEquals(1, thresholdRows);

        String reportBody = """
                {
                  "format": "HTML",
                  "includeLowRiskPairs": true,
                  "includeCodeSnippets": true,
                  "includeThresholdExplanation": true
                }
                """;
        MvcResult reportResult = mockMvc.perform(post("/api/tasks/%d/reports".formatted(taskId))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(reportBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("GENERATED"))
                .andExpect(jsonPath("$.data.format").value("HTML"))
                .andReturn();
        long reportId = objectMapper.readTree(reportResult.getResponse().getContentAsString()).path("data").path("reportId").asLong();

        mockMvc.perform(get("/api/reports/%d/download".formatted(reportId)))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", containsString("text/html")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("CodeRisk / PICAS")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("人工复核建议")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("FORMULA_SPEC_V1")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("picas-v2-rule-1.0")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(not(containsString("确认抄袭"))))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(not(containsString("作弊成立"))))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(not(containsString("证明抄袭"))));
    }

    @Test
    void questionFeatureEndpointReturnsProblemAwareProfile() throws Exception {
        long questionId = createQuestion("Simple Count");
        when(analysisClient.scoreProblem(any())).thenReturn(new ProblemScoreResult(
                questionId,
                Map.of(
                        "featureVersion", "pf-rule-v1.0",
                        "difficultyScore", 0.20,
                        "solutionSpaceScore", 0.18,
                        "templateRiskScore", 0.72,
                        "naturalSimilarityRisk", 0.81,
                        "recommendedBaseThreshold", 0.85
                ),
                Map.of(
                        "baseThreshold", 0.68,
                        "naturalSimilarityAdjustment", 0.0972,
                        "finalThreshold", 0.85,
                        "formulaVersion", "FORMULA_SPEC_V1"
                )
        ));

        mockMvc.perform(post("/api/questions/%d/features/compute".formatted(questionId))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.questionId").value(questionId))
                .andExpect(jsonPath("$.data.naturalSimilarityRisk").value(0.81))
                .andExpect(jsonPath("$.data.recommendedBaseThreshold").value(0.85))
                .andExpect(jsonPath("$.data.thresholdAdjustment.formulaVersion").value("FORMULA_SPEC_V1"));
    }

    @Test
    void crossLanguageIrPersistsAsExperimentalZeroWeightEvidence() throws Exception {
        long questionId = createQuestion("Cross Language Sum");
        long javaId = uploadSubmission(questionId, "java", "Main.java", "class Main { int add(int a,int b){ return a+b; } }");
        long pythonId = uploadSubmission(questionId, "python", "main.py", "def add(a,b):\n    return a+b\n");
        when(analysisClient.analyzePair(any())).thenReturn(new AnalyzeMockResult(
                41L, javaId, pythonId, 0.1, 0.2, 0.3, 0.0,
                0.2, 0.8, -0.6, 0.0, false, 0.4,
                "FORMULA_SPEC_V1", "LOW",
                Map.of("featureVersion", "pf-rule-v1.0", "difficultyScore", 0.5,
                        "solutionSpaceScore", 0.5, "templateRiskScore", 0.5,
                        "naturalSimilarityRisk", 0.5, "recommendedBaseThreshold", 0.8),
                Map.of("baseThreshold", 0.68, "finalThreshold", 0.80,
                        "formulaVersion", "FORMULA_SPEC_V1"),
                "实验性跨语言 IR 仅供人工复核。", false,
                List.of(
                        new MetricData("TOKEN_SIMILARITY", 0.1, 0.2, "token"),
                        new MetricData("AST_SIMILARITY", 0.2, 0.2, "ast"),
                        new MetricData("CANONICAL_TOKEN_SIMILARITY", 0.3, 0.45, "canonical"),
                        new MetricData("IDENTIFIER_MAPPING_SIMILARITY", 0.0, 0.15, "mapping"),
                        new MetricData("CROSSLANG_IR_SIMILARITY", 0.9, 0.0, "experimental"),
                        new MetricData("CROSSLANG_CONTROL_SUMMARY_SIMILARITY", 1.0, 0.0, "experimental summary"),
                        new MetricData("CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY", 0.8, 0.0, "experimental summary")
                ),
                List.of(new EvidenceData("CROSSLANG_IR_MATCH", 0.9, "experimental ir", Map.of(
                        "experimental", true,
                        "includedInWeightedScore", false,
                        "fragments", List.of(Map.of(
                                "nodes", List.of("ASSIGN", "RETURN"),
                                "submissionAStartLine", 1, "submissionAEndLine", 1,
                                "submissionBStartLine", 1, "submissionBEndLine", 2
                        ))
                )))
        ));

        String taskBody = """
                {"questionId": %d, "taskName": "Cross Language", "submissionIds": [%d, %d], "taskMode": "PICAS_CROSSLANG"}
                """.formatted(questionId, javaId, pythonId);
        MvcResult taskResult = mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content(taskBody))
                .andExpect(status().isOk()).andReturn();
        long taskId = objectMapper.readTree(taskResult.getResponse().getContentAsString()).path("data").path("id").asLong();
        startAndAwait(taskId);
        MvcResult resultResponse = mockMvc.perform(get("/api/tasks/%d/results".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.items[0].algorithmVersion").value("picas-v4-xl-ir0.1-sum0.2-exp"))
                .andReturn();
        long resultId = objectMapper.readTree(resultResponse.getResponse().getContentAsString())
                .path("data").path("items").get(0).path("id").asLong();

        mockMvc.perform(get("/api/results/%d/metrics".formatted(resultId)))
                .andExpect(status().isOk()).andExpect(jsonPath("$.data", hasSize(7)))
                .andExpect(jsonPath("$.data[4].name").value("CROSSLANG_IR_SIMILARITY"))
                .andExpect(jsonPath("$.data[4].weight").value(0.0))
                .andExpect(jsonPath("$.data[5].weight").value(0.0))
                .andExpect(jsonPath("$.data[6].weight").value(0.0));
        mockMvc.perform(get("/api/results/%d/evidence".formatted(resultId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0].evidenceType").value("CROSSLANG_IR_MATCH"))
                .andExpect(jsonPath("$.data[0].metadata.experimental").value(true));

        MvcResult report = mockMvc.perform(post("/api/tasks/%d/reports".formatted(taskId))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"format":"HTML","includeLowRiskPairs":true,"includeCodeSnippets":false,"includeThresholdExplanation":true}
                                """))
                .andExpect(status().isOk()).andReturn();
        long reportId = objectMapper.readTree(report.getResponse().getContentAsString()).path("data").path("reportId").asLong();
        mockMvc.perform(get("/api/reports/%d/download".formatted(reportId)))
                .andExpect(status().isOk())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("实验性能力")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("权重均为 0")))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.content().string(containsString("不表示语义等价")));
    }

    @Test
    void resultsUseRiskMarginOrderingAndSupportPaginationAndFiltering() throws Exception {
        long questionId = createQuestion("Ordering Check");
        long first = uploadSubmission(questionId, "one", "one.py", "print(1)");
        long second = uploadSubmission(questionId, "two", "two.py", "print(2)");
        long third = uploadSubmission(questionId, "three", "three.py", "print(3)");
        AtomicInteger call = new AtomicInteger();
        when(analysisClient.analyzePair(any())).thenAnswer(invocation -> {
            com.coderisk.integration.analysis.AnalyzeMockRequest request = invocation.getArgument(0);
            double[] weighted = {0.75, 0.85, 0.95};
            double score = weighted[call.getAndIncrement()];
            double margin = score - 0.80;
            String level = margin >= 0.10 ? "HIGH" : margin >= 0 ? "ELEVATED" : margin >= -0.10 ? "MEDIUM" : "LOW";
            return new AnalyzeMockResult(
                    request.taskId(), request.submissionA().id(), request.submissionB().id(),
                    score, score, score, score, score, 0.80, margin,
                    Math.max(0, Math.min(1, 0.5 + margin / 0.40)), margin >= 0, 0.40,
                    "FORMULA_SPEC_V1", level,
                    Map.of("featureVersion", "pf-rule-v1.0", "difficultyScore", 0.5,
                            "solutionSpaceScore", 0.5, "templateRiskScore", 0.5,
                            "naturalSimilarityRisk", 0.5, "recommendedBaseThreshold", 0.8),
                    Map.of("baseThreshold", 0.68, "finalThreshold", 0.80,
                            "formulaVersion", "FORMULA_SPEC_V1"),
                    "相似风险排序测试。", false, List.of(), List.of()
            );
        });

        String taskBody = """
                {"questionId": %d, "taskName": "Ordering", "submissionIds": [%d, %d, %d], "taskMode": "PICAS_STANDARD"}
                """.formatted(questionId, first, second, third);
        MvcResult taskResult = mockMvc.perform(post("/api/tasks")
                        .contentType(MediaType.APPLICATION_JSON).content(taskBody))
                .andExpect(status().isOk()).andReturn();
        long taskId = objectMapper.readTree(taskResult.getResponse().getContentAsString()).path("data").path("id").asLong();
        startAndAwait(taskId);

        mockMvc.perform(get("/api/tasks/%d/results?page=1&pageSize=1".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(3))
                .andExpect(jsonPath("$.data.totalPages").value(3))
                .andExpect(jsonPath("$.data.items[0].riskLevel").value("HIGH"));
        mockMvc.perform(get("/api/tasks/%d/results?page=2&pageSize=1".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.items[0].riskLevel").value("ELEVATED"));
        mockMvc.perform(get("/api/tasks/%d/results?riskLevel=MEDIUM".formatted(taskId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.items[0].riskMargin").value(-0.05));
    }

    @Test
    void htmlCUploadsExposeCorrectLanguageAndMixedDomainsAreRejected() throws Exception {
        long questionId = createQuestion("HTML source comparison");
        long htmlId = uploadSubmission(questionId, "html-student", "index.HTML", "<div>Hello</div>");
        uploadSubmission(questionId, "second-html", "other.htm", "<p>Hello</p>");
        long cId = uploadSubmission(questionId, "c-student", "main.c", "int main(){return 0;}");
        uploadSubmission(questionId, "cpp-student", "main.cpp", "class Main {};");
        mockMvc.perform(get("/api/questions/%d/submissions".formatted(questionId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0].language").value("cpp"))
                .andExpect(jsonPath("$.data[1].language").value("c"))
                .andExpect(jsonPath("$.data[2].language").value("html"))
                .andExpect(jsonPath("$.data[3].language").value("html"));
        String body = """
                {"questionId": %d, "submissionIds": [%d, %d], "taskMode": "PICAS_STANDARD"}
                """.formatted(questionId, htmlId, cId);
        mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("TASK_LANGUAGE_DOMAIN_MISMATCH"));
    }

    @Test
    void htmlTaskPreservesDomainMetadataAndExportsFixedThresholdReport() throws Exception {
        long questionId = createQuestion("HTML report");
        long first = uploadSubmission(questionId, "first", "first.html", "<div>Safe</div>");
        long second = uploadSubmission(questionId, "second", "second.htm", "<div>Safe</div>");
        // Analysis is stubbed to test persistence and report contracts; not an experiment score.
        when(analysisClient.analyzePair(any())).thenAnswer(invocation -> {
            com.coderisk.integration.analysis.AnalyzeMockRequest request = invocation.getArgument(0);
            return new AnalyzeMockResult(request.taskId(), first, second,
                    1, 1, 1, 0, 1, 0.85, 0.15, 0.875, true, 0.40,
                    "HTML_STRUCTURE_FIXED_V1", "HIGH", Map.of("domain", "html", "confidence", 0),
                    Map.of("policy", "FIXED_UNCALIBRATED", "finalThreshold", 0.85),
                    "HTML source comparison", false, List.of(), List.of());
        });
        MvcResult created = mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"questionId\":%d,\"submissionIds\":[%d,%d],\"taskMode\":\"PICAS_STANDARD\"}".formatted(questionId, first, second)))
                .andExpect(status().isOk()).andReturn();
        long taskId = objectMapper.readTree(created.getResponse().getContentAsString()).path("data").path("id").asLong();
        startAndAwait(taskId);
        mockMvc.perform(get("/api/tasks/%d/results".formatted(taskId)))
                .andExpect(jsonPath("$.data.items[0].problemProfile.domain").value("html"))
                .andExpect(jsonPath("$.data.items[0].thresholdAdjustment.policy").value("FIXED_UNCALIBRATED"));
        MvcResult report = mockMvc.perform(post("/api/tasks/%d/reports".formatted(taskId))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"format\":\"HTML\",\"includeLowRiskPairs\":true,\"includeThresholdExplanation\":true}"))
                .andExpect(status().isOk()).andReturn();
        long reportId = objectMapper.readTree(report.getResponse().getContentAsString()).path("data").path("reportId").asLong();
        String exported = mockMvc.perform(get("/api/reports/%d/download".formatted(reportId)))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        org.junit.jupiter.api.Assertions.assertTrue(exported.contains("固定阈值（待验证）"));
        org.junit.jupiter.api.Assertions.assertFalse(exported.contains("<h3>题目画像</h3>"));
    }

    @Test
    void reviewContextPersistsAndReachesAnalysisAndExport() throws Exception {
        String starter = "left=float(input())\nright=float(input())\n# CODERISK_STUDENT_CODE\n";
        String source = "synthetic teacher fixture <script>alert(1)</script>";
        String body = objectMapper.writeValueAsString(Map.of("title", "Calculator Context", "description", "synthetic fixture",
                "starterLanguage", "python", "starterCode", starter, "starterSource", source));
        MvcResult created = mockMvc.perform(post("/api/questions").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk()).andExpect(jsonPath("$.data.starterCode").value(starter)).andReturn();
        long questionId = objectMapper.readTree(created.getResponse().getContentAsString()).path("data").path("id").asLong();
        mockMvc.perform(get("/api/questions/" + questionId)).andExpect(jsonPath("$.data.starterSource").value(source));
        MockMultipartFile file = new MockMultipartFile("file", "calculator.py", "text/plain", "print(5/2)".getBytes());
        MvcResult uploaded = mockMvc.perform(multipart("/api/questions/%d/submissions/upload".formatted(questionId))
                        .file(file).param("studentId", "context-a").param("languageVersion", "Python 2.7"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.data.languageVersion").value("Python 2.7")).andReturn();
        long left = objectMapper.readTree(uploaded.getResponse().getContentAsString()).path("data").path("id").asLong();
        long right = uploadSubmission(questionId, "context-b", "calculator.py", "print(5/2)");
        MvcResult listed = mockMvc.perform(get("/api/questions/%d/submissions".formatted(questionId))).andExpect(status().isOk()).andReturn();
        boolean versionFound = false;
        for (JsonNode row : objectMapper.readTree(listed.getResponse().getContentAsString()).path("data")) {
            if (row.path("id").asLong() == left) {
                org.junit.jupiter.api.Assertions.assertEquals("Python 2.7", row.path("languageVersion").asText());
                versionFound = true;
            }
        }
        org.junit.jupiter.api.Assertions.assertTrue(versionFound);
        when(analysisClient.analyzePair(any())).thenAnswer(invocation -> {
            var request = (com.coderisk.integration.analysis.AnalyzeMockRequest) invocation.getArgument(0);
            org.junit.jupiter.api.Assertions.assertEquals(starter, request.question().starterCode());
            org.junit.jupiter.api.Assertions.assertEquals(source, request.question().starterSource());
            org.junit.jupiter.api.Assertions.assertEquals("Python 2.7", request.submissionA().languageVersion());
            org.junit.jupiter.api.Assertions.assertEquals("", request.submissionB().languageVersion());
            return new AnalyzeMockResult(request.taskId(), left, right, 1.0, 1.0, 1.0, 1.0, 1.0, .8, .2, 1.0, true, .4,
                    "FORMULA_SPEC_V1", "HIGH", Map.of(), Map.of(), "相似风险，需复核", false, List.of(),
                    List.of(new EvidenceData("REVIEW_NOTE", 0.0, "依据不足", Map.of("category", "REVIEW_ASSESSMENT",
                            "status", "INSUFFICIENT_DISTINGUISHING_EVIDENCE", "message", "依据不足 <script>alert(1)</script>")),
                            new EvidenceData("REVIEW_NOTE", 0.0, "版本声明", Map.of("category", "LANGUAGE_COMPATIBILITY",
                                    "submissionA", Map.of("declaredVersion", "Python 2.7"))),
                            new EvidenceData("REVIEW_NOTE", 0.0, "共同模板", Map.of("category", "SHARED_TEMPLATE_CONTEXT", "sourceReference", source))));
        });
        String taskBody = objectMapper.writeValueAsString(Map.of("questionId", questionId, "submissionIds", List.of(left, right)));
        MvcResult task = mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content(taskBody))
                .andExpect(status().isOk()).andReturn();
        long taskId = objectMapper.readTree(task.getResponse().getContentAsString()).path("data").path("id").asLong();
        startAndAwait(taskId);
        MvcResult results = mockMvc.perform(get("/api/tasks/%d/results".formatted(taskId))).andReturn();
        long resultId = objectMapper.readTree(results.getResponse().getContentAsString()).path("data").path("items").get(0).path("id").asLong();
        mockMvc.perform(get("/api/results/%d/evidence".formatted(resultId)))
                .andExpect(jsonPath("$.data[0].metadata.status").value("INSUFFICIENT_DISTINGUISHING_EVIDENCE"));
        MvcResult report = mockMvc.perform(post("/api/tasks/%d/reports".formatted(taskId)).contentType(MediaType.APPLICATION_JSON)
                .content("{\"format\":\"HTML\",\"includeCodeSnippets\":false}"))
                .andExpect(status().isOk()).andReturn();
        long reportId = objectMapper.readTree(report.getResponse().getContentAsString()).path("data").path("reportId").asLong();
        String exported = mockMvc.perform(get("/api/reports/%d/download".formatted(reportId))).andReturn()
                .getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        org.junit.jupiter.api.Assertions.assertTrue(exported.contains("可区分依据与复核限制"));
        org.junit.jupiter.api.Assertions.assertTrue(exported.contains("Python 2.7"));
        org.junit.jupiter.api.Assertions.assertTrue(exported.contains("&lt;script&gt;"));
        org.junit.jupiter.api.Assertions.assertFalse(exported.contains("<script>"));
    }

    @Test
    void invalidReviewContextIsRejectedBeforeStorage() throws Exception {
        mockMvc.perform(post("/api/questions").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"bad starter\",\"starterLanguage\":\"python\",\"starterCode\":\"print(1)\"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("STARTER_CONTEXT_INVALID"));
        long questionId = createQuestion("Bad version");
        MockMultipartFile file = new MockMultipartFile("file", "main.py", "text/plain", "print(1)".getBytes());
        mockMvc.perform(multipart("/api/questions/%d/submissions/upload".formatted(questionId)).file(file)
                        .param("languageVersion", "3.12\nnot a version"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("LANGUAGE_VERSION_INVALID"));
        mockMvc.perform(get("/api/questions/%d/submissions".formatted(questionId))).andExpect(jsonPath("$.data", hasSize(0)));
    }


    private JsonNode startAndAwait(long taskId) throws Exception {
        mockMvc.perform(post("/api/tasks/%d/start".formatted(taskId))).andExpect(status().isOk());
        return awaitTerminal(taskId);
    }

    private JsonNode awaitTerminal(long taskId) throws Exception {
        long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(10);
        while (System.nanoTime() < deadline) {
            JsonNode task = objectMapper.readTree(mockMvc.perform(get("/api/tasks/" + taskId))
                    .andExpect(status().isOk()).andReturn().getResponse().getContentAsString()).path("data");
            if (List.of("FINISHED", "FAILED", "PARTIAL").contains(task.path("status").asText())) return task;
            Thread.sleep(20);
        }
        throw new AssertionError("Task did not finish: " + taskId);
    }

    private long taskFor(long questionId, List<Long> ids) throws Exception {
        String body = objectMapper.writeValueAsString(Map.of("questionId", questionId, "submissionIds", ids));
        return objectMapper.readTree(mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString()).path("data").path("id").asLong();
    }

    private AnalyzeMockResult executionFixture(com.coderisk.integration.analysis.AnalyzeMockRequest req) {
        return new AnalyzeMockResult(req.taskId(), req.submissionA().id(), req.submissionB().id(),
                .2, .2, .2, .2, .2, .68, -.48, 0, false, .2, "test", "LOW", Map.of(), Map.of(),
                "Synthetic task execution fixture", true, List.of(), List.of());
    }

    @Test
    void asyncStartIsIdempotentAndCapacityIsBounded() throws Exception {
        long q = createQuestion("Async synthetic");
        long a = uploadSubmission(q, "a", "a.py", "print(1)");
        long b = uploadSubmission(q, "b", "b.py", "print(2)");
        long first = taskFor(q, List.of(a,b)), queued = taskFor(q, List.of(a,b)), excess = taskFor(q, List.of(a,b));
        var entered = new java.util.concurrent.CountDownLatch(1);
        var release = new java.util.concurrent.CountDownLatch(1);
        AtomicInteger calls = new AtomicInteger();
        when(analysisClient.analyzePair(any())).thenAnswer(inv -> {
            calls.incrementAndGet(); entered.countDown();
            if (!release.await(5, java.util.concurrent.TimeUnit.SECONDS)) throw new IllegalStateException("Fixture release timeout");
            return executionFixture(inv.getArgument(0));
        });
        try {
            mockMvc.perform(post("/api/tasks/" + first + "/start")).andExpect(status().isOk()).andExpect(jsonPath("$.data.status").value("RUNNING"));
            org.junit.jupiter.api.Assertions.assertTrue(entered.await(2, java.util.concurrent.TimeUnit.SECONDS));
            mockMvc.perform(post("/api/tasks/" + first + "/start")).andExpect(status().isOk());
            mockMvc.perform(post("/api/tasks/" + queued + "/start")).andExpect(status().isOk());
            mockMvc.perform(post("/api/tasks/" + excess + "/start")).andExpect(status().isServiceUnavailable()).andExpect(jsonPath("$.code").value("TASK_CAPACITY_EXCEEDED"));
            mockMvc.perform(get("/api/tasks/" + excess)).andExpect(jsonPath("$.data.status").value("PENDING"));
        } finally { release.countDown(); awaitTerminal(first); awaitTerminal(queued); }
        mockMvc.perform(post("/api/tasks/" + first + "/start")).andExpect(jsonPath("$.data.status").value("FINISHED"));
        org.junit.jupiter.api.Assertions.assertEquals(2, calls.get());
    }

    @Test
    void partialRetryPreservesResultsAndResolvesFailureHistory() throws Exception {
        long q = createQuestion("Retry synthetic");
        long a = uploadSubmission(q, "a", "a.py", "print(1)");
        long b = uploadSubmission(q, "b", "b.py", "print(2)");
        long c = uploadSubmission(q, "c", "c.py", "print(3)");
        long t = taskFor(q, List.of(c,a,b));
        var fail = new java.util.concurrent.atomic.AtomicBoolean(true);
        var calls = new java.util.concurrent.ConcurrentHashMap<String, AtomicInteger>();
        when(analysisClient.analyzePair(any())).thenAnswer(inv -> {
            com.coderisk.integration.analysis.AnalyzeMockRequest req = inv.getArgument(0);
            String key = req.submissionA().id() + ":" + req.submissionB().id();
            calls.computeIfAbsent(key, k -> new AtomicInteger()).incrementAndGet();
            if (req.submissionA().id() == a && req.submissionB().id() == b && fail.get()) throw new IllegalStateException("Synthetic timeout");
            return executionFixture(req);
        });
        JsonNode partial = startAndAwait(t);
        org.junit.jupiter.api.Assertions.assertEquals("PARTIAL", partial.path("status").asText());
        org.junit.jupiter.api.Assertions.assertEquals(2, partial.path("finishedPairs").asInt());
        org.junit.jupiter.api.Assertions.assertEquals(1, partial.path("failedPairs").asInt());
        mockMvc.perform(get("/api/tasks/" + t + "/failures")).andExpect(jsonPath("$.data", hasSize(1))).andExpect(jsonPath("$.data[0].resolved").value(false));
        MvcResult report = mockMvc.perform(post("/api/tasks/" + t + "/reports").contentType(MediaType.APPLICATION_JSON)
                .content("{\"format\":\"HTML\",\"includeLowRiskPairs\":true}" )).andExpect(status().isOk()).andReturn();
        long reportId = objectMapper.readTree(report.getResponse().getContentAsString()).path("data").path("reportId").asLong();
        String partialHtml = mockMvc.perform(get("/api/reports/" + reportId + "/download")).andReturn()
                .getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        org.junit.jupiter.api.Assertions.assertTrue(partialHtml.contains("本报告只包含生成时已成功的代码对"));
        org.junit.jupiter.api.Assertions.assertTrue(partialHtml.contains("PARTIAL"));
        startAndAwait(t);
        mockMvc.perform(get("/api/tasks/" + t + "/failures")).andExpect(jsonPath("$.data[0].attempts").value(2));
        // Simulate persisted RUNNING state after a process crash; no live worker remains.
        jdbcTemplate.update("UPDATE detection_task SET status='RUNNING', finished_pairs=0, progress=0 WHERE id=?", t);
        taskService.recoverInterruptedTasks();
        mockMvc.perform(get("/api/tasks/" + t)).andExpect(jsonPath("$.data.status").value("PARTIAL"));
        mockMvc.perform(get("/api/tasks/" + t)).andExpect(jsonPath("$.data.finishedPairs").value(2));
        fail.set(false);
        JsonNode done = startAndAwait(t);
        org.junit.jupiter.api.Assertions.assertEquals("FINISHED", done.path("status").asText());
        org.junit.jupiter.api.Assertions.assertEquals(3, done.path("finishedPairs").asInt());
        org.junit.jupiter.api.Assertions.assertEquals(0, done.path("failedPairs").asInt());
        org.junit.jupiter.api.Assertions.assertEquals(1.0, done.path("progress").asDouble());
        mockMvc.perform(get("/api/tasks/" + t + "/failures")).andExpect(jsonPath("$.data[0].resolved").value(true));
        org.junit.jupiter.api.Assertions.assertEquals(3, calls.get(a + ":" + b).get());
        org.junit.jupiter.api.Assertions.assertEquals(1, calls.get(a + ":" + c).get());
        org.junit.jupiter.api.Assertions.assertEquals(1, calls.get(b + ":" + c).get());
    }

    @Test
    void taskBudgetStopsNewPairsAndRetryResumesDurableResults() throws Exception {
        long q = createQuestion("Time budget synthetic");
        long a = uploadSubmission(q, "a", "a.py", "print(1)");
        long b = uploadSubmission(q, "b", "b.py", "print(2)");
        long c = uploadSubmission(q, "c", "c.py", "print(3)");
        long task = taskFor(q, List.of(a,b,c));
        AtomicInteger calls = new AtomicInteger();
        when(analysisClient.analyzePair(any())).thenAnswer(inv -> {
            if (calls.incrementAndGet() == 1) Thread.sleep(1100);
            return executionFixture(inv.getArgument(0));
        });
        JsonNode stopped = startAndAwait(task);
        org.junit.jupiter.api.Assertions.assertEquals("PARTIAL", stopped.path("status").asText());
        org.junit.jupiter.api.Assertions.assertEquals(1, stopped.path("finishedPairs").asInt());
        org.junit.jupiter.api.Assertions.assertTrue(stopped.path("failureReason").asText().contains("TASK_TIME_BUDGET_EXCEEDED"));
        org.junit.jupiter.api.Assertions.assertEquals("FINISHED", startAndAwait(task).path("status").asText());
        org.junit.jupiter.api.Assertions.assertEquals(3, calls.get());
    }

    @Test
    void duplicateIdsAndOversizedTasksAreRejected() throws Exception {
        long q = createQuestion("Limits synthetic");
        long a = uploadSubmission(q, "a", "a.py", "print(1)");
        for (var entry : Map.of("TASK_DUPLICATE_SUBMISSION", List.of(a,a),
                "TASK_TOO_MANY_SUBMISSIONS", java.util.Collections.nCopies(101,a)).entrySet()) {
            mockMvc.perform(post("/api/tasks").contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(Map.of("questionId", q, "submissionIds", entry.getValue()))))
                    .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value(entry.getKey()));
        }
    }

    private long createQuestion(String title) throws Exception {
        String body = """
                {
                  "title": "%s",
                  "description": "Read numbers and output the sum.",
                  "inputFormat": "numbers",
                  "outputFormat": "sum",
                  "constraintsText": "small demo"
                }
                """.formatted(title);
        MvcResult result = mockMvc.perform(post("/api/questions").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk())
                .andReturn();
        JsonNode root = objectMapper.readTree(result.getResponse().getContentAsString());
        return root.path("data").path("id").asLong();
    }

    private long uploadSubmission(long questionId, String studentId, String fileName, String code) throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                fileName,
                MediaType.TEXT_PLAIN_VALUE,
                code.getBytes()
        );
        MvcResult result = mockMvc.perform(multipart("/api/questions/%d/submissions/upload".formatted(questionId))
                        .file(file)
                        .param("studentId", studentId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.fileName").value(fileName))
                .andReturn();
        JsonNode root = objectMapper.readTree(result.getResponse().getContentAsString());
        return root.path("data").path("id").asLong();
    }
}
