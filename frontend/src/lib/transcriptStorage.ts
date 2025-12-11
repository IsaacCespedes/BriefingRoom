/**
 * Local storage service for transcript segments.
 * 
 * Stores transcript segments in local storage as they arrive during the call.
 * This provides immediate access and handles cases where the call is suddenly closed.
 */

export interface TranscriptSegment {
  id: number;
  text: string;
  speaker: string | null;
  participantId?: string | null; // Daily.co participant ID if available
  timestamp: number; // Unix timestamp in milliseconds
  sequenceNumber: number; // Order in which segments arrived
}

export interface StoredTranscript {
  interviewId: string;
  roomName: string;
  segments: TranscriptSegment[];
  startedAt: number; // Unix timestamp
  lastUpdatedAt: number; // Unix timestamp
  isComplete: boolean; // Whether the call has ended
}

const STORAGE_PREFIX = "transcript_";
const MAX_STORAGE_SIZE = 5 * 1024 * 1024; // 5MB limit per transcript

/**
 * Get storage key for an interview
 */
function getStorageKey(interviewId: string): string {
  return `${STORAGE_PREFIX}${interviewId}`;
}

/**
 * Initialize transcript storage for an interview
 */
export function initializeTranscript(interviewId: string, roomName: string): void {
  const key = getStorageKey(interviewId);
  const transcript: StoredTranscript = {
    interviewId,
    roomName,
    segments: [],
    startedAt: Date.now(),
    lastUpdatedAt: Date.now(),
    isComplete: false,
  };
  
  try {
    localStorage.setItem(key, JSON.stringify(transcript));
  } catch (e) {
    console.error("[TranscriptStorage] Failed to initialize transcript:", e);
    // If storage is full, try to clear old transcripts
    clearOldTranscripts();
    try {
      localStorage.setItem(key, JSON.stringify(transcript));
    } catch (e2) {
      console.error("[TranscriptStorage] Failed after cleanup:", e2);
    }
  }
}

/**
 * Add a segment to the transcript
 */
export function addTranscriptSegment(
  interviewId: string,
  segment: Omit<TranscriptSegment, "sequenceNumber">
): void {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) {
      console.warn("[TranscriptStorage] Transcript not initialized, initializing now");
      initializeTranscript(interviewId, `interview-${interviewId}`);
      // Retry after initialization
      addTranscriptSegment(interviewId, segment);
      return;
    }
    
    const transcript: StoredTranscript = JSON.parse(stored);
    const sequenceNumber = transcript.segments.length;
    
    const newSegment: TranscriptSegment = {
      ...segment,
      sequenceNumber,
    };
    
    transcript.segments.push(newSegment);
    transcript.lastUpdatedAt = Date.now();
    
    // Check storage size
    const size = JSON.stringify(transcript).length;
    if (size > MAX_STORAGE_SIZE) {
      console.warn("[TranscriptStorage] Transcript approaching size limit, keeping only recent segments");
      // Keep only the most recent 1000 segments
      transcript.segments = transcript.segments.slice(-1000);
    }
    
    localStorage.setItem(key, JSON.stringify(transcript));
  } catch (e) {
    console.error("[TranscriptStorage] Failed to add segment:", e);
  }
}

/**
 * Mark transcript as complete (call ended)
 */
export function markTranscriptComplete(interviewId: string): void {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return;
    
    const transcript: StoredTranscript = JSON.parse(stored);
    transcript.isComplete = true;
    transcript.lastUpdatedAt = Date.now();
    
    localStorage.setItem(key, JSON.stringify(transcript));
  } catch (e) {
    console.error("[TranscriptStorage] Failed to mark complete:", e);
  }
}

/**
 * Get transcript from local storage
 */
export function getTranscript(interviewId: string): StoredTranscript | null {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return null;
    
    return JSON.parse(stored) as StoredTranscript;
  } catch (e) {
    console.error("[TranscriptStorage] Failed to get transcript:", e);
    return null;
  }
}

