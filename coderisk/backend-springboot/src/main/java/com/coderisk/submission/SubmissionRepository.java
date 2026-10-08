package com.coderisk.submission;

import static com.coderisk.persistence.JdbcTimes.offset;
import static com.coderisk.persistence.JdbcTimes.timestamp;

import com.coderisk.common.enums.LanguageSupportLevel;
import com.coderisk.common.enums.ParserStatus;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.stereotype.Repository;

@Repository
public class SubmissionRepository {

    private final JdbcTemplate jdbc;
    private final SimpleJdbcInsert insert;

    public SubmissionRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
        this.insert = new SimpleJdbcInsert(jdbc)
                .withTableName("submission")
                .usingGeneratedKeyColumns("id");
    }

    public SubmissionResponse save(
            long questionId,
            String studentId,
            String language,
            LanguageSupportLevel supportLevel,
            String fileName,
            long fileSizeBytes,
            String rawCodePath,
            String codeHash,
            String languageVersion
    ) {
        OffsetDateTime now = OffsetDateTime.now();
        Map<String, Object> values = new java.util.LinkedHashMap<>();
        values.put("question_id", questionId);
        values.put("student_id", studentId);
        values.put("language", language);
        values.put("language_version", languageVersion);
        values.put("support_level", supportLevel.name());
        values.put("file_name", fileName);
        values.put("file_size_bytes", fileSizeBytes);
        values.put("raw_code_path", rawCodePath);
        values.put("code_hash", codeHash);
        values.put("parser_status", ParserStatus.NOT_PARSED.name());
        values.put("created_at", timestamp(now));
        values.put("updated_at", timestamp(now));
        values.put("deleted", 0);
        long id = insert.executeAndReturnKey(values).longValue();
        return find(id);
    }

    public SubmissionResponse find(long id) {
        List<SubmissionResponse> matches = jdbc.query(
                """
                SELECT id, question_id, student_id, language, language_version, support_level, file_name,
                       file_size_bytes, raw_code_path, parser_status, created_at
                FROM submission WHERE id = ? AND deleted = 0
                """,
                (rs, row) -> new SubmissionResponse(
                        rs.getLong("id"),
                        rs.getLong("question_id"),
                        rs.getString("student_id"),
                        rs.getString("language"),
                        rs.getString("language_version"),
                        LanguageSupportLevel.valueOf(rs.getString("support_level")),
                        rs.getString("file_name"),
                        rs.getLong("file_size_bytes"),
                        rs.getString("raw_code_path"),
                        ParserStatus.valueOf(rs.getString("parser_status")),
                        offset(rs.getTimestamp("created_at"))
                ),
                id
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    public List<SubmissionResponse> findByQuestion(long questionId) {
        return jdbc.query(
                """
                SELECT id, question_id, student_id, language, language_version, support_level, file_name,
                       file_size_bytes, raw_code_path, parser_status, created_at
                FROM submission WHERE question_id = ? AND deleted = 0 ORDER BY created_at DESC
                """,
                (rs, row) -> new SubmissionResponse(
                        rs.getLong("id"),
                        rs.getLong("question_id"),
                        rs.getString("student_id"),
                        rs.getString("language"),
                        rs.getString("language_version"),
                        LanguageSupportLevel.valueOf(rs.getString("support_level")),
                        rs.getString("file_name"),
                        rs.getLong("file_size_bytes"),
                        rs.getString("raw_code_path"),
                        ParserStatus.valueOf(rs.getString("parser_status")),
                        offset(rs.getTimestamp("created_at"))
                ),
                questionId
        );
    }

    public long count() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM submission WHERE deleted = 0", Long.class);
        return count == null ? 0 : count;
    }
}
