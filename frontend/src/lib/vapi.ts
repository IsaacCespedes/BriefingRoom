const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface VapiPublicKeyResponse {
  public_key: string;
}

export interface CreateCallRequest {
  assistantId: string;
  assistantOverrides?: {
    variableValues?: Record<string, any>;
    [key: string]: any;
  };
  [key: string]: any;
}

export interface CallResponse {
  id: string;
  [key: string]: any;
}

/**
 * Get the Vapi public key for frontend SDK initialization
 */
export async function getVapiPublicKey(token: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/vapi/public-key`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to get Vapi public key: ${response.statusText}`);
  }

  const data: VapiPublicKeyResponse = await response.json();
  return data.public_key;
}

/**
 * Create a Vapi call (convenience function)
 */
export async function createVapiCall(
  request: CreateCallRequest,
  token: string
): Promise<CallResponse> {
  const response = await fetch(`${API_BASE_URL}/api/vapi/call`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to create Vapi call: ${response.statusText}`);
  }

  return response.json();
}

