/**
 * API client functions for interview management.
 */

import type { Interview } from "./types";
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

export interface CreateInterviewRequest {
  job_description: string;
  resume_text: string;
  status?: string;
}

export interface CreateInterviewResponse {
  interview_id: string;
  host_token: string;
  candidate_token: string;
}

/**
 * Create a new interview and generate tokens.
 */
export async function createInterview(
  request: CreateInterviewRequest
): Promise<CreateInterviewResponse> {
  const apiUrl = getApiBaseUrl();
  const response = await fetch(`${apiUrl}/api/interviews`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to create interview: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get interview details by ID.
 */
export async function getInterview(interviewId: string, token: string): Promise<Interview> {
  const apiUrl = getApiBaseUrl();
  const response = await fetch(`${apiUrl}/api/interviews/${interviewId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to get interview: ${response.statusText}`);
  }

  return response.json();
}

