const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface CreateRoomRequest {
  interview_id: string;
}

export interface CreateRoomResponse {
  room_url: string;
  room_token?: string;
}

/**
 * Create a Daily.co room for an interview
 */
export async function createRoom(
  request: CreateRoomRequest,
  token: string
): Promise<CreateRoomResponse> {
  const response = await fetch(`${API_BASE_URL}/api/daily/create-room`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to create room: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get room URL for an interview
 */
export async function getRoomUrl(interviewId: string, token: string): Promise<CreateRoomResponse> {
  const response = await fetch(`${API_BASE_URL}/api/daily/room/${interviewId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to get room URL: ${response.statusText}`);
  }

  return response.json();
}
