package com.coderisk.task;

import static com.coderisk.persistence.JdbcTimes.offset;
import static com.coderisk.persistence.JdbcTimes.timestamp;

import com.coderisk.common.enums.TaskMode;
import com.coderisk.common.enums.TaskStatus;
import com.coderisk.persistence.JdbcJson;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class TaskRepository {

    private final JdbcTemplate jdbc;
    private final JdbcJson json;
    private final SimpleJdbcInsert taskInsert;

    public TaskRepository(JdbcTemplate jdbc, JdbcJson json) {
        this.jdbc = jdbc;
        this.json = json;
        this.taskInsert = new SimpleJdbcInsert(jdbc)
                .withTableName("detection_task")
                .usingGeneratedKeyColumns("id");
    }

    @Transactional
    public DetectionTaskResponse save(
            long questionId,
            String taskName,
            TaskMode taskMode,
            List<Long> submissionIds
    ) {
        OffsetDateTime now = OffsetDateTime.now();
        int totalPairs = submissionIds.size() * (submissionIds.size() - 1) / 2;
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("question_id", questionId);
        values.put("task_name", taskName);
        values.put("task_mode", taskMode.name());
        values.put("status", TaskStatus.PENDING.name());
        values.put("progress", 0.0);
        values.put("total_submissions", submissionIds.size());
        values.put("total_pairs", totalPairs);
        values.put("finished_pairs", 0);
        values.put("failed_pairs", 0);
        values.put("config_json", json.write(Map.of("mode", taskMode.name())));
        values.put("created_at", timestamp(now));
        values.put("updated_at", timestamp(now));
        values.put("deleted", 0);
        long taskId = taskInsert.executeAndReturnKey(values).longValue();
        for (Long submissionId : submissionIds) {
            jdbc.update(
                    "INSERT INTO detection_task_submission (task_id, submission_id, role, created_at) VALUES (?, ?, 'TARGET', ?)",
                    taskId,
                    submissionId,
                    timestamp(now)
            );
        }
        return find(taskId);
    }

    public DetectionTaskResponse find(long taskId) {
        List<DetectionTaskResponse> matches = jdbc.query(
                """
                SELECT id, question_id, task_name, task_mode, status, total_submissions, total_pairs,
                       finished_pairs, error_message, created_at, finished_at
                FROM detection_task WHERE id = ? AND deleted = 0
                """,
                (rs, row) -> new DetectionTaskResponse(
                        rs.getLong("id"),
                        rs.getLong("question_id"),
                        rs.getString("task_name"),
                        TaskMode.valueOf(rs.getString("task_mode")),
                        TaskStatus.valueOf(rs.getString("status")),
                        rs.getInt("total_submissions"),
                        rs.getInt("total_pairs"),
                        rs.getInt("finished_pairs"),
                        submissionIds(rs.getLong("id")),
                        rs.getString("error_message") == null ? "" : rs.getString("error_message"),
                        offset(rs.getTimestamp("created_at")),
                        offset(rs.getTimestamp("finished_at"))
                ),
                taskId
        );
        return matches.isEmpty() ? null : matches.getFirst();
    }

    public List<DetectionTaskResponse> recent(int limit) {
        List<Long> ids = jdbc.query(
                "SELECT id FROM detection_task WHERE deleted = 0 ORDER BY created_at DESC LIMIT ?",
                (rs, row) -> rs.getLong("id"),
                limit
        );
        List<DetectionTaskResponse> tasks = new ArrayList<>();
        for (Long id : ids) {
            tasks.add(find(id));
        }
        return tasks;
    }

    public void updateState(
            long taskId,
            TaskStatus status,
            int finishedPairs,
            int failedPairs,
            String errorMessage,
            OffsetDateTime finishedAt
    ) {
        DetectionTaskResponse current = find(taskId);
        double progress = current == null || current.totalPairs() == 0
                ? 0.0
                : (double) finishedPairs / current.totalPairs();
        jdbc.update(
                """
                UPDATE detection_task
                SET status = ?, progress = ?, finished_pairs = ?, failed_pairs = ?, error_message = ?,
                    started_at = CASE WHEN started_at IS NULL AND ? = 'RUNNING' THEN ? ELSE started_at END,
                    finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                status.name(),
                progress,
                finishedPairs,
                failedPairs,
                errorMessage,
                status.name(),
                timestamp(OffsetDateTime.now()),
                timestamp(finishedAt),
                timestamp(OffsetDateTime.now()),
                taskId
        );
    }

    public long count() {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM detection_task WHERE deleted = 0", Long.class);
        return count == null ? 0 : count;
    }

    private List<Long> submissionIds(long taskId) {
        return jdbc.query(
                "SELECT submission_id FROM detection_task_submission WHERE task_id = ? ORDER BY id",
                (rs, row) -> rs.getLong("submission_id"),
                taskId
        );
    }
}
