import { describe, it, expect, vi, beforeEach } from "vitest";
import { load } from "../+page.server";
import { validateToken } from "$lib/api";
import { getInterview } from "$lib/interviews";
import { HttpError } from "@sveltejs/kit";

vi.mock("$lib/api");
vi.mock("$lib/interviews");

describe("host +page.server load function", () => {
  const mockUrl = {
    searchParams: {
      get: vi.fn(),
    },
  } as any;

  const mockCookies = {
    get: vi.fn(),
  } as any;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return 401 when no token is provided", async () => {
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(null);

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow(HttpError);
    await load({ url: mockUrl, cookies: mockCookies } as any).catch((e: HttpError) => {
      expect(e.status).toBe(401);
      expect(e.body.message).toBe("No token provided");
    });
  });

  it("should return role and interview_id for valid host token", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    const mockInterview = {
      id: "interview-123",
      job_description: "Software Engineer",
      resume_text: "John Doe resume",
      status: "pending",
      created_at: "2024-01-01T00:00:00Z",
    };

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    vi.mocked(getInterview).mockResolvedValue(mockInterview);

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: "host",
      interviewId: "interview-123",
      interview: mockInterview,
      error: null,
    });
  });

  it("should return 403 when token has candidate role", async () => {
    const token = "candidate-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow(HttpError);
    await load({ url: mockUrl, cookies: mockCookies } as any).catch((e: HttpError) => {
      expect(e.status).toBe(403);
      expect(e.body.message).toBe("Access denied. Host role required.");
    });
  });

  it("should return 401 when token validation fails", async () => {
    const token = "invalid-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockRejectedValue(new Error("Invalid or expired token"));

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow(HttpError);
    await load({ url: mockUrl, cookies: mockCookies } as any).catch((e: HttpError) => {
      expect(e.status).toBe(401);
      expect(e.body.message).toBe("Invalid or expired token");
    });
  });

  it("should use token from cookie if query parameter is not present", async () => {
    const token = "cookie-token";
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(token);

    const mockInterview = {
      id: "interview-789",
      job_description: "Software Engineer",
      resume_text: "John Doe resume",
      status: "pending",
      created_at: "2024-01-01T00:00:00Z",
    };

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-789",
    });

    vi.mocked(getInterview).mockResolvedValue(mockInterview);

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(result.role).toBe("host");
    expect(result.interview).toEqual(mockInterview);
  });

  it("should handle interview fetch failure gracefully", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    vi.mocked(getInterview).mockRejectedValue(new Error("Interview not found"));

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: "host",
      interviewId: "interview-123",
      interview: null,
      error: null,
    });
  });
});
