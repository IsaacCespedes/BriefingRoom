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
  job_description?: string;
  resume_text?: string;
  status?: string;
  // For file uploads
  job_description_file?: File;
  resume_file?: File;
  // For URL inputs
  job_description_url?: string;
  resume_url?: string;
  // Source types
  job_description_type?: "text" | "file" | "url";
  resume_type?: "text" | "file" | "url";
}

export interface CreateInterviewResponse {
  interview_id: string;
  host_token: string;
  candidate_token: string;
}

/**
 * Create a new interview and generate tokens.
 * Supports text, file uploads, and URLs.
 */
export async function createInterview(
  request: CreateInterviewRequest
): Promise<CreateInterviewResponse> {
  const apiUrl = getApiBaseUrl();
  
  // Check if we have file uploads - use FormData for multipart
  const hasFiles = request.job_description_file || request.resume_file;
  
  if (hasFiles) {
    // Use FormData for file uploads
    const formData = new FormData();
    
    if (request.job_description_file) {
      formData.append("job_description", request.job_description_file);
      formData.append("job_description_type", "file");
    } else if (request.job_description_url) {
      formData.append("job_description_text", request.job_description_url);
      formData.append("job_description_type", "url");
    } else if (request.job_description) {
      formData.append("job_description_text", request.job_description);
      formData.append("job_description_type", "text");
    }
    
    if (request.resume_file) {
      formData.append("resume_text", request.resume_file);
      formData.append("resume_type", "file");
    } else if (request.resume_url) {
      formData.append("resume_text_value", request.resume_url);
      formData.append("resume_type", "url");
    } else if (request.resume_text) {
      formData.append("resume_text_value", request.resume_text);
      formData.append("resume_type", "text");
    }
    
    if (request.status) {
      formData.append("status", request.status);
    }
    
    const response = await fetch(`${apiUrl}/api/interviews`, {
      method: "POST",
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to create interview: ${response.statusText}`);
    }
    
    return response.json();
  } else {
    // Use JSON for text/URL inputs
    const jsonBody: any = {
      status: request.status || "pending",
    };
    
    // Handle job description
    if (request.job_description_url) {
      jsonBody.job_description_path = request.job_description_url;
      jsonBody.job_description_source = "url";
    } else if (request.job_description) {
      jsonBody.job_description = request.job_description;
      jsonBody.job_description_source = "text";
    }
    
    // Handle resume
    if (request.resume_url) {
      jsonBody.resume_path = request.resume_url;
      jsonBody.resume_source = "url";
    } else if (request.resume_text) {
      jsonBody.resume_text = request.resume_text;
      jsonBody.resume_source = "text";
    }
    
    const response = await fetch(`${apiUrl}/api/interviews`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(jsonBody),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Failed to create interview: ${response.statusText}`);
    }

    return response.json();
  }
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

