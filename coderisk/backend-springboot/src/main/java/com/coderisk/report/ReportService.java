package com.coderisk.report;

import com.coderisk.common.config.CoderiskProperties;
import com.coderisk.common.enums.RiskLevel;
import com.coderisk.common.enums.EvidenceType;
import com.coderisk.common.exception.ApiException;
import com.coderisk.integration.analysis.MetricData;
import com.coderisk.question.QuestionResponse;
import com.coderisk.question.QuestionService;
import com.coderisk.result.CodePairResponse;
import com.coderisk.result.EvidenceResponse;
import com.coderisk.result.ResultResponse;
import com.coderisk.result.ResultService;
import com.coderisk.task.DetectionTaskResponse;
import com.coderisk.task.TaskService;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class ReportService {

    private final TaskService taskService;
    private final QuestionService questionService;
    private final ResultService resultService;
    private final ReportRepository repository;
    private final Path artifactRoot;

    public ReportService(
            TaskService taskService,
            QuestionService questionService,
            ResultService resultService,
            ReportRepository repository,
            CoderiskProperties properties
    ) {
        this.taskService = taskService;
        this.questionService = questionService;
        this.resultService = resultService;
        this.repository = repository;
        this.artifactRoot = Path.of(properties.artifacts().rootPath()).toAbsolutePath().normalize();
    }

    public ReportResponse generate(long taskId, ReportCreateRequest request) {
        DetectionTaskResponse task = taskService.get(taskId);
        if (!"HTML".equalsIgnoreCase(request.format())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "REPORT_FORMAT_NOT_SUPPORTED", "V2 report export supports HTML");
        }
        QuestionResponse question = questionService.get(task.questionId());
        List<ResultResponse> results = taskService.results(taskId).stream()
                .filter(result -> request.includeLowRiskPairs() || result.riskLevel() != RiskLevel.LOW)
                .toList();
        String html = renderHtml(task, question, results, request);
        String timestamp = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss").format(OffsetDateTime.now());
        String fileName = "task-" + taskId + "-risk-report-" + timestamp + ".html";
        Path directory = artifactRoot.resolve("reports").resolve("task-" + taskId).normalize();
        Path target = directory.resolve(fileName).normalize();
        if (!target.startsWith(artifactRoot)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "REPORT_PATH_INVALID", "Report path escapes artifact root");
        }
        try {
            Files.createDirectories(directory);
            Files.writeString(target, html, StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "REPORT_GENERATION_FAILED", "Failed to write report artifact");
        }
        ReportFile saved = repository.save(
                taskId,
                "HTML",
                fileName,
                target.toString().replace('\\', '/'),
                sha256(html)
        );
        return response(saved);
    }

    public List<ReportResponse> list(long taskId) {
        taskService.get(taskId);
        return repository.findByTask(taskId).stream().map(this::response).toList();
    }

    public ReportFile get(long reportId) {
        ReportFile report = repository.find(reportId);
        if (report == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "REPORT_NOT_FOUND", "Report not found: " + reportId);
        }
        return report;
    }

    public FileSystemResource resource(long reportId) {
        ReportFile report = get(reportId);
        Path path = Path.of(report.filePath()).toAbsolutePath().normalize();
        if (!path.startsWith(artifactRoot) || !Files.isRegularFile(path)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "REPORT_FILE_NOT_FOUND", "Report artifact is missing");
        }
        return new FileSystemResource(path);
    }

    private String renderHtml(
            DetectionTaskResponse task,
            QuestionResponse question,
            List<ResultResponse> results,
            ReportCreateRequest request
    ) {
        StringBuilder html = new StringBuilder();
        html.append("""
                <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>CodeRisk 相似风险报告</title><style>
                body{font-family:Arial,"Microsoft YaHei",sans-serif;color:#18231f;margin:0;background:#f4f7f6}
                main{max-width:1080px;margin:auto;padding:28px}.band{background:#fff;border:1px solid #dce5e1;padding:20px;margin:14px 0}
                h1,h2,h3{margin-top:0}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:9px;border:1px solid #dce5e1;text-align:left;vertical-align:top}
                th{background:#eef4f1}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f7faf9;padding:12px;border:1px solid #e1e9e6}
                .notice{border-left:4px solid #b7791f;background:#fff8e8;padding:14px}.experimental{border-left:4px solid #7c3aed;background:#f5f1ff;padding:14px;margin-top:10px}.muted{color:#60716b}.pair{page-break-inside:avoid}
                </style></head><body><main>
                """);
        html.append("<h1>CodeRisk / PICAS 相似风险报告</h1>");
        html.append("<div class=notice>本报告仅提供相似风险指标、结构化证据与人工复核建议，不直接作出纪律结论。</div>");
        if ("PICAS_CROSSLANG".equals(task.taskMode().name())) {
            html.append("<div class=experimental><strong>实验性能力：</strong>跨语言 normalized IR 与轻量控制/数据流摘要仅支持有限 Java/Python 结构，权重均为 0，不构建完整 CFG/DFG，不进入 PICAS_STANDARD，也不表示语义等价。</div>");
        }
        html.append("<section class=band><h2>题目与任务</h2><table>");
        row(html, "题目", question.title());
        row(html, "题目描述", question.description());
        row(html, "输入格式", question.inputFormat());
        row(html, "输出格式", question.outputFormat());
        row(html, "约束", question.constraintsText());
        row(html, "任务", task.taskName());
        row(html, "模式", task.taskMode().name());
        row(html, "生成时间", OffsetDateTime.now().toString());
        html.append("</table></section>");
        for (ResultResponse result : results) {
            renderResult(html, result, request);
        }
        html.append("<p class=muted>人工复核建议：结合课程要求、独立实现可能性、题目模板化程度及证据片段综合判断。</p>");
        html.append("</main></body></html>");
        return html.toString();
    }

    private void renderResult(StringBuilder html, ResultResponse result, ReportCreateRequest request) {
        boolean htmlSource = "HTML_STRUCTURE_FIXED_V1".equals(result.formulaVersion());
        html.append("<section class=\"band pair\"><h2>代码对：")
                .append(escape(result.submissionAFileName())).append(" / ")
                .append(escape(result.submissionBFileName())).append("</h2>");
        html.append("<table><tr><th>综合分</th><th>")
                .append(htmlSource ? "固定阈值（待验证）" : "动态阈值")
                .append("</th><th>风险边际</th><th>校准分</th><th>超过阈值</th><th>风险等级</th></tr><tr>")
                .append(cell(percent(result.weightedSimilarityScore())))
                .append(cell(percent(result.dynamicThreshold())))
                .append(cell(String.format("%+.4f", result.riskMargin())))
                .append(cell(percent(result.calibratedRiskScore())))
                .append(cell(result.exceedThreshold() ? "是" : "否"))
                .append(cell(result.riskLevel().name())).append("</tr></table>");
        html.append("<table><tr><th>公式版本</th><td>").append(escape(result.formulaVersion()))
                .append("</td><th>算法版本</th><td>").append(escape(result.algorithmVersion()))
                .append("</td><th>指标配置哈希</th><td>").append(escape(result.metricConfigHash()))
                .append("</td></tr></table>");
        html.append("<p>").append(escape(result.reasonSummary())).append("</p>");
        for (EvidenceResponse context : resultService.evidenceForResult(result.id())) {
            String category = String.valueOf(context.metadata().get("category"));
            if (category.equals("REVIEW_ASSESSMENT")) {
                html.append("<div class=experimental><strong>可区分依据与复核限制：</strong>")
                        .append(escape(String.valueOf(context.metadata().get("message"))))
                        .append("（不改变原始分数，规则尚未校准）</div>");
            }
            if (List.of("LANGUAGE_COMPATIBILITY", "SHARED_TEMPLATE_CONTEXT", "REVIEW_ASSESSMENT").contains(category)) {
                html.append("<h3>").append(escape(category)).append("</h3><table>");
                context.metadata().forEach((key, value) -> row(html, key, String.valueOf(value)));
                html.append("</table>");
            }
        }

        if (htmlSource) {
            html.append("<div class=experimental>HTML 源码结构检测为实验功能，固定阈值尚未通过标注数据校准；共同模板需人工复核。嵌入脚本和样式仅作为文本，不执行页面或脚本。</div>");
        } else {
        html.append("<h3>题目画像</h3><table>");
        profileRow(html, result.problemProfile(), "difficultyScore", "DifficultyScore");
        profileRow(html, result.problemProfile(), "solutionSpaceScore", "SolutionSpaceScore");
        profileRow(html, result.problemProfile(), "templateRiskScore", "TemplateRiskScore");
        profileRow(html, result.problemProfile(), "naturalSimilarityRisk", "NaturalSimilarityRisk");
        html.append("</table>");
        }

        html.append("<h3>多维指标</h3><table><tr><th>指标</th><th>值</th><th>权重</th><th>说明</th></tr>");
        for (MetricData metric : resultService.metricsForResult(result.id())) {
            String metricName = metric.name().startsWith("CROSSLANG_")
                    ? metric.name() + "（实验性）"
                    : metric.name();
            html.append("<tr>").append(cell(metricName)).append(cell(percent(metric.value())))
                    .append(cell(percent(metric.weight()))).append(cell(metric.explanation())).append("</tr>");
        }
        html.append("</table>");

        if (request.includeThresholdExplanation()) {
            html.append(htmlSource ? "<h3>固定阈值说明</h3><table>" : "<h3>动态阈值解释</h3><table>");
            result.thresholdAdjustment().forEach((key, value) -> row(html, key, String.valueOf(value)));
            html.append("</table>");
        }

        List<Map<String, Object>> mappings = resultService.identifierMappings(result.id());
        html.append("<h3>Identifier mappings</h3><table><tr><th>类型</th><th>A</th><th>B</th><th>Canonical</th><th>置信度</th></tr>");
        for (Map<String, Object> mapping : mappings) {
            html.append("<tr>").append(cell(value(mapping, "mappingType")))
                    .append(cell(value(mapping, "submissionAName")))
                    .append(cell(value(mapping, "submissionBName")))
                    .append(cell(value(mapping, "canonicalName")))
                    .append(cell(value(mapping, "confidence"))).append("</tr>");
        }
        html.append("</table>");

        html.append("<h3>结构化证据</h3><table><tr><th>类型</th><th>分数</th><th>说明</th></tr>");
        for (EvidenceResponse evidence : resultService.evidenceForResult(result.id())) {
            html.append("<tr>").append(cell(evidence.evidenceType().name()))
                    .append(cell(evidence.evidenceType() == EvidenceType.REVIEW_NOTE || evidence.evidenceType() == EvidenceType.PARSER_WARNING ? "—" : percent(evidence.similarityScore())))
                    .append(cell(evidence.description())).append("</tr>");
        }
        html.append("</table>");

        if (request.includeCodeSnippets()) {
            CodePairResponse pair = resultService.codePair(result.id());
            html.append("<h3>代码片段 A</h3><pre>").append(escape(pair.submissionA().code())).append("</pre>");
            html.append("<h3>代码片段 B</h3><pre>").append(escape(pair.submissionB().code())).append("</pre>");
        }
        html.append("</section>");
    }

    private void profileRow(StringBuilder html, Map<String, Object> profile, String key, String label) {
        Object value = profile.get(key);
        row(html, label, value instanceof Number number ? percent(number.doubleValue()) : "-");
    }

    private void row(StringBuilder html, String label, String value) {
        html.append("<tr><th>").append(escape(label)).append("</th><td>")
                .append(escape(value == null ? "" : value)).append("</td></tr>");
    }

    private String cell(String value) {
        return "<td>" + escape(value == null ? "" : value) + "</td>";
    }

    private String value(Map<String, Object> map, String key) {
        Object value = map.get(key);
        return value == null ? "" : value.toString();
    }

    private String percent(double value) {
        return String.format("%.2f%%", value * 100.0);
    }

    private String escape(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }

    private String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return "sha256:" + HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("SHA-256 unavailable", exception);
        }
    }

    private ReportResponse response(ReportFile report) {
        return new ReportResponse(
                report.id(),
                report.taskId(),
                report.status(),
                report.format(),
                report.fileName(),
                "/api/reports/" + report.id() + "/download",
                report.createdAt()
        );
    }
}
