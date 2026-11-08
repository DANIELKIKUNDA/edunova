-- EduNova v0.25.2 LOT24 industrial closure: result safety and operational review indexes.
ALTER TABLE assignment_grading_decisions ADD CONSTRAINT ck_assignment_grade_proposed_nonnegative CHECK(proposed_score IS NULL OR proposed_score>=0);
ALTER TABLE assignment_grading_decisions ADD CONSTRAINT ck_assignment_grade_final_nonnegative CHECK(final_score IS NULL OR final_score>=0);
ALTER TABLE assignment_similarity_flags ADD CONSTRAINT ck_assignment_similarity_review_state CHECK(review_state IN ('needs_review','cleared','escalated'));
CREATE INDEX ix_assignment_grade_validation ON assignment_grading_decisions(institution_id,validated_by,updated_at);
CREATE INDEX ix_assignment_results_state ON campus_assignments(institution_id,state,updated_at);
