/**
 * API client functions for interview review management.
 */

import { browser } from "$app/environment";

/**
 * Get the API base URL, handling both client-side and server-side contexts.
 */
function getApiBaseUrl(): string {
  if (browser) {
    return import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  } else {
    // @ts-ignore - process is available in Node.js runtime
    const apiUrl = process.env?.API_BASE_URL || process.env?.VITE_API_BASE_URL;
    return apiUrl || "http://backend:8000";
  }
}

export interface GenerateReviewRequest {
  transcript_text?: string;  // Optional: can provide transcript text directly (e.g., from local storage)
}

export interface GenerateReviewResponse {
  interview_id: string;
  review_id: string;
  review: string;
}

export interface GetReviewResponse {
  interview_id: string;
  review_id: string;
  review: string;
  created_at: string;
}

/**
 * Generate an interview review based on the transcript.
 * 
 * @param interviewId - The interview ID
 * @param token - Authentication token
 * @param transcriptText - Optional transcript text (e.g., from local storage). If provided, will be used directly instead of fetching from database.
 */
export async function generateReview(
  interviewId: string,
  token: string,
  transcriptText?: string
): Promise<GenerateReviewResponse> {
  const apiUrl = getApiBaseUrl();
  
  const body: GenerateReviewRequest = {};
  if (transcriptText) {
    body.transcript_text = transcriptText;
  }
  
  const response = await fetch(`${apiUrl}/api/interviews/${interviewId}/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to generate review: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get the interview review if it exists.
 */
export async function getReview(
  interviewId: string,
  token: string
): Promise<GetReviewResponse> {
  const apiUrl = getApiBaseUrl();
  const response = await fetch(`${apiUrl}/api/interviews/${interviewId}/review`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to get review: ${response.statusText}`);
  }

  return response.json();
}
