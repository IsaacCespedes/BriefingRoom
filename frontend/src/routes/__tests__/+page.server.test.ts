import { describe, it, expect, vi, beforeEach } from "vitest";
import { load } from "../+page.server";
import { validateToken } from "$lib/api";
import { redirect } from "@sveltejs/kit";

vi.mock("$lib/api");
vi.mock("@sveltejs/kit", async () => {
  const actual = await vi.importActual("@sveltejs/kit");
  return {
    ...actual,
    redirect: vi.fn((status, url) => {
      const error = new Error("Redirect");
      (error as any).status = status;
      (error as any).location = url;
      throw error;
    }),
  };
});

describe("+page.server load function", () => {
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
  });

  it("should validate token from query parameter and redirect host", async () => {
    const token = "host-token-123";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow("Redirect");

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(redirect).toHaveBeenCalledWith(302, "/host");
  });

  it("should validate token from query parameter and redirect candidate", async () => {
    const token = "candidate-token-456";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "candidate",
      interview_id: "interview-456",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow("Redirect");

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(redirect).toHaveBeenCalledWith(302, "/candidate");
  });

  it("should use token from cookie if query parameter is not present", async () => {
    const token = "cookie-token";
    mockUrl.searchParams.get.mockReturnValue(null);
    mockCookies.get.mockReturnValue(token);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-789",
    });

    await expect(load({ url: mockUrl, cookies: mockCookies } as any)).rejects.toThrow("Redirect");

    expect(validateToken).toHaveBeenCalledWith(token);
  });

  it("should handle token validation errors", async () => {
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

  it("should store token in cookie after validation", async () => {
    const token = "valid-token";
    mockUrl.searchParams.get.mockReturnValue(token);
    mockCookies.get.mockReturnValue(null);

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    try {
      await load({ url: mockUrl, cookies: mockCookies } as any);
    } catch (e) {
      // Expected redirect
    }

    expect(mockCookies.set).toHaveBeenCalledWith(
      "token",
      token,
      expect.objectContaining({
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        secure: false, // In test environment, NODE_ENV is not 'production'
      })
    );
  });
});
