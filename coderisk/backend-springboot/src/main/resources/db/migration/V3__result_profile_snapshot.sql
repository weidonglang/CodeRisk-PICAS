-- Preserve each result's domain/profile independently of the question's latest profile.
ALTER TABLE analysis_result ADD COLUMN problem_profile_json TEXT NULL;
