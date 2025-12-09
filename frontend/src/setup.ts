import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock environment variables for tests
// Set default API base URL for tests to use localhost
if (typeof process !== "undefined") {
  process.env.API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";
  process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || "http://localhost:8000";
}

// Mock $app/environment to return browser: false for server-side code in tests
vi.mock("$app/environment", () => ({
  browser: false,
  dev: false,
  building: false,
  version: "1.0.0",
}));
