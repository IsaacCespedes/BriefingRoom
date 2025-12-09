import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createRoom, getRoomUrl } from "../daily";

describe("daily API client", () => {
  const originalFetch = global.fetch;
  const API_BASE_URL = "http://localhost:8000";
  const mockToken = "test-token-123";

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  describe("createRoom", () => {
    it("should create a Daily.co room successfully", async () => {
      const request = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
      };

      const mockResponse = {
        room_url: "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000",
        room_token: "meeting-token-123",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createRoom(request, mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/daily/create-room`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${mockToken}`,
          },
          body: JSON.stringify(request),
        }
      );

      expect(result).toEqual(mockResponse);
      expect(result.room_url).toBe(
        "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000"
      );
      expect(result.room_token).toBe("meeting-token-123");
    });

    it("should handle response without room_token", async () => {
      const request = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
      };

      const mockResponse = {
        room_url: "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createRoom(request, mockToken);

      expect(result.room_url).toBe(
        "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000"
      );
      expect(result.room_token).toBeUndefined();
    });

    it("should throw error when API returns error response", async () => {
      const request = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
      };

      const errorResponse = {
        detail: "Failed to create room: Interview ID mismatch",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: "Forbidden",
        json: async () => errorResponse,
      });

      await expect(createRoom(request, mockToken)).rejects.toThrow(
        "Failed to create room: Interview ID mismatch"
      );
    });

    it("should handle network errors", async () => {
      const request = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("JSON parse error");
        },
      });

      await expect(createRoom(request, mockToken)).rejects.toThrow("Internal Server Error");
    });

    it("should handle unauthorized access", async () => {
      const request = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
      };

      const errorResponse = {
        detail: "Invalid or expired token",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: async () => errorResponse,
      });

      await expect(createRoom(request, mockToken)).rejects.toThrow(
        "Invalid or expired token"
      );
    });
  });

  describe("getRoomUrl", () => {
    it("should get room URL for an existing interview", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";

      const mockResponse = {
        room_url: "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000",
        room_token: "meeting-token-456",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getRoomUrl(interviewId, mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/daily/room/${interviewId}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );

      expect(result).toEqual(mockResponse);
      expect(result.room_url).toBe(
        "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000"
      );
    });

    it("should handle response without room_token", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";

      const mockResponse = {
        room_url: "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getRoomUrl(interviewId, mockToken);

      expect(result.room_url).toBe(
        "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000"
      );
      expect(result.room_token).toBeUndefined();
    });

    it("should throw error when room not found", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";

      const errorResponse = {
        detail: "Room not found",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => errorResponse,
      });

      await expect(getRoomUrl(interviewId, mockToken)).rejects.toThrow("Room not found");
    });

    it("should throw error on unauthorized access", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";

      const errorResponse = {
        detail: "Invalid or expired token",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: async () => errorResponse,
      });

      await expect(getRoomUrl(interviewId, mockToken)).rejects.toThrow(
        "Invalid or expired token"
      );
    });

    it("should handle network errors gracefully", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("JSON parse error");
        },
      });

      await expect(getRoomUrl(interviewId, mockToken)).rejects.toThrow("Internal Server Error");
    });
  });
});
