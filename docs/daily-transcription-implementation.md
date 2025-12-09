# Daily.co Transcription Implementation Guide

This document outlines the implementation steps for adding transcription capabilities to the Daily.co video calls, including real-time closed captions during calls and transcript storage/retrieval after calls end.

## Overview

The implementation consists of four main components:

1. **Real-time Transcription**: Display live closed captions during active video calls
2. **Transcription Storage**: Automatically store transcripts in our database after calls end
3. **REST API Access**: Provide endpoints to retrieve and download stored transcripts
4. **AI/Agent Interpretation**: Real-time analysis of conversation through transcript processing

---

## Prerequisites

### 1. Daily.co Domain Configuration

Before implementing transcription, you must configure transcription on your Daily.co domain:

1. **Enable Transcription in Daily.co Dashboard**:
   - Navigate to your Daily.co dashboard
   - Go to Settings → Transcription
   - Enable transcription for your domain
   - Note: Daily.co uses Deepgram as the transcription partner

2. **Deepgram Setup** (Required):
   - Sign up for a Deepgram account at [deepgram.com](https://www.deepgram.com)
   - Get your Deepgram API key from the dashboard
   - Daily.co will prompt you to enter your Deepgram credentials when enabling transcription
   - Deepgram offers $150 free credit upon signup

3. **Environment Variables**:
   - No additional environment variables needed beyond existing `DAILY_API_KEY`
   - Transcription is billed per-minute by Daily.co (included in your usage)

### 2. Understanding Daily.co Transcription

- **Real-time transcription**: Live transcription during calls, accessible via JavaScript SDK events
- **Stored transcripts**: Automatically saved in WebVTT format when `enable_transcription_storage` is enabled
- **API access**: Transcripts can be retrieved via Daily.co REST API after calls end

---

## Component 1: Real-Time Transcription (Closed Captions)

### 1.1 Backend: Enable Transcription on Room Creation

**File**: `backend/app/api/daily.py`

**Changes needed**:

1. **Update room properties** to enable transcription storage:
   ```python
   room_properties = {
       "enable_chat": True,
       "enable_screenshare": True,
       "enable_recording": False,
       "enable_transcription_storage": True,  # NEW: Store transcripts
       "transcription_options": {
           "provider": "deepgram",
           "model": "nova-2",  # Optional: specify Deepgram model
       }
   }
   ```

2. **No new API endpoints needed** - transcription is handled client-side via SDK events

### 1.2 Frontend: Add Closed Captions Component

**New File**: `frontend/src/lib/components/ClosedCaptions.svelte`

**Component responsibilities**:
- Subscribe to Daily.co transcription events
- Display real-time captions in a scrollable overlay
- Show speaker identification (if available)
- Styling that works over video call interface

**Key features**:
- Listen to `transcription-started`, `transcription-stopped`, and `transcription-message` events from Daily.co callFrame
- Maintain a buffer of recent caption lines (e.g., last 5-10 lines)
- Auto-scroll as new captions arrive
- Option to toggle captions on/off
- Position as overlay at bottom of video call interface

**Event handling**:
```typescript
callFrame.on("transcription-started", () => {
  // Captions are now active
});

callFrame.on("transcription-stopped", () => {
  // Captions stopped
});

callFrame.on("transcription-message", (event: any) => {
  // New caption text: event.text
  // Speaker: event.speaker (if available)
  // Timestamp: event.timestamp
});
```

### 1.3 Frontend: Integrate Closed Captions into DailyCall Component

**File**: `frontend/src/lib/components/DailyCall.svelte`

**Changes needed**:

1. **Import and add ClosedCaptions component**:
   - Place it as an overlay div within the video call container
   - Position absolutely at bottom of frame
   - Make it conditionally visible (toggle button)

2. **Subscribe to transcription events**:
   - After `callFrame.join()`, set up transcription event listeners
   - Pass callFrame reference to ClosedCaptions component (or handle events in parent)
   - Start transcription programmatically or let room settings handle it

3. **Start transcription when call is active**:
   ```typescript
   // After joining, start transcription
   if (callFrame && isJoined) {
     try {
       await callFrame.startTranscription();
     } catch (error) {
       console.error("Failed to start transcription:", error);
     }
   }
   ```

4. **Stop transcription when leaving**:
   ```typescript
   // In leaveCall() function
   if (callFrame) {
     try {
       await callFrame.stopTranscription();
     } catch (error) {
       console.error("Failed to stop transcription:", error);
     }
   }
   ```

### 1.4 Frontend: Add Toggle Controls

**User interface**:
- Add a "Show Captions" / "Hide Captions" toggle button
- Add a visual indicator when transcription is active
- Option to adjust caption position/size (future enhancement)

---

## Component 2: Transcription Storage

### 2.1 Database: Create Transcript Table

**New migration file**: `backend/migrations/XXX_add_transcripts_table.sql`

**Schema**:
```sql
CREATE TABLE interview_transcripts (
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

-- Indexes
CREATE INDEX idx_interview_transcripts_interview_id ON interview_transcripts(interview_id);
CREATE INDEX idx_interview_transcripts_daily_room_name ON interview_transcripts(daily_room_name);
CREATE INDEX idx_interview_transcripts_status ON interview_transcripts(status);
```

**Alternative approach**: Store transcript as JSONB for more flexibility:
```sql
ALTER TABLE interview_transcripts 
ADD COLUMN transcript_data JSONB;  -- Structured transcript data (segments, speakers, timestamps)
```

### 2.2 Backend: Create Transcript Model

**New File**: `backend/app/models/transcript.py`

**Model definition**:
```python
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class TranscriptBase(BaseModel):
    """Base transcript model."""
    interview_id: UUID
    daily_room_name: str
    transcript_text: str
    transcript_webvtt: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    participant_count: Optional[int] = None
    status: str = Field(default="pending")

class TranscriptCreate(TranscriptBase):
    """Model for creating a new transcript."""
    pass

class Transcript(TranscriptBase):
    """Full transcript model with database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TranscriptResponse(TranscriptBase):
    """Transcript response model for API responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
```

### 2.3 Backend: Add Database Functions

**File**: `backend/app/db.py`

**New functions**:
```python
def create_transcript(
    interview_id: UUID,
    daily_room_name: str,
    transcript_text: str,
    transcript_webvtt: Optional[str] = None,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    participant_count: Optional[int] = None,
    status: str = "pending"
) -> dict:
    """Create a new transcript record in the database."""
    # Implementation using Supabase client

def get_transcript_by_interview_id(interview_id: UUID) -> Optional[dict]:
    """Retrieve transcript for a given interview."""
    # Implementation

def update_transcript_status(transcript_id: UUID, status: str) -> dict:
    """Update transcript status."""
    # Implementation
```

### 2.4 Backend: Fetch Transcripts from Daily.co

**File**: `backend/app/api/daily.py`

**New helper function**:
```python
async def get_daily_transcript(room_name: str) -> Optional[dict]:
    """
    Retrieve stored transcript from Daily.co for a room.
    
    Args:
        room_name: Name of the Daily.co room (e.g., "interview-{interview_id}")
    
    Returns:
        Dictionary containing transcript data, or None if not available
    """
    # Use Daily.co REST API: GET /transcript
    # Endpoint: {DAILY_API_URL}/transcript?room_name={room_name}
    # Returns transcript in WebVTT format
```

**Notes**:
- Transcripts may not be immediately available after call ends
- Daily.co processes transcripts asynchronously
- May need to poll or use webhooks (future enhancement)
- Transcripts are returned in WebVTT format - need to parse to plain text

### 2.5 Backend: Transcript Processing Service

**New File**: `backend/app/services/transcript_service.py`

**Responsibilities**:
- Fetch transcripts from Daily.co API
- Parse WebVTT format to plain text
- Extract metadata (duration, participants, timestamps)
- Store in database
- Handle retries if transcript not yet available

**Key functions**:
```python
async def fetch_and_store_transcript(room_name: str, interview_id: UUID) -> dict:
    """
    Fetch transcript from Daily.co and store in database.
    
    This function:
    1. Calls Daily.co API to get transcript
    2. Parses WebVTT to plain text
    3. Extracts metadata
    4. Stores in database
    """
    
def parse_webvtt_to_text(webvtt_content: str) -> str:
    """Convert WebVTT format to plain text transcript."""
    # Parse WebVTT format and extract text content
    
def extract_webvtt_metadata(webvtt_content: str) -> dict:
    """Extract metadata from WebVTT (duration, timestamps, etc.)."""
```

### 2.6 Backend: Background Job / Webhook Handler

**Option A: Polling Approach** (Initial implementation):

**New endpoint**: `POST /api/daily/fetch-transcript/{interview_id}`

- Called manually or by a scheduled job
- Fetches transcript from Daily.co
- Stores in database
- Returns transcript or "not ready" status

**Option B: Webhook Approach** (Future enhancement):

**New endpoint**: `POST /api/daily/transcript-webhook`

- Daily.co sends webhook when transcript is ready
- Processes and stores transcript automatically
- More efficient but requires webhook configuration in Daily.co

**For initial implementation, use Option A (polling/manual trigger)**.

---

## Component 3: REST API Access to Transcripts

### 3.1 Backend: Get Transcript Endpoint

**File**: `backend/app/api/daily.py` (or new `backend/app/api/transcripts.py`)

**New endpoint**: `GET /api/transcripts/{interview_id}`

**Features**:
- Authenticated endpoint (requires valid token)
- Validates interview_id matches token's interview_id
- Returns full transcript with metadata
- Supports different response formats (JSON, plain text, WebVTT)

**Response model**:
```python
class TranscriptResponse(BaseModel):
    id: UUID
    interview_id: UUID
    transcript_text: str
    transcript_webvtt: Optional[str] = None
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    participant_count: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
```

### 3.2 Backend: List Transcripts Endpoint (Optional)

**Endpoint**: `GET /api/transcripts`

- List all transcripts (with pagination)
- Filter by interview_id, status, date range
- Useful for admin/debugging purposes

### 3.3 Backend: Download Transcript Endpoint

**Endpoint**: `GET /api/transcripts/{interview_id}/download`

**Features**:
- Returns transcript as downloadable file
- Supports multiple formats:
  - Plain text (`.txt`)
  - WebVTT (`.vtt`)
  - JSON (`.json`) - structured format with timestamps
- Sets appropriate `Content-Disposition` header
- Authenticated endpoint

**Query parameters**:
- `format`: `txt`, `vtt`, or `json` (default: `txt`)

### 3.4 Frontend: Transcript Download Component

**New File**: `frontend/src/lib/components/TranscriptDownload.svelte`

**Component responsibilities**:
- Display transcript status (pending, available, processing)
- Show "Download Transcript" button when available
- Format selector (TXT, VTT, JSON)
- Display transcript preview (first few lines)
- Error handling for unavailable transcripts

**Placement**:
- Add to host page (`frontend/src/routes/host/+page.svelte`) after call ends
- Add to candidate page (`frontend/src/routes/candidate/+page.svelte`) as well
- Show only when transcript is available

### 3.5 Frontend: Add API Functions

**File**: `frontend/src/lib/daily.ts` (or new `frontend/src/lib/transcripts.ts`)

**New functions**:
```typescript
export async function getTranscript(
  interviewId: string,
  token: string
): Promise<TranscriptResponse> {
  // GET /api/transcripts/{interview_id}
}

export async function downloadTranscript(
  interviewId: string,
  format: 'txt' | 'vtt' | 'json',
  token: string
): Promise<Blob> {
  // GET /api/transcripts/{interview_id}/download?format={format}
  // Returns blob for download
}

export async function fetchTranscriptFromDaily(
  interviewId: string,
  token: string
): Promise<TranscriptResponse> {
  // POST /api/daily/fetch-transcript/{interview_id}
  // Triggers fetching from Daily.co
}
```

### 3.6 Frontend: Integrate Download UI

**Files to update**:
- `frontend/src/routes/host/+page.svelte`
- `frontend/src/routes/candidate/+page.svelte`

**Changes**:
1. Check transcript availability on page load
2. Display transcript status indicator
3. Show download button when transcript is ready
4. Handle "Fetch Transcript" action if not yet fetched
5. Display transcript preview in a collapsible section

---

## Component 4: AI/Agent Interpretation

### 4.1 Architecture Decision

**Recommended Approach: Hybrid Real-Time Streaming**

This component enables real-time AI analysis of the conversation by streaming transcript chunks from the frontend to the backend, where AI agents process the content and stream insights back.

**Why Hybrid Approach?**
- **Security**: API keys stay server-side (OpenAI, Anthropic, etc.)
- **Cost Control**: Centralized billing and rate limiting
- **Scalability**: Handle long conversations without browser limitations
- **Real-Time**: Low-latency updates via WebSocket/SSE
- **Persistence**: Store analysis results in database for post-call review

**Architecture Flow**:
1. Frontend captures Daily.co transcription events (Component 1)
2. Frontend sends transcript segments to backend via WebSocket/SSE
3. Backend processes chunks with AI agents (OpenAI, Anthropic, etc.)
4. Backend streams insights back to frontend in real-time
5. Frontend displays live insights panel
6. Backend stores full analysis in database

**Alternative Approaches Considered**:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Frontend-only** | Lower latency, no backend load | API keys exposed, cost control issues, token limits | ❌ Not recommended |
| **Backend polling** | Simple, secure | Higher latency, less real-time | ✅ Good for post-call analysis |
| **Hybrid streaming** | Best of both worlds | More complex setup | ✅ **Recommended for real-time** |

### 4.2 Database: Create Analysis Results Table

**New migration file**: `backend/migrations/XXX_add_transcript_analysis_table.sql`

**Schema**:
```sql
CREATE TABLE transcript_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    transcript_id UUID REFERENCES interview_transcripts(id) ON DELETE CASCADE,
    
    -- Analysis results (JSONB for flexibility)
    analysis_data JSONB NOT NULL,  -- Structured analysis results
    
    -- Analysis type metadata
    analysis_type VARCHAR(100) NOT NULL,  -- 'real_time', 'full_transcript', 'summary'
    model_used VARCHAR(100),  -- 'gpt-4', 'claude-3', etc.
    provider VARCHAR(50),  -- 'openai', 'anthropic', 'custom'
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending'  -- 'pending', 'processing', 'completed', 'failed'
);

-- Indexes
CREATE INDEX idx_transcript_analyses_interview_id ON transcript_analyses(interview_id);
CREATE INDEX idx_transcript_analyses_transcript_id ON transcript_analyses(transcript_id);
CREATE INDEX idx_transcript_analyses_type ON transcript_analyses(analysis_type);
CREATE INDEX idx_transcript_analyses_status ON transcript_analyses(status);
CREATE INDEX idx_transcript_analyses_created_at ON transcript_analyses(created_at DESC);
```

**Analysis Data JSONB Structure** (flexible schema):
```json
{
  "sentiment": {
    "overall": "positive",
    "segments": [...],
    "trends": [...]
  },
  "topics": ["technical skills", "team collaboration", "leadership"],
  "key_points": [...],
  "questions": {
    "candidate_questions": [...],
    "interviewer_questions": [...]
  },
  "insights": [...],
  "recommendations": [...],
  "timestamps": {
    "speaking_time": {
      "candidate": 1200,
      "interviewer": 800
    }
  }
}
```

### 4.3 Backend: Create Analysis Model

**New File**: `backend/app/models/transcript_analysis.py`

**Model definition**:
```python
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TranscriptAnalysisBase(BaseModel):
    """Base transcript analysis model."""
    interview_id: UUID
    transcript_id: Optional[UUID] = None
    analysis_data: Dict[str, Any]  # JSONB structure
    analysis_type: str  # 'real_time', 'full_transcript', 'summary'
    model_used: Optional[str] = None
    provider: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(default="pending")

class TranscriptAnalysisCreate(TranscriptAnalysisBase):
    """Model for creating a new analysis."""
    pass

class TranscriptAnalysis(TranscriptAnalysisBase):
    """Full analysis model with database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TranscriptAnalysisResponse(TranscriptAnalysisBase):
    """Analysis response model for API responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime

class TranscriptChunk(BaseModel):
    """Model for incoming transcript chunks."""
    interview_id: UUID
    text: str
    speaker: Optional[str] = None
    timestamp: float
    sequence_number: int
```

### 4.4 Backend: WebSocket Support

**New File**: `backend/app/api/websocket.py`

**Responsibilities**:
- Handle WebSocket connections for real-time transcript streaming
- Authenticate WebSocket connections using tokens
- Route transcript chunks to analysis service
- Stream analysis results back to connected clients

**Key components**:
```python
from fastapi import WebSocket, WebSocketDisconnect
from app.api.auth import validate_websocket_token

@router.websocket("/ws/transcript-stream/{interview_id}")
async def transcript_stream_websocket(
    websocket: WebSocket,
    interview_id: str,
    token: str
):
    """
    WebSocket endpoint for real-time transcript streaming and analysis.
    
    Client sends: Transcript chunks as JSON
    Server sends: Analysis results as JSON
    
    Message format (client -> server):
    {
        "type": "transcript_chunk",
        "data": {
            "text": "...",
            "speaker": "...",
            "timestamp": 123.45,
            "sequence_number": 1
        }
    }
    
    Message format (server -> client):
    {
        "type": "analysis_update",
        "data": {
            "sentiment": "...",
            "topics": [...],
            "insights": [...],
            "timestamp": 123.45
        }
    }
    """
    # Authenticate connection
    # Accept WebSocket
    # Start analysis worker
    # Handle bidirectional streaming
```

**Alternative: Server-Sent Events (SSE)**
- Simpler than WebSocket (one-way from server)
- Good if only server->client updates needed
- Easier to implement with FastAPI

### 4.5 Backend: AI Analysis Service

**New File**: `backend/app/services/analysis_service.py`

**Responsibilities**:
- Process transcript chunks with AI models
- Aggregate insights over time
- Generate real-time and post-call analysis
- Support multiple AI providers (OpenAI, Anthropic, custom)

**Key functions**:
```python
from openai import AsyncOpenAI  # or Anthropic, etc.

class AnalysisService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Initialize other AI clients as needed
    
    async def analyze_transcript_chunk(
        self,
        chunk: TranscriptChunk,
        context: Dict[str, Any],
        interview_context: Dict[str, Any]  # job_description, resume, etc.
    ) -> Dict[str, Any]:
        """
        Analyze a single transcript chunk.
        
        Returns:
            {
                "sentiment": "...",
                "topics": [...],
                "key_points": [...],
                "insights": [...]
            }
        """
        # Build prompt with context
        # Call AI API
        # Parse and return results
    
    async def generate_aggregate_analysis(
        self,
        all_chunks: List[TranscriptChunk],
        interview_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis from full transcript.
        
        Useful for:
        - Post-call summary
        - Final recommendations
        - Comparison against job requirements
        """
        # Aggregate all chunks
        # Build comprehensive prompt
        # Call AI API for full analysis
        # Return structured results
    
    async def generate_realtime_insight(
        self,
        recent_chunks: List[TranscriptChunk],
        accumulated_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate quick insight from recent conversation.
        
        Optimized for speed and relevance.
        """
        # Focus on recent context
        # Generate quick insights
        # Return lightweight results
```

**AI Provider Options**:
- **OpenAI**: GPT-4, GPT-3.5-turbo (good balance of speed/cost/quality)
- **Anthropic**: Claude 3 (excellent for analysis, longer context)
- **Custom Agents**: CrewAI agents for specialized analysis
- **Local Models**: For on-premise deployments (future)

### 4.6 Backend: Analysis Types

**Different analysis types to support**:

1. **Real-Time Analysis**:
   - Sentiment tracking
   - Topic detection
   - Question identification
   - Speaking time analysis
   - Quick insights from recent conversation

2. **Full Transcript Analysis** (post-call):
   - Comprehensive sentiment analysis
   - Topic extraction and categorization
   - Key points summary
   - Question/answer analysis
   - Skills assessment against job requirements
   - Strengths and concerns identification
   - Recommendation generation

3. **Custom Analysis**:
   - Job-specific evaluation criteria
   - Resume alignment analysis
   - Communication style assessment
   - Cultural fit indicators

### 4.7 Backend: Analysis Endpoints

**New File**: `backend/app/api/analysis.py` (or add to existing endpoints)

**Endpoints**:

1. **WebSocket Endpoint** (Real-time):
   ```
   WS /api/ws/transcript-stream/{interview_id}?token={token}
   ```

2. **Get Analysis Results**:
   ```
   GET /api/analysis/{interview_id}
   ```
   - Returns latest analysis results
   - Supports filtering by analysis_type
   - Authenticated endpoint

3. **Trigger Full Analysis**:
   ```
   POST /api/analysis/{interview_id}/analyze
   ```
   - Triggers comprehensive analysis of full transcript
   - Returns job ID for async processing
   - Useful for post-call deep analysis

4. **Get Analysis History**:
   ```
   GET /api/analysis/{interview_id}/history
   ```
   - Returns all analysis snapshots over time
   - Useful for seeing how insights evolved during call

### 4.8 Frontend: Real-Time Insights Component

**New File**: `frontend/src/lib/components/RealTimeInsights.svelte`

**Component responsibilities**:
- Establish WebSocket connection for transcript streaming
- Send transcript chunks to backend as they arrive
- Display real-time analysis results
- Show sentiment indicators, topics, key insights
- Update UI as new insights arrive

**Key features**:
- Auto-connect WebSocket when call starts
- Buffer and send transcript chunks (every 5-10 seconds or sentence boundaries)
- Display live sentiment indicator
- Show detected topics in real-time
- Display key insights as they're generated
- Smooth updates without jarring UI changes

**UI Elements**:
- Sentiment gauge (positive/neutral/negative)
- Topic tags (appear/disappear dynamically)
- Insights panel (scrollable, auto-updates)
- Speaking time indicators
- Question markers

### 4.9 Frontend: Integrate WebSocket Streaming

**File**: `frontend/src/lib/components/DailyCall.svelte`

**Changes needed**:

1. **Establish WebSocket connection**:
   ```typescript
   // After joining call
   if (callFrame && isJoined) {
     connectWebSocket(interviewId, token);
   }
   
   // On leave
   if (websocket) {
     websocket.close();
   }
   ```

2. **Capture and send transcript chunks**:
   ```typescript
   callFrame.on("transcription-message", async (event: any) => {
     // Buffer transcript text
     transcriptBuffer += event.text;
     
     // Send chunk every 5 seconds or on sentence boundary
     if (shouldSendChunk()) {
       await sendTranscriptChunk({
         interview_id: interviewId,
         text: transcriptBuffer,
         speaker: event.speaker,
         timestamp: event.timestamp,
         sequence_number: chunkSequence++
       });
       transcriptBuffer = "";
     }
   });
   ```

3. **Handle incoming analysis updates**:
   ```typescript
   websocket.onmessage = (event) => {
     const data = JSON.parse(event.data);
     if (data.type === "analysis_update") {
       updateInsights(data.data);
     }
   };
   ```

### 4.10 Frontend: Add WebSocket Utility

**New File**: `frontend/src/lib/websocket.ts`

**Functions**:
```typescript
export function createTranscriptWebSocket(
  interviewId: string,
  token: string,
  onMessage: (data: any) => void,
  onError: (error: Error) => void
): WebSocket {
  // Create WebSocket connection
  // Handle reconnection logic
  // Return WebSocket instance
}

export async function sendTranscriptChunk(
  websocket: WebSocket,
  chunk: TranscriptChunk
): Promise<void> {
  // Send chunk to backend via WebSocket
}
```

### 4.11 Frontend: Integrate Insights Display

**Files to update**:
- `frontend/src/routes/host/+page.svelte`
- `frontend/src/routes/candidate/+page.svelte` (optional - may want to hide from candidate)

**Changes**:
1. Add `RealTimeInsights` component alongside video call
2. Display insights panel when call is active
3. Show analysis results after call ends (from database)
4. Add toggle to show/hide insights
5. Position insights panel appropriately (sidebar or overlay)

### 4.12 Backend: Database Functions

**File**: `backend/app/db.py`

**New functions**:
```python
def create_transcript_analysis(
    interview_id: UUID,
    analysis_data: dict,
    analysis_type: str,
    transcript_id: Optional[UUID] = None,
    model_used: Optional[str] = None,
    provider: Optional[str] = None,
    status: str = "pending"
) -> dict:
    """Create a new transcript analysis record."""

def get_latest_analysis(
    interview_id: UUID,
    analysis_type: Optional[str] = None
) -> Optional[dict]:
    """Get the latest analysis for an interview."""

def update_analysis(
    analysis_id: UUID,
    analysis_data: Optional[dict] = None,
    status: Optional[str] = None,
    completed_at: Optional[datetime] = None
) -> dict:
    """Update an existing analysis record."""

def get_analysis_history(
    interview_id: UUID,
    limit: int = 50
) -> List[dict]:
    """Get analysis history for an interview."""
```

### 4.13 Configuration

**Environment Variables**:
```bash
# AI Provider Configuration
OPENAI_API_KEY=your_openai_key_here  # For OpenAI analysis
ANTHROPIC_API_KEY=your_anthropic_key  # Optional: For Claude
ANALYSIS_MODEL=gpt-4  # or gpt-3.5-turbo, claude-3-opus, etc.
ANALYSIS_PROVIDER=openai  # or anthropic, custom

# Analysis Settings
ANALYSIS_CHUNK_SIZE=5  # Send chunks every N seconds
ANALYSIS_REALTIME_ENABLED=true
ANALYSIS_FULL_TRANSCRIPT_ENABLED=true
```

---

## Implementation Order

### Phase 1: Real-Time Transcription (Closed Captions)

1. ✅ Backend: Update room creation to enable transcription storage
2. ✅ Frontend: Create `ClosedCaptions.svelte` component
3. ✅ Frontend: Integrate captions into `DailyCall.svelte`
4. ✅ Frontend: Add transcription start/stop logic
5. ✅ Frontend: Add caption toggle controls
6. ✅ Test: Verify captions appear during live calls

### Phase 2: Transcript Storage

1. ✅ Database: Create migration for `interview_transcripts` table
2. ✅ Backend: Create transcript model (`models/transcript.py`)
3. ✅ Backend: Add database functions (`db.py`)
4. ✅ Backend: Add Daily.co transcript fetching function
5. ✅ Backend: Create transcript processing service
6. ✅ Backend: Add endpoint to trigger transcript fetch
7. ✅ Test: Verify transcripts are stored correctly

### Phase 3: REST API Access

1. ✅ Backend: Create transcript retrieval endpoint
2. ✅ Backend: Create transcript download endpoint
3. ✅ Frontend: Create `TranscriptDownload.svelte` component
4. ✅ Frontend: Add transcript API functions
5. ✅ Frontend: Integrate download UI into host/candidate pages
6. ✅ Test: Verify download functionality works

### Phase 4: AI/Agent Interpretation

1. ✅ Database: Create migration for `transcript_analyses` table
2. ✅ Backend: Create analysis model (`models/transcript_analysis.py`)
3. ✅ Backend: Add database functions for analysis storage
4. ✅ Backend: Set up WebSocket support (`api/websocket.py`)
5. ✅ Backend: Create analysis service (`services/analysis_service.py`)
6. ✅ Backend: Implement AI integration (OpenAI/Anthropic)
7. ✅ Backend: Create analysis endpoints
8. ✅ Frontend: Create `RealTimeInsights.svelte` component
9. ✅ Frontend: Add WebSocket utility functions
10. ✅ Frontend: Integrate transcript chunk streaming in `DailyCall.svelte`
11. ✅ Frontend: Integrate insights display in host/candidate pages
12. ✅ Test: Verify real-time analysis works during calls
13. ✅ Test: Verify analysis results are stored correctly

---

## Testing Checklist

### Real-Time Transcription
- [ ] Captions appear during active call
- [ ] Captions update in real-time
- [ ] Captions can be toggled on/off
- [ ] Caption overlay doesn't obstruct video
- [ ] Captions stop when call ends
- [ ] Error handling if transcription fails to start

### Transcript Storage
- [ ] Transcripts are fetched from Daily.co after call
- [ ] WebVTT is parsed correctly to plain text
- [ ] Transcript metadata is extracted correctly
- [ ] Transcripts are stored in database with correct interview_id
- [ ] Handles cases where transcript isn't ready yet
- [ ] Handles transcription failures gracefully

### REST API Access
- [ ] Transcript retrieval endpoint works with authentication
- [ ] Download endpoint returns correct file format
- [ ] Download works for TXT, VTT, and JSON formats
- [ ] Frontend correctly displays transcript status
- [ ] Download button triggers file download
- [ ] Error messages are clear when transcript unavailable

### AI/Agent Interpretation
- [ ] WebSocket connection establishes successfully
- [ ] Transcript chunks are sent to backend in real-time
- [ ] Analysis results stream back to frontend
- [ ] Insights display updates smoothly
- [ ] Sentiment tracking works correctly
- [ ] Topic detection identifies relevant topics
- [ ] Analysis results are stored in database
- [ ] Full transcript analysis works after call ends
- [ ] Error handling for AI API failures
- [ ] Rate limiting prevents excessive API calls
- [ ] WebSocket reconnects automatically on disconnect

---

## Error Handling

### Common Issues

1. **Transcription not starting**:
   - Check Daily.co domain has transcription enabled
   - Verify Deepgram credentials are configured
   - Check browser console for SDK errors

2. **Transcript not available after call**:
   - Daily.co processes transcripts asynchronously (may take 1-5 minutes)
   - Implement retry logic or polling
   - Show "processing" status to users

3. **WebVTT parsing errors**:
   - Validate WebVTT format before parsing
   - Handle malformed transcripts gracefully
   - Log parsing errors for debugging

4. **Storage failures**:
   - Validate database connection
   - Handle duplicate transcript attempts
   - Implement transaction rollback on errors

5. **WebSocket connection issues**:
   - Implement automatic reconnection logic
   - Handle authentication failures gracefully
   - Show connection status to users
   - Fallback to polling if WebSocket unavailable

6. **AI API failures**:
   - Implement retry logic with exponential backoff
   - Handle rate limiting (429 errors)
   - Cache recent analysis results
   - Show "analysis unavailable" status gracefully
   - Log errors for debugging

7. **Analysis performance**:
   - Optimize chunk size for balance between latency and context
   - Use streaming responses from AI APIs when available
   - Cache common analysis patterns
   - Consider using faster models for real-time vs full analysis

---

## Future Enhancements

1. **Speaker Identification**: Display speaker names in captions and transcripts
2. **Search Functionality**: Search within transcripts
3. **Transcript Editing**: Allow users to edit/correct transcripts
4. **Real-time Collaboration**: Share transcripts during calls
5. **Webhook Integration**: Automatic transcript processing via Daily.co webhooks
6. **Transcript Analytics**: Word count, speaking time, sentiment analysis
7. **Export Formats**: PDF, DOCX, SRT (subtitle format)
8. **Transcript Versioning**: Store multiple versions if transcript is updated
9. **AI Analysis Enhancements**:
   - Multi-provider support (fallback if one fails)
   - Custom prompt templates per job role
   - A/B testing different analysis models
   - Confidence scores for insights
   - Explainable AI (why certain insights were generated)
10. **Real-Time Collaboration**: Share insights with multiple viewers during call
11. **Analysis Comparison**: Compare multiple candidates' analysis results
12. **Automated Recommendations**: Generate follow-up questions or next steps

---

## References

- [Daily.co Transcription Documentation](https://docs.daily.co/guides/products/transcription)
- [Daily.co REST API - Transcripts](https://docs.daily.co/reference/rest-api/transcript)
- [Daily.co JavaScript SDK - Transcription Events](https://docs.daily.co/reference/daily-js/instance-methods/start-transcription)
- [WebVTT Format Specification](https://www.w3.org/TR/webvtt1/)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/claude/reference)
- [FastAPI WebSocket Support](https://fastapi.tiangolo.com/advanced/websockets/)
- [Server-Sent Events (SSE) Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## Cost Considerations

### Transcription Costs
- **Real-time transcription**: $0.0059 per unmuted participant minute
- **Post-call transcription**: $0.0043 per recorded minute
- **Free tier**: 10,000 minutes/month included
- **Deepgram**: $150 free credit on signup

Example: A 30-minute interview with 2 participants = ~60 participant-minutes
- Transcription cost: 60 × $0.0059 = $0.35 per interview (after free tier)

### AI Analysis Costs
- **OpenAI GPT-4**: ~$0.03-0.06 per 1K tokens (input + output)
- **OpenAI GPT-3.5-turbo**: ~$0.001-0.002 per 1K tokens
- **Anthropic Claude 3**: ~$0.015-0.075 per 1K tokens (varies by model)

**Cost Estimation**:
- **Real-time analysis** (chunks every 5-10 seconds):
  - ~6-12 API calls per 30-minute interview
  - ~500-1000 tokens per call
  - GPT-3.5-turbo: ~$0.01-0.02 per interview
  - GPT-4: ~$0.15-0.30 per interview

- **Full transcript analysis** (post-call):
  - 1 API call per interview
  - ~2000-5000 tokens per call
  - GPT-3.5-turbo: ~$0.01-0.02 per interview
  - GPT-4: ~$0.10-0.30 per interview

**Total per interview** (30 min, 2 participants):
- Transcription: $0.35
- Real-time analysis (GPT-3.5): $0.02
- Full analysis (GPT-3.5): $0.02
- **Total: ~$0.39 per interview**

**Cost Optimization Tips**:
- Use GPT-3.5-turbo for real-time analysis (faster, cheaper)
- Use GPT-4 only for final comprehensive analysis
- Cache analysis results to avoid duplicate processing
- Implement rate limiting to prevent excessive API calls
- Batch multiple interviews for batch processing (future)

---

## Security Considerations

1. **Authentication**: All transcript endpoints require valid authentication tokens
2. **Authorization**: Users can only access transcripts for interviews they have access to
3. **Data Privacy**: Transcripts contain sensitive interview content - ensure secure storage
4. **API Key Security**: 
   - Keep Daily.co API key server-side only (already implemented)
   - Keep AI provider API keys (OpenAI, Anthropic) server-side only
   - Never expose API keys to frontend
5. **Rate Limiting**: 
   - Rate limit transcript fetch endpoints
   - Rate limit AI analysis endpoints to prevent abuse
   - Implement per-user rate limits
6. **WebSocket Security**:
   - Authenticate WebSocket connections using tokens
   - Validate interview_id ownership on connection
   - Implement connection timeout/cleanup
   - Prevent unauthorized access to analysis streams
7. **Data Handling**:
   - Transcripts sent to AI providers - review their data retention policies
   - Consider using OpenAI/Anthropic with data processing opt-outs if available
   - Log access to sensitive transcript data
   - Implement audit trails for analysis requests
8. **Input Validation**:
   - Sanitize transcript chunks before sending to AI APIs
   - Validate WebSocket message formats
   - Prevent injection attacks in prompts

---

## Notes

- Transcripts are stored in Daily.co's system temporarily - fetch and store in your database for long-term access
- WebVTT format includes timestamps - consider storing structured format (JSON) for better querying
- Daily.co transcription may take a few minutes to process after call ends
- Consider implementing a background job to periodically fetch transcripts for completed calls
- AI analysis can be resource-intensive - monitor API costs and usage
- Real-time analysis provides value during calls, but full transcript analysis post-call may be more accurate
- Consider caching analysis results to reduce API calls and costs
- WebSocket connections should be cleaned up properly when calls end to prevent resource leaks
- AI provider responses may vary - implement fallback strategies for critical analysis features

