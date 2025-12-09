import { describe, it, expect, vi, beforeEach } from "vitest";
import { load } from "../../candidate/+page.server";
import { validateToken } from "$lib/api";
import { error } from "@sveltejs/kit";

vi.mock("$lib/api");

describe("candidate +page.server load function", () => {
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

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 401,
        body: {
          message: "No token provided",
        },
      })
    );
  });

  it("should return role and interview_id for valid candidate token", async () => {
    const token = "candidate-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-123",
    });

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: "candidate",
      interviewId: "interview-123",
      error: null,
    });
    expect(validateToken).toHaveBeenCalledWith(token);
  });

  it("should return 403 when token has host role", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 403,
        body: {
          message: "Access denied. Candidate role required.",
        },
      })
    );
  });

  it("should return 401 when token validation fails", async () => {
    const token = "invalid-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockRejectedValue(new Error("Invalid or expired token"));

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 401,
        body: {
          message: "Invalid or expired token",
        },
      })
    );
  });

  it("should use token from cookie if query parameter is not present", async () => {
    const token = "cookie-token";
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(token);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-789",
    });

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(result.role).toBe("candidate");
    expect(result.interviewId).toBe("interview-789");
  });

  it("should prefer query parameter token over cookie token", async () => {
    const queryToken = "query-token";
    const cookieToken = "cookie-token";
    mockUrl.searchParams.get.mockReturnValue(queryToken);
    mockCookies.get.mockReturnValue(cookieToken);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-999",
    });

    await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(validateToken).toHaveBeenCalledWith(queryToken);
    expect(validateToken).not.toHaveBeenCalledWith(cookieToken);
  });

  it("should handle unknown roles by returning 403", async () => {
    const token = "unknown-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "unknown",
      interview_id: "interview-111",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 403,
        body: {
          message: "Access denied. Candidate role required.",
        },
      })
    );
  });

  it("should re-throw 403 errors", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 403,
        body: {
          message: "Access denied. Candidate role required.",
        },
      })
    );
  });
});

