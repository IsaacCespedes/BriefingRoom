-- Add source tracking and metadata columns for multi-format input support
ALTER TABLE interviews
ADD COLUMN IF NOT EXISTS job_description_source VARCHAR(50) DEFAULT 'text',
ADD COLUMN IF NOT EXISTS job_description_metadata JSONB,
ADD COLUMN IF NOT EXISTS job_description_path TEXT,  -- File path or URL (if not text)
ADD COLUMN IF NOT EXISTS resume_source VARCHAR(50) DEFAULT 'text',
ADD COLUMN IF NOT EXISTS resume_metadata JSONB,
ADD COLUMN IF NOT EXISTS resume_path TEXT;  -- File path or URL (if not text)

-- Add indexes for querying by source type
CREATE INDEX IF NOT EXISTS idx_interviews_jd_source ON interviews(job_description_source);
CREATE INDEX IF NOT EXISTS idx_interviews_resume_source ON interviews(resume_source);

-- Add comments explaining the columns
COMMENT ON COLUMN interviews.job_description_source IS 'Source type: text, pdf, docx, url';
COMMENT ON COLUMN interviews.job_description_metadata IS 'Metadata about the source (filename, file_size, file_type, url, etc.)';
COMMENT ON COLUMN interviews.job_description_path IS 'File path in storage or URL (if source is file/url)';
COMMENT ON COLUMN interviews.resume_source IS 'Source type: text, pdf, docx, url';
COMMENT ON COLUMN interviews.resume_metadata IS 'Metadata about the source (filename, file_size, file_type, url, etc.)';
COMMENT ON COLUMN interviews.resume_path IS 'File path in storage or URL (if source is file/url)';
