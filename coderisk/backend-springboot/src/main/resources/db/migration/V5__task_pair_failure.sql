CREATE TABLE task_pair_failure (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    submission_a_id BIGINT NOT NULL,
    submission_b_id BIGINT NOT NULL,
    message VARCHAR(2000) NOT NULL,
    attempts INT NOT NULL DEFAULT 1,
    resolved TINYINT NOT NULL DEFAULT 0,
    last_attempt_at DATETIME(6) NOT NULL,
    UNIQUE KEY uk_task_failure_pair (task_id, submission_a_id, submission_b_id),
    INDEX idx_task_failure_active (task_id, resolved)
);
