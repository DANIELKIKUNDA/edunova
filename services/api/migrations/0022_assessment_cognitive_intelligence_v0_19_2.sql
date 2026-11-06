-- LOT 18 Cognitive Intelligence: Bloom taxonomy, quality gates and higher-order assessment metadata.
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS bloom_level varchar(24) NOT NULL DEFAULT 'understand' CHECK (bloom_level IN ('remember','understand','apply','analyze','evaluate','create'));
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS learning_objective text NOT NULL DEFAULT '';
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS cognitive_steps json NOT NULL DEFAULT '[]';
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS distractor_rationales json NOT NULL DEFAULT '[]';
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS quality_score integer NOT NULL DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 100);
ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS clinical_vignette integer NOT NULL DEFAULT 0 CHECK (clinical_vignette IN (0,1));
ALTER TABLE assessment_blueprints ADD COLUMN IF NOT EXISTS bloom_distribution json;
ALTER TABLE assessment_blueprints ADD COLUMN IF NOT EXISTS min_quality_score integer NOT NULL DEFAULT 0 CHECK (min_quality_score BETWEEN 0 AND 100);
ALTER TABLE assessment_results ADD COLUMN IF NOT EXISTS by_bloom json NOT NULL DEFAULT '{}';
CREATE INDEX IF NOT EXISTS ix_assessment_questions_cognitive ON assessment_questions(course_id,approved,bloom_level,quality_score DESC,difficulty DESC);
