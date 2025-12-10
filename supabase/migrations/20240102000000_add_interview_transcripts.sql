-- Create interview_transcripts table for storing Daily.co transcription data
CREATE TABLE IF NOT EXISTS interview_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    daily_room_name VARCHAR(255) NOT NULL,  -- e.g., "interview-{interview_id}"
    transcript_text TEXT NOT NULL,  -- Full transcript in plain text
    transcript_webvtt TEXT,  -- Original WebVTT format (optional, for reference)
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    duration_seconds INTEGER,  -- Call duration in seconds
    participant_count INTEGER,  -- Number of participants
    status VARCHAR(50) DEFAULT 'pending'  -- 'pending', 'processing', 'completed', 'failed'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_interview_transcripts_interview_id ON interview_transcripts(interview_id);
CREATE INDEX IF NOT EXISTS idx_interview_transcripts_daily_room_name ON interview_transcripts(daily_room_name);
CREATE INDEX IF NOT EXISTS idx_interview_transcripts_status ON interview_transcripts(status);

-- Grant table permissions
GRANT ALL ON TABLE interview_transcripts TO anon, authenticated, service_role;

-- Enable Row Level Security
ALTER TABLE interview_transcripts ENABLE ROW LEVEL SECURITY;
