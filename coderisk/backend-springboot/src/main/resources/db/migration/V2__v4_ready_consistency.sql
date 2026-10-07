CREATE INDEX idx_result_formula ON analysis_result (formula_version, algorithm_version);

CREATE TABLE experiment_case (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_id BIGINT NULL,
    case_id VARCHAR(128) NOT NULL,
    problem_id VARCHAR(128) NOT NULL,
    problem_type VARCHAR(64) NOT NULL,
    split_name VARCHAR(32) NOT NULL,
    source_id VARCHAR(128) NOT NULL,
    experiment_label VARCHAR(32) NOT NULL,
    case_type VARCHAR(64) NOT NULL,
    language VARCHAR(32) NOT NULL,
    dataset_version VARCHAR(64) NOT NULL,
    case_payload JSON NULL,
    created_at DATETIME(6) NOT NULL,
    UNIQUE KEY uk_experiment_case_id (dataset_version, case_id),
    INDEX idx_case_dataset (dataset_id),
    INDEX idx_case_problem_split (problem_id, split_name),
    INDEX idx_case_label_type (experiment_label, case_type)
);
