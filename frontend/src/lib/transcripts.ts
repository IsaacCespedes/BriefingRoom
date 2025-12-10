const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface TranscriptResponse {
  id: string;
  interview_id: string;
  daily_room_name: string;
  transcript_text: string;
  transcript_webvtt?: string;
  transcript_data?: {
    segments?: Array<{
      speaker?: string;
      text: string;
      start_time: number;
      end_time: number;
    }>;
  };
  started_at?: string;
  ended_at?: string;
  duration_seconds?: number;
  participant_count?: number;
  status: string;
  created_at: string;
  updated_at: string;
}

/**
 * Get transcript for an interview
 */
export async function getTranscript(
  interviewId: string,
  token: string
): Promise<TranscriptResponse> {
  const response = await fetch(`${API_BASE_URL}/api/transcripts/${interviewId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to get transcript: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Download transcript for an interview in various formats
 * 
 * @param interviewId - The interview ID
 * @param format - Format: 'txt', 'vtt', or 'json'
 * @param token - Authentication token
 * @returns Blob that can be downloaded
 */
export async function downloadTranscript(
  interviewId: string,
  format: "txt" | "vtt" | "json",
  token: string
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/transcripts/${interviewId}/download?format=${format}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to download transcript: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * Trigger fetching transcript from Daily.co and storing in database
 * 
 * This calls the backend endpoint that fetches from Daily.co API
 * and stores the transcript in the database.
 */
export async function fetchTranscriptFromDaily(
  interviewId: string,
  token: string
): Promise<TranscriptResponse> {
  const response = await fetch(`${API_BASE_URL}/api/daily/fetch-transcript/${interviewId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch transcript: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Helper function to trigger a file download from a blob
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
