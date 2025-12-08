import { fail } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { validateToken } from "$lib/api";

export const load: PageServerLoad = async ({ url, cookies }) => {
  const token = url.searchParams.get("token") || cookies.get("token");

  if (!token) {
    return fail(401, {
      error: "No token provided",
      role: null,
      interviewId: null,
    });
  }

  try {
    const tokenInfo = await validateToken(token);

    if (tokenInfo.role !== "candidate") {
      return fail(403, {
        error: "Access denied. Candidate role required.",
        role: tokenInfo.role,
        interviewId: tokenInfo.interview_id,
      });
    }

    return {
      role: tokenInfo.role,
      interviewId: tokenInfo.interview_id,
      error: null,
    };
  } catch (error) {
    return fail(401, {
      error: error instanceof Error ? error.message : "Token validation failed",
      role: null,
      interviewId: null,
    });
  }
};
