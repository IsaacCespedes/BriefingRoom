-- Create emotion_detections table for storing emotion detection data
CREATE TABLE IF NOT EXISTS emotion_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    participant_id VARCHAR(255) NOT NULL,  -- Daily.co participant ID
    participant_name VARCHAR(255),  -- Participant name (e.g., "Candidate")
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,  -- When the emotion was detected
    emotions JSONB NOT NULL,  -- Emotion scores: {happy: 0.78, sad: 0.15, ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'local_storage'  -- Source: 'local_storage', 'api', etc.
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_emotion_detections_interview_id ON emotion_detections(interview_id);
CREATE INDEX IF NOT EXISTS idx_emotion_detections_timestamp ON emotion_detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_emotion_detections_participant_id ON emotion_detections(participant_id);

-- Grant table permissions
GRANT ALL ON TABLE emotion_detections TO anon, authenticated, service_role;

-- Enable Row Level Security
ALTER TABLE emotion_detections ENABLE ROW LEVEL SECURITY;
