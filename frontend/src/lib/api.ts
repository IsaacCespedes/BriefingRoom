import type { TokenInfo } from "./types";
import { browser } from "$app/environment";

/**
 * Get the API base URL, handling both client-side and server-side contexts.
 * In Docker, server-side code should use the service name 'backend'.
 * Client-side code uses the configured VITE_API_BASE_URL.
 */
function getApiBaseUrl(): string {
  if (browser) {
    // Client-side: use VITE_ variable
    return import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  } else {
    // Server-side: use process.env (works in Docker)
    // In Docker, use the service name 'backend' to reach the backend container
    // @ts-ignore - process is available in Node.js runtime
    const apiUrl = process.env?.API_BASE_URL || process.env?.VITE_API_BASE_URL;
    return apiUrl || "http://backend:8000";
  }
}

/**
 * Validates a token and returns the role and interview_id
 */
export async function validateToken(token: string): Promise<TokenInfo> {
  const API_BASE_URL = getApiBaseUrl();
  const response = await fetch(
    `${API_BASE_URL}/api/validate-token?token=${encodeURIComponent(token)}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Invalid or expired token");
    }
    throw new Error(`Token validation failed: ${response.statusText}`);
  }

  return response.json();
}
