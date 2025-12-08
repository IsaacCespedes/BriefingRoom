import { error } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { validateToken } from "$lib/api";

export const load: PageServerLoad = async ({ url, cookies }) => {
  const token = url.searchParams.get("token") || cookies.get("token");

  if (!token) {
    throw error(401, "No token provided");
  }

  try {
    const tokenInfo = await validateToken(token);

    if (tokenInfo.role !== "host") {
      throw error(403, "Access denied. Host role required.");
    }

    return {
      role: tokenInfo.role,
      interviewId: tokenInfo.interview_id,
      error: null,
    };
  } catch (err: any) {
    if (err && err.status === 403) {
      throw err;
    }
    throw error(401, err instanceof Error ? err.message : "Token validation failed");
  }
};
