# DATABASE_SCHEMA.md

> 2026-10-09 本轮增量：Flyway V5 新增 task_pair_failure：id、task_id、submission_a_id、submission_b_id、message(VARCHAR2000)、attempts、resolved、last_attempt_at，唯一键为 task_id+A+B。attempts 表示累计失败次数，恢复后保留历史。遗留 RUNNING 的成功计数和进度从 analysis_result 重建，不依赖崩溃前计数；仅支持单后端实例。已在隔离 H2 验证，MySQL 实库未验证。 依据与边界见 [前三项推进记录](proposal/NEXT_THREE_PROGRESS.md)。

> 2026-10-09 Flyway V4 增量：`submission.language_version VARCHAR(64) NOT NULL DEFAULT ''`；`question.starter_language VARCHAR(16) NOT NULL DEFAULT ''`、`starter_code TEXT NULL`、`starter_source VARCHAR(2000) NOT NULL DEFAULT ''`。历史缺失模板源码在响应中规范为空字符串；原始模板内容按输入保存，不裁剪行号。复核上下文沿用 evidence 的 JSON 元数据快照，无新增关系标签。具体实现为 `V4__review_context.sql`，旧迁移保持不变。

> 2026-10-08 Flyway V3：`analysis_result.problem_profile_json TEXT NULL` 保存每次结果画像，避免读取题目的最新画像改变旧结果；无快照的历史记录仍使用旧回退逻辑。`threshold_adjustment_json` 原有字段保存的完整 JSON 优先用于接口返回，保留 HTML 的策略标记；既有关系表继续用于兼容查询。HTML 不写入算法题 `problem_feature`，`.cpp` 新上传登记为 `cpp`。迁移已在 H2 MySQL 兼容模式验证，实际 MySQL 重放待完成。

> 本文件定义 CodeRisk / PICAS 的数据库结构。数据库设计必须服务“题目感知型代码相似风险检测”主线，完整保存题目信息、代码提交、任务状态、题目特征、多维相似度、动态阈值、证据链、实验结果和报告元数据。

---

## 1. 数据库设计目标

### 1.1 核心目标

数据库需要支撑以下能力：

```text
题目管理
代码提交管理
检测任务管理
题目复杂度评分存储
多维相似度结果存储
动态阈值与风险等级存储
证据片段与变量映射存储
实验数据集与实验结果存储
报告导出与审计追踪
```

### 1.2 设计原则

```text
权威数据入库，大型中间产物存路径；
检测结果可追溯，实验结果可复现；
最终分数、分项指标、阈值、证据必须分开保存；
不要只保存一个 similarity 百分比；
不要把报告文本当作唯一结果来源；
```

### 1.3 数据库选择

首期推荐：

```text
MySQL 8.x
```

原因：

1. 本科毕设与工程展示环境部署简单。
2. JSON 字段可存储轻量特征扩展。
3. MySQL 与 Spring Boot、MyBatis-Plus 配合稳定。
4. 软著和答辩说明更容易。

可替代方案：PostgreSQL。若后续需要更强 JSON 查询和实验分析，可迁移。

---

## 2. 命名规范

### 2.1 表命名

```text
小写蛇形命名
业务实体使用单数或复合名
不使用 t_ 前缀
```

示例：

```text
question
submission
detection_task
analysis_result
evidence
```

### 2.2 字段命名

```text
id                  主键
created_at          创建时间
updated_at          更新时间
deleted             逻辑删除标记
status              状态
```

### 2.3 主键策略

推荐使用：

```text
BIGINT 自增主键
```

若后续需要分布式，可替换为雪花 ID。

### 2.4 时间字段

```text
created_at DATETIME NOT NULL
updated_at DATETIME NOT NULL
finished_at DATETIME NULL
```

建议由后端统一填充。

---

## 3. 用户与权限表

### 3.1 user

