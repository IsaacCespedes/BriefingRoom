import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { validateToken } from "../api";

describe("validateToken", () => {
  const originalFetch = global.fetch;
  const API_BASE_URL = "http://localhost:8000";

  beforeEach(() => {
    global.fetch = vi.fn();
    // Set environment variable for tests
    if (typeof process !== "undefined") {
      process.env.API_BASE_URL = API_BASE_URL;
      process.env.VITE_API_BASE_URL = API_BASE_URL;
    }
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  it("should validate a token and return role and interview_id", async () => {
    const mockToken = "test-token-123";
    const mockResponse = {
      role: "host",
      interview_id: "interview-uuid-123",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await validateToken(mockToken);

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/validate-token?token=${encodeURIComponent(mockToken)}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    expect(result).toEqual(mockResponse);
  });

  it("should throw error for invalid token (401)", async () => {
    const mockToken = "invalid-token";

    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    });

    await expect(validateToken(mockToken)).rejects.toThrow("Invalid or expired token");
  });

  it("should throw error for other HTTP errors", async () => {
    const mockToken = "test-token";

    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    await expect(validateToken(mockToken)).rejects.toThrow(
      "Token validation failed: Internal Server Error"
    );
  });

  it("should handle candidate role", async () => {
    const mockToken = "candidate-token";
    const mockResponse = {
      role: "candidate",
      interview_id: "interview-uuid-456",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await validateToken(mockToken);

    expect(result.role).toBe("candidate");
    expect(result.interview_id).toBe("interview-uuid-456");
  });
});