/**
 * Convert stored transcript to plain text with timestamps
 */
export function transcriptToText(transcript: StoredTranscript): string {
  return transcript.segments
    .map((segment) => {
      // Format timestamp as [YYYY-MM-DD HH:MM:SS]
      const timestamp = new Date(segment.timestamp);
      const timestampStr = timestamp.toISOString().replace("T", " ").substring(0, 19);
      
      if (segment.speaker) {
        return `[${timestampStr}] ${segment.speaker}: ${segment.text}`;
      }
      return `[${timestampStr}] ${segment.text}`;
    })
    .join("\n");
}

/**
 * Convert stored transcript to structured format (for backend)
 */
export function transcriptToStructured(transcript: StoredTranscript): {
  segments: Array<{
    speaker: string | null;
    participantId?: string | null;
    text: string;
    start_time: number; // Seconds since start
    end_time: number; // Seconds since start
    timestamp: number; // Unix timestamp
  }>;
  started_at: string; // ISO timestamp
  ended_at: string | null; // ISO timestamp
  duration_seconds: number;
} {
  const startTime = transcript.startedAt;
  const endTime = transcript.isComplete ? transcript.lastUpdatedAt : Date.now();
  
  const segments = transcript.segments.map((segment) => {
    const relativeStartTime = (segment.timestamp - startTime) / 1000; // Convert to seconds
    // Estimate end time (could be improved with actual duration from Daily.co)
    const relativeEndTime = relativeStartTime + 5; // Assume 5 seconds per segment
    
    return {
      speaker: segment.speaker,
      participantId: segment.participantId || undefined,
      text: segment.text,
      start_time: relativeStartTime,
      end_time: relativeEndTime,
      timestamp: segment.timestamp,
    };
  });
  
  return {
    segments,
    started_at: new Date(startTime).toISOString(),
    ended_at: transcript.isComplete ? new Date(endTime).toISOString() : null,
    duration_seconds: Math.floor((endTime - startTime) / 1000),
  };
}

/**
 * Clear transcript from local storage
 */
export function clearTranscript(interviewId: string): void {
  const key = getStorageKey(interviewId);
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.error("[TranscriptStorage] Failed to clear transcript:", e);
  }
}

/**
 * Clear old transcripts (keep only the 10 most recent)
 */
function clearOldTranscripts(): void {
  try {
    const keys = Object.keys(localStorage).filter((key) => key.startsWith(STORAGE_PREFIX));
    
    if (keys.length <= 10) return;
    
    // Get all transcripts with their last updated times
    const transcripts = keys
      .map((key) => {
        try {
          const stored = localStorage.getItem(key);
          if (!stored) return null;
          const transcript: StoredTranscript = JSON.parse(stored);
          return { key, lastUpdated: transcript.lastUpdatedAt };
        } catch {
          return null;
        }
      })
      .filter((t): t is { key: string; lastUpdated: number } => t !== null);
    
    // Sort by last updated (oldest first)
    transcripts.sort((a, b) => a.lastUpdated - b.lastUpdated);
    
    // Remove oldest transcripts (keep 10 most recent)
    const toRemove = transcripts.slice(0, transcripts.length - 10);
    toRemove.forEach(({ key }) => localStorage.removeItem(key));
    
    console.log(`[TranscriptStorage] Cleared ${toRemove.length} old transcripts`);
  } catch (e) {
    console.error("[TranscriptStorage] Failed to clear old transcripts:", e);
  }
}

/**
 * Get all stored transcript IDs
 */
export function getAllTranscriptIds(): string[] {
  try {
    const keys = Object.keys(localStorage).filter((key) => key.startsWith(STORAGE_PREFIX));
    return keys.map((key) => key.replace(STORAGE_PREFIX, ""));
  } catch (e) {
    console.error("[TranscriptStorage] Failed to get transcript IDs:", e);
    return [];
  }
}
