-- Make job_description and resume_text nullable to support file/URL sources
-- When source is 'file' or 'url', text will be NULL (extracted by CrewAI agents)
ALTER TABLE interviews
ALTER COLUMN job_description DROP NOT NULL,
ALTER COLUMN resume_text DROP NOT NULL;

-- Add comment explaining when these can be NULL
COMMENT ON COLUMN interviews.job_description IS 'Text content (NULL if source is file/url - will be extracted by CrewAI agents)';
COMMENT ON COLUMN interviews.resume_text IS 'Text content (NULL if source is file/url - will be extracted by CrewAI agents)';
