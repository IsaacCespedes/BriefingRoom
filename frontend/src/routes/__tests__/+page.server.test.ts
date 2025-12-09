import { describe, it, expect, vi, beforeEach } from "vitest";
import { load } from "../+page.server";
import { validateToken } from "$lib/api";
import { redirect } from "@sveltejs/kit";

vi.mock("$lib/api");

describe("root +page.server load function", () => {
  const mockUrl = {
    searchParams: {
      get: vi.fn(),
    },
  } as any;

  const mockCookies = {
    get: vi.fn(),
    set: vi.fn(),
  } as any;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return error when no token is provided", async () => {
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(null);

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: null,
      interviewId: null,
      error: "No token provided",
    });
    expect(validateToken).not.toHaveBeenCalled();
  });

  it("should validate token from query parameter", async () => {
    const token = "test-token-123";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(mockCookies.set).toHaveBeenCalledWith("token", token, expect.any(Object));
  });

  it("should validate token from cookie when query parameter is not present", async () => {
    const token = "cookie-token-456";
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(token);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 302,
        location: "/candidate",
      })
    );
  });

  it("should prefer query parameter token over cookie token", async () => {
    const queryToken = "query-token-789";
    const cookieToken = "cookie-token-789";
    mockUrl.searchParams.get.mockReturnValue(queryToken);
    mockCookies.get.mockReturnValue(cookieToken);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-789",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 302,
        location: "/host",
      })
    );
  });

  it("should redirect to /host when token has host role", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 302,
        location: "/host",
      })
    );
  });

  it("should redirect to /candidate when token has candidate role", async () => {
    const token = "candidate-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 302,
        location: "/candidate",
      })
    );
  });

  it("should return role and interview_id for unknown roles", async () => {
    const token = "unknown-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "unknown",
      interview_id: "interview-789",
    });

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: "unknown",
      interviewId: "interview-789",
      error: null,
    });
  });

  it("should handle token validation errors gracefully", async () => {
    const token = "invalid-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockRejectedValue(new Error("Invalid or expired token"));

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: null,
      interviewId: null,
      error: "Invalid or expired token",
    });
  });

  it("should set cookie with correct options", async () => {
    const token = "test-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    try {
      await load({ url: mockUrl, cookies: mockCookies } as any);
    } catch {
      // Ignore redirect error
    }

    expect(mockCookies.set).toHaveBeenCalledWith(
      "token",
      token,
      expect.objectContaining({
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
      })
    );
  });

  it("should re-throw redirect errors", async () => {
    const token = "host-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toEqual(
      expect.objectContaining({
        status: 302,
        location: "/host",
      })
    );
  });
});

