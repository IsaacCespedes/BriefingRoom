import { describe, it, expect, vi, beforeEach } from "vitest";
import { load } from "../+page.server";
import { validateToken } from "$lib/api";
import { HttpError } from "@sveltejs/kit";

vi.mock("$lib/api");

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

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-123",
    });

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(result).toEqual({
      role: "host",
      interviewId: "interview-123",
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

    vi.mocked(validateToken).mockResolvedValue({
      role: "host",
      interview_id: "interview-789",
    });

    const result = await load({ url: mockUrl, cookies: mockCookies } as any);

    expect(validateToken).toHaveBeenCalledWith(token);
    expect(result.role).toBe("host");
  });
});
