import { error } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { validateToken } from "$lib/api";
import { getInterview } from "$lib/interviews";

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

    // Fetch interview details to get job description and resume
    let interview = null;
    try {
      interview = await getInterview(tokenInfo.interview_id, token);
    } catch (err) {
      // If interview fetch fails, we'll still allow access but without interview data
      console.error("Failed to fetch interview details:", err);
    }

    return {
      role: tokenInfo.role,
      interviewId: tokenInfo.interview_id,
      interview: interview,
      error: null,
    };
  } catch (err: any) {
    if (err && err.status === 403) {
      throw err;
    }
    throw error(401, err instanceof Error ? err.message : "Token validation failed");
  }
};
