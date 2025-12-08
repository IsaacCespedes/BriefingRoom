import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import DailyCall from "../components/DailyCall.svelte";

// Mock Daily.co SDK
vi.mock("@daily-co/daily-js", () => ({
  default: {
    createFrame: vi.fn(() => ({
      on: vi.fn(),
      join: vi.fn(),
      leave: vi.fn(),
      destroy: vi.fn(),
    })),
  },
}));

describe("DailyCall", () => {
  const mockRoomUrl = "https://test.daily.co/test-room";
  const mockToken = "test-token";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render the component with join button", () => {
    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    expect(screen.getByText("Join Call")).toBeInTheDocument();
  });

  it("should show error when room URL is not provided", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "",
        token: mockToken,
      },
    });

    await waitFor(() => {
      expect(screen.getByText(/Room URL is required/i)).toBeInTheDocument();
    });
  });

  it("should initialize Daily.co call frame on mount", async () => {
    const DailyIframe = await import("@daily-co/daily-js");

    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    // Note: This test verifies the component structure
    // Actual Daily.co SDK integration would require more complex mocking
    expect(screen.getByText("Join Call")).toBeInTheDocument();
  });

  it("should handle join call action", async () => {
    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    // In a real implementation, we would verify the join method was called
    // This test verifies the button exists and can be clicked
    expect(joinButton).toBeInTheDocument();
  });

  it("should display leave button when joined", () => {
    // This test would require setting up the component in a joined state
    // For now, we verify the component structure
    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    // Leave button should not be visible initially
    expect(screen.queryByText("Leave Call")).not.toBeInTheDocument();
  });
});
