-- Add JSONB field for structured transcript data with speaker segments
ALTER TABLE interview_transcripts 
ADD COLUMN IF NOT EXISTS transcript_data JSONB;

-- Create index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_interview_transcripts_data ON interview_transcripts USING GIN (transcript_data);

-- Add comment explaining the JSONB structure
COMMENT ON COLUMN interview_transcripts.transcript_data IS 'Structured transcript data with speaker segments. Format: {"segments": [{"speaker": "Speaker 0", "text": "...", "start_time": 0.0, "end_time": 5.0}, ...]}';
