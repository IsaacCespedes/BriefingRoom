import { fail, redirect } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { validateToken } from "$lib/api";

export const load: PageServerLoad = async ({ url, cookies }) => {
  // Get token from query parameter or cookie
  const token = url.searchParams.get("token") || cookies.get("token");

  if (!token) {
    return {
      role: null,
      interviewId: null,
      error: "No token provided",
    };
  }

  try {
    // Validate token with backend
    const tokenInfo = await validateToken(token);

    // Store token in cookie for subsequent requests
    cookies.set("token", token, {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    // Redirect based on role
    if (tokenInfo.role === "host") {
      throw redirect(302, `/host`);
    } else if (tokenInfo.role === "candidate") {
      throw redirect(302, `/candidate`);
    }

    return {
      role: tokenInfo.role,
      interviewId: tokenInfo.interview_id,
      error: null,
    };
  } catch (error: any) {
    // If it's a redirect, re-throw it
    if (error && error.status >= 300 && error.status < 400 && error.location) {
      throw error;
    }

    // Otherwise, return error
    return {
      role: null,
      interviewId: null,
      error: error instanceof Error ? error.message : "Token validation failed",
    };
  }
};
