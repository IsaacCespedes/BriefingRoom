import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { generateBriefing, getInterview } from "../briefing";

describe("briefing API", () => {
  const originalFetch = global.fetch;
  const API_BASE_URL = "http://localhost:8000";
  const mockToken = "test-token";

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  describe("generateBriefing", () => {
    it("should generate a briefing successfully", async () => {
      const request = {
        job_description: "Software Engineer position",
        resume_text: "John Doe has 5 years of experience...",
      };

      const mockResponse = {
        interview_id: "interview-123",
        briefing: "This is a generated briefing about the candidate...",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await generateBriefing(request, mockToken);

      expect(global.fetch).toHaveBeenCalledWith(`${API_BASE_URL}/generate-briefing`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${mockToken}`,
        },
        body: JSON.stringify(request),
      });

      expect(result).toEqual(mockResponse);
    });

    it("should throw error when request fails", async () => {
      const request = {
        job_description: "Software Engineer position",
        resume_text: "John Doe has 5 years of experience...",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => ({ detail: "Failed to generate briefing" }),
      });

      await expect(generateBriefing(request, mockToken)).rejects.toThrow(
        "Failed to generate briefing"
      );
    });

    it("should handle network errors", async () => {
      const request = {
        job_description: "Software Engineer position",
        resume_text: "John Doe has 5 years of experience...",
      };

      (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));

      await expect(generateBriefing(request, mockToken)).rejects.toThrow("Network error");
    });
  });

  describe("getInterview", () => {
    it("should get interview details successfully", async () => {
      const interviewId = "interview-123";
      const mockInterview = {
        id: interviewId,
        created_at: "2024-01-01T00:00:00Z",
        job_description: "Software Engineer position",
        resume_text: "John Doe has 5 years of experience...",
        status: "pending",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockInterview,
      });

      const result = await getInterview(interviewId, mockToken);

      expect(global.fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/interviews/${interviewId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${mockToken}`,
        },
      });

      expect(result).toEqual(mockInterview);
    });

    it("should throw error when interview not found", async () => {
      const interviewId = "non-existent";

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({ detail: "Interview not found" }),
      });

      await expect(getInterview(interviewId, mockToken)).rejects.toThrow("Interview not found");
    });
  });
});
