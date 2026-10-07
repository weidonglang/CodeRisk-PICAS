package com.coderisk.report;

import static com.coderisk.persistence.JdbcTimes.offset;
import static com.coderisk.persistence.JdbcTimes.timestamp;

import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.stereotype.Repository;

@Repository
public class ReportRepository {

    private final JdbcTemplate jdbc;
    private final SimpleJdbcInsert insert;

    public ReportRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
        this.insert = new SimpleJdbcInsert(jdbc)
                .withTableName("report_file")
                .usingGeneratedKeyColumns("id");
    }

    public ReportFile save(long taskId, String format, String fileName, String filePath, String fileHash) {
        OffsetDateTime now = OffsetDateTime.now();
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("task_id", taskId);
        values.put("report_type", "DETECTION_REPORT");
        values.put("report_status", "GENERATED");
        values.put("file_format", format);
        values.put("file_name", fileName);
        values.put("file_path", filePath);
        values.put("file_hash", fileHash);
        values.put("created_at", timestamp(now));
        long id = insert.executeAndReturnKey(values).longValue();
        return find(id);
    }

    public ReportFile find(long reportId) {
        List<ReportFile> matches = jdbc.query(
                """
                SELECT id, task_id, report_status, file_format, file_name, file_path, file_hash, created_at
                FROM report_file WHERE id = ?
                """,
                (rs, row) -> new ReportFile(
                        rs.getLong("id"),
                        rs.getLong("task_id"),
                        rs.getString("report_status"),
                        rs.getString("file_format"),
                        rs.getString("file_name"),
                        rs.getString("file_path"),
                        rs.getString("file_hash"),
                        offset(rs.getTimestamp("created_at"))
                ),
                reportId
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    public List<ReportFile> findByTask(long taskId) {
        return jdbc.query(
                """
                SELECT id, task_id, report_status, file_format, file_name, file_path, file_hash, created_at
                FROM report_file WHERE task_id = ? ORDER BY created_at DESC
                """,
                (rs, row) -> new ReportFile(
                        rs.getLong("id"),
                        rs.getLong("task_id"),
                        rs.getString("report_status"),
                        rs.getString("file_format"),
                        rs.getString("file_name"),
                        rs.getString("file_path"),
                        rs.getString("file_hash"),
                        offset(rs.getTimestamp("created_at"))
                ),
                taskId
        );
    }
}
