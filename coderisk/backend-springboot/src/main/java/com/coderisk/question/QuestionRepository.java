package com.coderisk.question;

import static com.coderisk.persistence.JdbcTimes.offset;
import static com.coderisk.persistence.JdbcTimes.timestamp;

import java.sql.Timestamp;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.stereotype.Repository;

@Repository
public class QuestionRepository {

    private final JdbcTemplate jdbc;
    private final SimpleJdbcInsert insert;

    public QuestionRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
        this.insert = new SimpleJdbcInsert(jdbc)
                .withTableName("question")
                .usingGeneratedKeyColumns("id");
    }

    public QuestionResponse save(QuestionCreateRequest request) {
        OffsetDateTime now = OffsetDateTime.now();
        Map<String, Object> values = new java.util.LinkedHashMap<>(Map.of(
                "title", request.title().trim(),
                "description", normalize(request.description()),
                "input_format", normalize(request.inputFormat()),
                "output_format", normalize(request.outputFormat()),
                "constraints_text", normalize(request.constraintsText()),
                "source_type", "MANUAL",
                "created_at", timestamp(now),
                "updated_at", timestamp(now),
                "deleted", 0
        ));
        values.put("starter_language", normalize(request.starterLanguage()).toLowerCase(java.util.Locale.ROOT));
        values.put("starter_code", request.starterCode() == null ? "" : request.starterCode());
        values.put("starter_source", normalize(request.starterSource()));
        long id = insert.executeAndReturnKey(values).longValue();
        return find(id);
    }

    public QuestionResponse find(long id) {
        List<QuestionResponse> matches = jdbc.query(
                """
                SELECT id, title, description, input_format, output_format, constraints_text, starter_language, starter_code, starter_source, created_at, updated_at
                FROM question WHERE id = ? AND deleted = 0
                """,
                (rs, row) -> new QuestionResponse(
                        rs.getLong("id"),
                        rs.getString("title"),
                        rs.getString("description"),
                        rs.getString("input_format"),
                        rs.getString("output_format"),
                        rs.getString("constraints_text"),
                        normalize(rs.getString("starter_language")),
                        rs.getString("starter_code") == null ? "" : rs.getString("starter_code"),
                        normalize(rs.getString("starter_source")),
                        offset(rs.getTimestamp("created_at")),
                        offset(rs.getTimestamp("updated_at"))
                ),
                id
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    public List<QuestionResponse> list(int offset, int limit) {
        return jdbc.query(
                """
                SELECT id, title, description, input_format, output_format, constraints_text, starter_language, starter_code, starter_source, created_at, updated_at
                FROM question WHERE deleted = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (rs, row) -> new QuestionResponse(
                        rs.getLong("id"),
                        rs.getString("title"),
                        rs.getString("description"),
                        rs.getString("input_format"),
                        rs.getString("output_format"),
                        rs.getString("constraints_text"),
                        normalize(rs.getString("starter_language")),
                        rs.getString("starter_code") == null ? "" : rs.getString("starter_code"),
                        normalize(rs.getString("starter_source")),
                        offset(rs.getTimestamp("created_at")),
                        offset(rs.getTimestamp("updated_at"))
                ),
                limit,
                offset
        );
    }

    public long count() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM question WHERE deleted = 0", Long.class);
        return count == null ? 0 : count;
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim();
    }
}
