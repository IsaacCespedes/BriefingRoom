import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createInterview, getInterview } from "../interviews";

describe("interviews API client", () => {
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

  describe("createInterview", () => {
    it("should create an interview and return tokens", async () => {
      const mockRequest = {
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
      };

      const mockResponse = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
        host_token: "host-token-123",
        candidate_token: "candidate-token-456",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createInterview(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/interviews`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(mockRequest),
        }
      );

      expect(result).toEqual(mockResponse);
      expect(result.interview_id).toBe("123e4567-e89b-12d3-a456-426614174000");
      expect(result.host_token).toBe("host-token-123");
      expect(result.candidate_token).toBe("candidate-token-456");
    });

    it("should create an interview with optional status", async () => {
      const mockRequest = {
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
        status: "completed",
      };

      const mockResponse = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
        host_token: "host-token-123",
        candidate_token: "candidate-token-456",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createInterview(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/interviews`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(mockRequest),
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it("should throw error when API returns error response", async () => {
      const mockRequest = {
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
      };

      const errorResponse = {
        detail: "Failed to create interview",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => errorResponse,
      });

      await expect(createInterview(mockRequest)).rejects.toThrow(
        "Failed to create interview"
      );
    });

    it("should handle network errors", async () => {
      const mockRequest = {
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("JSON parse error");
        },
      });

      await expect(createInterview(mockRequest)).rejects.toThrow("Internal Server Error");
    });

    it("should use custom API base URL from environment", async () => {
      const customApiUrl = "http://custom-api:8000";
      const originalEnv = process.env.API_BASE_URL;
      const originalViteEnv = process.env.VITE_API_BASE_URL;
      
      // Set environment variable for server-side code
      process.env.API_BASE_URL = customApiUrl;
      process.env.VITE_API_BASE_URL = customApiUrl;

      const mockRequest = {
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
      };

      const mockResponse = {
        interview_id: "123e4567-e89b-12d3-a456-426614174000",
        host_token: "host-token-123",
        candidate_token: "candidate-token-456",
      };

      // Reload the module to pick up new env var
      vi.resetModules();
      const { createInterview: createInterviewWithCustomUrl } = await import(
        "../interviews"
      );

      // Mock fetch for the reloaded module
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await createInterviewWithCustomUrl(mockRequest);

      expect(global.fetch).toHaveBeenCalledWith(
        `${customApiUrl}/api/interviews`,
        expect.any(Object)
      );

      // Restore original environment
      if (originalEnv) {
        process.env.API_BASE_URL = originalEnv;
      } else {
        delete process.env.API_BASE_URL;
      }
      if (originalViteEnv) {
        process.env.VITE_API_BASE_URL = originalViteEnv;
      } else {
        delete process.env.VITE_API_BASE_URL;
      }
    });
  });

  describe("getInterview", () => {
    it("should fetch interview details with token", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";
      const token = "test-token-123";

      const mockResponse = {
        id: interviewId,
        job_description: "Software Engineer",
        resume_text: "John Doe resume",
        status: "pending",
        created_at: "2024-01-01T00:00:00Z",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getInterview(interviewId, token);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/interviews/${interviewId}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      expect(result).toEqual(mockResponse);
      expect(result.id).toBe(interviewId);
      expect(result.job_description).toBe("Software Engineer");
    });

    it("should throw error when interview not found", async () => {
      const interviewId = "non-existent-id";
      const token = "test-token-123";

      const errorResponse = {
        detail: "Interview not found",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => errorResponse,
      });

      await expect(getInterview(interviewId, token)).rejects.toThrow(
        "Interview not found"
      );
    });

    it("should throw error on unauthorized access", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";
      const token = "invalid-token";

      const errorResponse = {
        detail: "Unauthorized",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: async () => errorResponse,
      });

      await expect(getInterview(interviewId, token)).rejects.toThrow(
        "Unauthorized"
      );
    });

    it("should handle network errors gracefully", async () => {
      const interviewId = "123e4567-e89b-12d3-a456-426614174000";
      const token = "test-token-123";

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("JSON parse error");
        },
      });

      await expect(getInterview(interviewId, token)).rejects.toThrow("Internal Server Error");
    });
  });
});