用于保存系统用户。V1 可只实现管理员和普通用户。

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(64) NULL,
    email VARCHAR(128) NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'USER',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0
);
```

### 3.2 user_login_log

可选，用于记录登录行为。

```sql
CREATE TABLE user_login_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    ip_address VARCHAR(64) NULL,
    user_agent VARCHAR(255) NULL,
    login_result VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_login_user_time (user_id, created_at)
);
```

---

## 4. 题目相关表

### 4.1 question

保存题目基础信息。

```sql
CREATE TABLE question (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    input_format TEXT NULL,
    output_format TEXT NULL,
    constraints_text TEXT NULL,
    sample_text TEXT NULL,
    source_type VARCHAR(64) NOT NULL DEFAULT 'MANUAL',
    source_name VARCHAR(128) NULL,
    manual_difficulty VARCHAR(32) NULL,
    created_by BIGINT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_question_title (title),
    INDEX idx_question_created_by (created_by)
);
```

字段说明：

```text
description：题面主体
constraints_text：约束条件原文
manual_difficulty：人工标注难度，可选 EASY/MEDIUM/HARD
source_type：MANUAL / DATASET / IMPORTED
```

### 4.2 reference_solution

保存参考答案。一个题目可有多个参考答案。

```sql
CREATE TABLE reference_solution (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    language VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    raw_code_path VARCHAR(512) NOT NULL,
    clean_code_path VARCHAR(512) NULL,
    code_hash VARCHAR(128) NOT NULL,
    line_count INT NULL,
    function_count INT NULL,
    cyclomatic_complexity DECIMAL(8,4) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_ref_question (question_id),
    INDEX idx_ref_language (language)
);
```

### 4.3 problem_feature

保存题目复杂度评分结果。该表是本项目区别于普通查重系统的核心表。

```sql
CREATE TABLE problem_feature (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    feature_version VARCHAR(32) NOT NULL,
    description_length INT NOT NULL DEFAULT 0,
    io_field_count INT NOT NULL DEFAULT 0,
    input_output_complexity DECIMAL(8,4) NOT NULL DEFAULT 0,
    constraint_count INT NOT NULL DEFAULT 0,
    sample_count INT NOT NULL DEFAULT 0,
    reference_line_count INT NULL,
    reference_function_count INT NULL,
    reference_cyclomatic_complexity DECIMAL(8,4) NULL,
    api_call_count INT NOT NULL DEFAULT 0,
    data_structure_count INT NOT NULL DEFAULT 0,
    data_structure_score DECIMAL(8,4) NOT NULL DEFAULT 0,
    algorithm_template_score DECIMAL(8,4) NOT NULL DEFAULT 0,
    historical_similarity_mean DECIMAL(8,4) NULL,
    historical_similarity_std DECIMAL(8,4) NULL,
    difficulty_score DECIMAL(8,4) NOT NULL,
    solution_space_score DECIMAL(8,4) NOT NULL,
    template_risk_score DECIMAL(8,4) NOT NULL,
    natural_similarity_risk DECIMAL(8,4) NOT NULL,
    recommended_base_threshold DECIMAL(8,4) NOT NULL,
    confidence DECIMAL(8,4) NOT NULL DEFAULT 0,
    explanation_json JSON NULL,
    threshold_adjustment_json JSON NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_problem_feature_version (question_id, feature_version),
    INDEX idx_problem_score (difficulty_score, natural_similarity_risk)
);
```

字段说明：

```text
difficulty_score：题目难度分数
solution_space_score：解法空间分数
template_risk_score：模板化风险分数
natural_similarity_risk：自然相似风险
recommended_base_threshold：基于题目特征推荐的初始阈值
feature_version：评分算法版本，保证实验可复现
```

---

## 5. 提交与文件表

### 5.1 submission

保存学生代码提交记录。

```sql
CREATE TABLE submission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    submitter_id VARCHAR(128) NULL,
    submitter_alias VARCHAR(128) NULL,
    language VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    raw_code_path VARCHAR(512) NOT NULL,
    clean_code_path VARCHAR(512) NULL,
    code_hash VARCHAR(128) NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    line_count INT NULL,
    token_count INT NULL,
    parser_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    parse_error TEXT NULL,
    source_type VARCHAR(64) NOT NULL DEFAULT 'UPLOAD',
    created_by BIGINT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_submission_question (question_id),
    INDEX idx_submission_hash (code_hash),
    INDEX idx_submission_language (language),
    INDEX idx_submission_submitter (submitter_id)
);
```

### 5.2 submission_artifact

保存提交代码的中间产物路径。

```sql
CREATE TABLE submission_artifact (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    submission_id BIGINT NOT NULL,
    task_id BIGINT NULL,
    artifact_type VARCHAR(64) NOT NULL,
    artifact_version VARCHAR(32) NOT NULL,
    artifact_path VARCHAR(512) NOT NULL,
    artifact_hash VARCHAR(128) NULL,
    summary_json JSON NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_artifact_submission (submission_id),
    INDEX idx_artifact_task (task_id),
    INDEX idx_artifact_type (artifact_type)
);
```

artifact_type 可取：

```text
CLEAN_CODE
TOKEN_SEQUENCE
RAW_AST
CANONICAL_TOKENS
CANONICAL_AST
IR
CFG
DFG
FINGERPRINT
```

---

## 6. 检测任务表

### 6.1 detection_task

保存一次查重任务。

```sql
CREATE TABLE detection_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_mode VARCHAR(64) NOT NULL DEFAULT 'PICAS_STANDARD',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    progress DECIMAL(8,4) NOT NULL DEFAULT 0,
    total_submissions INT NOT NULL DEFAULT 0,
    total_pairs INT NOT NULL DEFAULT 0,
    finished_pairs INT NOT NULL DEFAULT 0,
    failed_pairs INT NOT NULL DEFAULT 0,
    config_json JSON NULL,
    error_message TEXT NULL,
    created_by BIGINT NULL,
    started_at DATETIME NULL,
    finished_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_task_question (question_id),
    INDEX idx_task_status (status),
    INDEX idx_task_created_by (created_by, created_at)
);
```

task_mode 可取：

```text
BASIC_TOKEN
TOKEN_AST
PICAS_INVARIANT
PICAS_STANDARD
PICAS_CROSSLANG
PICAS_EXPERIMENTAL
```

### 6.2 detection_task_submission

任务和提交之间的关联表。

```sql
CREATE TABLE detection_task_submission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    submission_id BIGINT NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'TARGET',
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_task_submission (task_id, submission_id),
    INDEX idx_dts_task (task_id),
    INDEX idx_dts_submission (submission_id)
);
```

role 可取：

```text
TARGET
REFERENCE
EXCLUDED
```

---

## 7. 分析结果表

### 7.1 analysis_result

保存一个代码对的综合分析结果。

```sql
CREATE TABLE analysis_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    submission_a_id BIGINT NOT NULL,
    submission_b_id BIGINT NOT NULL,
    language_pair VARCHAR(64) NOT NULL,
    weighted_similarity_score DECIMAL(8,4) NOT NULL,
    dynamic_threshold DECIMAL(8,4) NOT NULL,
    risk_margin DECIMAL(8,4) NOT NULL,
    calibrated_risk_score DECIMAL(8,4) NOT NULL,
    risk_level VARCHAR(32) NOT NULL,
    exceed_threshold TINYINT NOT NULL DEFAULT 0,
    margin_scale DECIMAL(8,4) NOT NULL DEFAULT 0.4000,
    formula_version VARCHAR(64) NOT NULL DEFAULT 'FORMULA_SPEC_V1',
    algorithm_version VARCHAR(64) NOT NULL,
    metric_config_hash VARCHAR(128) NULL,
    threshold_explanation TEXT NULL,
    threshold_adjustment_json JSON NULL,
    evidence_count INT NOT NULL DEFAULT 0,
    high_confidence_evidence_count INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'FINISHED',
    error_message TEXT NULL,
    reason_summary TEXT NULL,
    is_mock TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_result_pair (task_id, submission_a_id, submission_b_id),
    INDEX idx_result_task (task_id),
    INDEX idx_result_question (question_id),
    INDEX idx_result_risk (risk_level, risk_margin),
    INDEX idx_result_threshold (exceed_threshold),
    INDEX idx_result_margin (risk_margin),
    INDEX idx_result_formula (formula_version, algorithm_version)
);
```

字段说明：

```text
weighted_similarity_score：多维相似度加权结果，等于 Σ wi * Sim_i。
dynamic_threshold：根据题目画像生成的动态阈值。
risk_margin：weighted_similarity_score - dynamic_threshold。
calibrated_risk_score：用于展示的归一化风险分数，不能作为排序第一关键字。
exceed_threshold：weighted_similarity_score 是否超过 dynamic_threshold。
margin_scale：risk_margin 映射为 calibrated_risk_score 的尺度，默认 0.4000。
formula_version：公式版本，用于实验和结果复现。
metric_config_hash：指标权重配置哈希，用于复现实验结果。
threshold_explanation：动态阈值自然语言解释。
threshold_adjustment_json：动态阈值各调整项明细。
```

risk_level 可取：

```text
LOW
MEDIUM
ELEVATED
HIGH
```

### 7.2 similarity_metric

保存每个代码对的分项指标。

```sql
CREATE TABLE similarity_metric (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    metric_value DECIMAL(8,4) NOT NULL,
    metric_weight DECIMAL(8,4) NOT NULL DEFAULT 0,
    metric_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    explanation TEXT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_result_metric (result_id, metric_name),
    INDEX idx_metric_name_value (metric_name, metric_value)
);
```

metric_name 可取：

```text
TOKEN_SIMILARITY
AST_SIMILARITY
CANONICAL_TOKEN_SIMILARITY
CONTROL_FLOW_SIMILARITY
DATA_DEPENDENCY_SIMILARITY
OPERATION_SEQUENCE_SIMILARITY
RARE_FRAGMENT_SIMILARITY
IDENTIFIER_MAPPING_SIMILARITY
IO_PATTERN_SIMILARITY
BUG_PATTERN_SIMILARITY
CROSSLANG_IR_SIMILARITY
CROSSLANG_CONTROL_SUMMARY_SIMILARITY
CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY
```

V4 Phase 1-2 的三个 CROSSLANG 指标均以 metric_weight=0 保存，只用于实验展示和复现，不进入 PICAS_STANDARD。轻量摘要存入 evidence_payload，不新增 CFG/DFG 图表。

### 7.3 threshold_adjustment

保存动态阈值的解释性分解。

```sql
CREATE TABLE threshold_adjustment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL,
    base_threshold DECIMAL(8,4) NOT NULL,
    difficulty_adjustment DECIMAL(8,4) NOT NULL DEFAULT 0,
    solution_space_adjustment DECIMAL(8,4) NOT NULL DEFAULT 0,
    template_risk_adjustment DECIMAL(8,4) NOT NULL DEFAULT 0,
    natural_similarity_adjustment DECIMAL(8,4) NOT NULL DEFAULT 0,
    historical_distribution_adjustment DECIMAL(8,4) NOT NULL DEFAULT 0,
    final_threshold DECIMAL(8,4) NOT NULL,
    formula_version VARCHAR(32) NOT NULL,
    explanation TEXT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_threshold_result (result_id)
);
```

---

## 8. 证据表

### 8.1 evidence

保存结构化证据。

```sql
CREATE TABLE evidence (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL,
    evidence_type VARCHAR(64) NOT NULL,
    confidence DECIMAL(8,4) NOT NULL,
    similarity_score DECIMAL(8,4) NOT NULL,
    code_a_start_line INT NULL,
    code_a_end_line INT NULL,
    code_b_start_line INT NULL,
    code_b_end_line INT NULL,
    code_a_snippet TEXT NULL,
    code_b_snippet TEXT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    evidence_payload JSON NULL,
    visualizable TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    INDEX idx_evidence_result (result_id),
    INDEX idx_evidence_type (evidence_type),
    INDEX idx_evidence_confidence (confidence)
);
```

evidence_type 可取：

```text
TOKEN_MATCH
AST_STRUCTURE_MATCH
CANONICAL_TOKEN_MATCH
IDENTIFIER_MAPPING
CONTROL_STRUCTURE_MATCH
OPERATION_SEQUENCE_MATCH
BOUNDARY_PATTERN_MATCH
RARE_FRAGMENT_MATCH
TEMPLATE_COMMON_FRAGMENT
CROSSLANG_IR_MATCH
PARSER_WARNING
REVIEW_NOTE
```

### 8.2 identifier_mapping

保存变量名、函数名、参数名的疑似映射关系。

```sql
CREATE TABLE identifier_mapping (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL,
    mapping_type VARCHAR(32) NOT NULL,
    name_a VARCHAR(255) NOT NULL,
    name_b VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255) NULL,
    scope_path VARCHAR(255) NULL,
    occurrence_a INT NOT NULL DEFAULT 0,
    occurrence_b INT NOT NULL DEFAULT 0,
    confidence DECIMAL(8,4) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_mapping_result (result_id),
    INDEX idx_mapping_type (mapping_type)
);
```

mapping_type 可取：

```text
VARIABLE
FUNCTION
PARAMETER
CLASS
CONSTANT
```

### 8.3 rare_fragment

保存稀有片段证据。

```sql
CREATE TABLE rare_fragment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL,
    fragment_signature VARCHAR(255) NOT NULL,
    fragment_type VARCHAR(64) NOT NULL,
    rarity_score DECIMAL(8,4) NOT NULL,
    similarity_score DECIMAL(8,4) NOT NULL,
    code_a_start_line INT NULL,
    code_a_end_line INT NULL,
    code_b_start_line INT NULL,
    code_b_end_line INT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_rare_result (result_id),
    INDEX idx_rare_signature (fragment_signature)
);
```

---

## 9. 报告表

### 9.1 report_file

保存导出报告。

```sql
CREATE TABLE report_file (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NULL,
    experiment_run_id BIGINT NULL,
    report_type VARCHAR(64) NOT NULL,
    report_status VARCHAR(32) NOT NULL DEFAULT 'GENERATED',
    file_format VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(128) NULL,
    generated_by BIGINT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_report_task (task_id),
    INDEX idx_report_experiment (experiment_run_id),
    INDEX idx_report_type (report_type)
);
```

report_type 可取：

```text
DETECTION_REPORT
EXPERIMENT_REPORT
SOFTWARE_MANUAL
PAPER_TABLE_EXPORT
```

---

## 10. 实验数据集表

### 10.1 experiment_dataset

保存实验数据集信息。

```sql
CREATE TABLE experiment_dataset (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_name VARCHAR(255) NOT NULL,
    dataset_version VARCHAR(64) NOT NULL,
    dataset_type VARCHAR(64) NOT NULL,
    description TEXT NULL,
    source_url VARCHAR(512) NULL,
    license_text VARCHAR(255) NULL,
    total_questions INT NOT NULL DEFAULT 0,
    total_submissions INT NOT NULL DEFAULT 0,
    total_pairs INT NOT NULL DEFAULT 0,
    created_by BIGINT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_dataset_version (dataset_name, dataset_version)
);
```

dataset_type 可取：

```text
PUBLIC_BENCHMARK
COURSE_ASSIGNMENT
SYNTHETIC_OBFUSCATION
AI_REWRITE
MIXED
```

### 10.2 experiment_case

保存一个实验样本对。

```sql
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
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_experiment_case_id (dataset_version, case_id),
    INDEX idx_case_dataset (dataset_id),
    INDEX idx_case_problem_split (problem_id, split_name),
    INDEX idx_case_label_type (experiment_label, case_type)
);
```

`experiment_label` 可取值以 `ENUMS.md` 为准：

```text
SIMILAR
SUSPICIOUS
TRANSFORMED
INDEPENDENT
NATURAL_SIMILAR
UNCERTAIN
```

`case_type` 同样以 `ENUMS.md` 为真源，当前 V3 数据集覆盖 `VARIABLE_RENAME`、`PARAMETER_RENAME`、`FUNCTION_RENAME`、`FORMAT_COMMENT_CHANGE`、`NATURAL_TEMPLATE` 和 `INDEPENDENT_SOLUTION` 等类型。

### 10.3 experiment_run

保存一次实验运行。

```sql
CREATE TABLE experiment_run (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_id BIGINT NULL,
    experiment_id VARCHAR(64) NOT NULL,
    run_name VARCHAR(255) NOT NULL,
    method_name VARCHAR(128) NOT NULL,
    method_version VARCHAR(64) NOT NULL,
    formula_version VARCHAR(64) NOT NULL,
    dataset_version VARCHAR(64) NOT NULL,
    random_seed BIGINT NOT NULL,
    git_commit VARCHAR(128) NOT NULL,
    config_json JSON NULL,
    result_path VARCHAR(512) NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    total_cases INT NOT NULL DEFAULT 0,
    finished_cases INT NOT NULL DEFAULT 0,
    failed_cases INT NOT NULL DEFAULT 0,
    started_at DATETIME NULL,
    finished_at DATETIME NULL,
    created_by BIGINT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_run_dataset (dataset_id),
    INDEX idx_run_method (method_name, method_version),
    INDEX idx_run_status (status)
);
```

method_name 可取：

```text
STRING_BASELINE
TOKEN_BASELINE
AST_BASELINE
FIXED_THRESHOLD
JPLAG
DOLOS
PICAS_STANDARD
PICAS_ABLATION_NO_PROBLEM
PICAS_ABLATION_NO_CANONICAL
PICAS_ABLATION_NO_RARE
```

### 10.4 experiment_result

保存每个实验样本对的预测结果。

```sql
CREATE TABLE experiment_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    run_id BIGINT NOT NULL,
    case_id VARCHAR(128) NOT NULL,
    experiment_label VARCHAR(32) NOT NULL,
    predicted_score DECIMAL(8,4) NOT NULL,
    predicted_label VARCHAR(32) NOT NULL,
    threshold_value DECIMAL(8,4) NOT NULL,
    correct TINYINT NULL,
    runtime_ms BIGINT NULL,
    result_payload JSON NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_run_case (run_id, case_id),
    INDEX idx_exp_result_run (run_id),
    INDEX idx_exp_result_correct (correct),
    INDEX idx_exp_result_label (predicted_label)
);
```

### 10.5 experiment_summary

保存一次实验运行的总体指标。

```sql
CREATE TABLE experiment_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    run_id BIGINT NOT NULL,
    group_name VARCHAR(128) NOT NULL DEFAULT 'ALL',
    group_value VARCHAR(128) NOT NULL DEFAULT 'ALL',
    precision_score DECIMAL(8,4) NULL,
    recall_score DECIMAL(8,4) NULL,
    f1_score DECIMAL(8,4) NULL,
    accuracy_score DECIMAL(8,4) NULL,
    false_positive_rate DECIMAL(8,4) NULL,
    false_negative_rate DECIMAL(8,4) NULL,
    auc_score DECIMAL(8,4) NULL,
    average_runtime_ms DECIMAL(12,4) NULL,
    sample_count INT NOT NULL DEFAULT 0,
    summary_json JSON NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_run_group (run_id, group_name, group_value)
);
```

---

## 11. 审计与日志表

### 11.1 audit_log

保存关键操作记录。

```sql
CREATE TABLE audit_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NULL,
    action VARCHAR(128) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id BIGINT NULL,
    ip_address VARCHAR(64) NULL,
    detail_json JSON NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_audit_user_time (user_id, created_at),
    INDEX idx_audit_target (target_type, target_id),
    INDEX idx_audit_action (action)
);
```

### 11.2 system_error_log

保存系统异常。

```sql
CREATE TABLE system_error_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(64) NOT NULL,
    error_type VARCHAR(128) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace MEDIUMTEXT NULL,
    context_json JSON NULL,
    resolved TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    INDEX idx_error_service_time (service_name, created_at),
    INDEX idx_error_type (error_type)
);
```

---

## 12. 状态枚举规范

### 12.1 任务状态

```text
PENDING
QUEUED
RUNNING
PARTIAL
FAILED
CANCELLED
FINISHED
```

### 12.2 解析状态

字段名统一使用 `parser_status`，取值如下：

```text
NOT_PARSED
PARSED
PARTIAL
FAILED
FALLBACK_TOKEN_ONLY
```

### 12.3 风险等级

```text
LOW
MEDIUM
ELEVATED
HIGH
```

禁止使用 `CRITICAL`、`EXTREME`、`CONFIRMED_PLAGIARISM` 作为生产风险等级。

### 12.4 实验状态

```text
PENDING
RUNNING
FAILED
FINISHED
CANCELLED
```

---

## 13. JSON 字段规范

### 13.1 problem_feature.explanation_json

```json
{
  "difficultyReasons": ["reference solution has multiple branches"],
  "templateRiskReasons": ["standard sorting pattern detected"],
  "naturalSimilarityReasons": ["simple input-output format"],
  "weights": {
    "difficulty": 0.30,
    "templateRisk": 0.25
  }
}
```

### 13.2 detection_task.config_json

```json
{
  "mode": "PICAS_STANDARD",
  "languages": ["java", "python"],
  "enableCanonicalization": true,
  "enableProblemAwareThreshold": true,
  "enableRareFragment": true,
  "maxEvidencePerPair": 20
}
```

### 13.3 evidence.evidence_payload

```json
{
  "astNodeType": "FOR_STATEMENT",
  "operationSignature": "ITERATE_SEQUENCE->MOD_CHECK->COUNTER_INCREMENT",
  "identifierPairs": [
    {"a": "sum", "b": "result", "canonical": "VAR_1"}
  ]
}
```

---

## 14. 索引设计建议

### 14.1 高频查询

高频查询包括：

```text
按题目查提交
按任务查结果
按结果查证据
按风险等级排序代码对
按实验运行查实验结果
```

### 14.2 必备索引

必须保留：

```text
submission(question_id)
detection_task(question_id, status)
analysis_result(task_id)
analysis_result(risk_level, risk_margin)
evidence(result_id)
similarity_metric(result_id, metric_name)
experiment_result(run_id, case_id)
experiment_summary(run_id, group_name, group_value)
```

### 14.3 大表注意事项

`analysis_result` 和 `evidence` 在大任务下增长较快。增强版可考虑：

```text
按 task_id 分页查询
只对高风险结果保存完整证据
低风险结果保存摘要
归档历史任务
```

---

## 15. 数据一致性规则

### 15.1 检测任务一致性

```text
一个 detection_task 必须关联一个 question
一个 detection_task 必须至少关联两个 submission
一个 analysis_result 必须属于一个 detection_task
一个 analysis_result 必须对应两个不同 submission
一个 result 可以有多个 metric 和 evidence
```

### 15.2 删除规则

建议使用逻辑删除：

```text
question.deleted = 1
submission.deleted = 1
detection_task.deleted = 1
```

已生成的实验结果和报告不建议物理删除，除非明确清理。

### 15.3 文件一致性

数据库中的文件路径必须对应真实文件。若文件缺失：

```text
后端返回 FILE_NOT_FOUND
任务不可重新分析
已有结果仍可展示摘要
```

---

## 16. 数据库初始化策略

### 16.1 初始化脚本

建议提供：

```text
scripts/init_db.sql
scripts/seed_demo_data.sql
scripts/clear_demo_data.sql
```

### 16.2 Demo 数据

Demo 至少包含：

```text
3 个题目：简单题、模板题、复杂题
每题 6~10 份代码
包含变量改名、格式修改、函数拆分样例
至少一个 Java-Python 跨语言样例
至少一个高风险代码对
至少一个自然相似但低风险代码对
```

---

## 17. 软著与论文复用点

### 17.1 软著材料

数据库设计可用于软著说明书中的：

```text
系统数据结构
功能模块说明
查重任务流程
检测报告管理
实验结果管理
```

### 17.2 论文材料

数据库设计可用于论文中的：

```text
系统实现章节
数据流设计
实验数据管理
结果可追溯性说明
```

### 17.3 专利材料

以下表与专利技术点强相关：

```text
problem_feature
threshold_adjustment
similarity_metric
evidence
identifier_mapping
rare_fragment
```

---

## 18. 数据库验收标准

数据库设计完成后必须满足：

```text
1. 能保存题目信息和参考答案。
2. 能保存多个语言的提交代码。
3. 能保存检测任务状态和进度。
4. 能保存题目复杂度评分四大核心分数。
5. 能保存动态阈值分解过程。
6. 能保存每个代码对的综合风险结果。
7. 能保存多维相似度指标。
8. 能保存结构化证据和代码行号。
9. 能保存标识符映射关系。
10. 能保存实验数据集、实验样本、实验运行和实验指标。
11. 能支撑前端分页查询高风险结果。
12. 能支撑论文实验复现。
```

---

## 19. 禁止事项

```text
禁止只设计 question/submission/result 三张表就结束。
禁止只保存最终 similarity，不保存分项指标。
禁止不保存 dynamic_threshold 和 threshold_adjustment。
禁止不保存 evidence 的行号范围。
禁止把大型 AST 全部塞进数据库正文。
禁止实验结果只保存成 Excel 而不入库或归档。
禁止在真实学生数据中保存未脱敏姓名学号。
```

---

## 20. 后续扩展表

增强版可增加：

```text
llm_assisted_review：LLM 辅助解释记录
manual_review：人工复核记录
feedback_record：用户反馈记录
plagiarism_case_archive：历史案例库
model_config：算法权重配置版本
```

这些不是 V1 必做，但适合 V3/V4。
