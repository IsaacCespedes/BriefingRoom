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
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
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

  it("should not initialize Daily.co call frame on mount", async () => {
    const DailyIframe = await import("@daily-co/daily-js");

    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    expect(DailyIframe.default.createFrame).not.toHaveBeenCalled();
  });

  it("should handle join call action and show leave button", async () => {
    const DailyIframe = await import("@daily-co/daily-js");

    render(DailyCall, {
      props: {
        roomUrl: mockRoomUrl,
        token: mockToken,
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    vi.runAllTimers();

    await waitFor(() => {
      expect(DailyIframe.default.createFrame).toHaveBeenCalled();
      expect(screen.getByText("Leave Call")).toBeInTheDocument();
    });
  });
});
