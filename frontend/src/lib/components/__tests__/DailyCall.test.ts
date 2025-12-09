import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import { tick } from "svelte";
import DailyCall from "../DailyCall.svelte";
import DailyIframe from "@daily-co/daily-js";

vi.mock("@daily-co/daily-js", () => ({
  default: {
    createFrame: vi.fn(),
  },
}));

describe("DailyCall component", () => {
  let mockCallFrame: any;
  let joinedMeetingCallback: (() => void) | undefined;

  beforeEach(() => {
    mockCallFrame = {
      join: vi.fn().mockResolvedValue(undefined),
      leave: vi.fn(),
      destroy: vi.fn(),
      on: vi.fn((event, callback) => {
        if (event === "joined-meeting") {
          joinedMeetingCallback = callback;
        }
        return mockCallFrame;
      }),
    };

    (DailyIframe.createFrame as any).mockReturnValue(mockCallFrame);

    // Mock DOM methods
    document.getElementById = vi.fn();
    joinedMeetingCallback = undefined; // Reset for each test
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render join button when not joined", () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    expect(screen.getByText("Join Call")).toBeInTheDocument();
  });

  it("should display error when roomUrl is not provided", () => {
    render(DailyCall, {
      props: {
        roomUrl: "",
      },
    });

    expect(screen.getByText(/Room URL is required/i)).toBeInTheDocument();
    expect(screen.getByText("Join Call")).toBeDisabled();
  });

  it("should initialize Daily.co frame when join button is clicked", async () => {
    const { container } = render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(DailyIframe.createFrame).toHaveBeenCalled();
    });
  });

  it("should show joining state while connecting", async () => {
    // Mock a delayed join
    mockCallFrame.join = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(resolve, 100);
        })
    );

    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    // Should show "Joining..." state
    await waitFor(() => {
      expect(screen.getByText("Joining...")).toBeInTheDocument();
    });
  });

  it("should join call with room URL and token when provided", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
        token: "test-token-123",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(mockCallFrame.join).toHaveBeenCalledWith({
        url: "https://test.daily.co/test-room",
        token: "test-token-123",
      });
    });
  });

  it("should join call without token when token is not provided", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
        token: null,
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(mockCallFrame.join).toHaveBeenCalledWith({
        url: "https://test.daily.co/test-room",
      });
    });
  });

  it("should not include token when token is empty string", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
        token: "",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(mockCallFrame.join).toHaveBeenCalledWith({
        url: "https://test.daily.co/test-room",
      });
      expect(mockCallFrame.join).not.toHaveBeenCalledWith(
        expect.objectContaining({
          token: expect.anything(),
        })
      );
    });
  });

  it("should register event handlers when frame is created", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(mockCallFrame.on).toHaveBeenCalledWith("joined-meeting", expect.any(Function));
      expect(mockCallFrame.on).toHaveBeenCalledWith("left-meeting", expect.any(Function));
      expect(mockCallFrame.on).toHaveBeenCalledWith("error", expect.any(Function));
    });
  });

  it("should show leave button when joined", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    // Wait for the join to be called
    await waitFor(() => {
      expect(mockCallFrame.join).toHaveBeenCalled();
    });

    // Simulate joined event by calling the callback that was registered
    // The component chains .on() calls, so we need to find the handler from the mock
    const onCalls = (mockCallFrame.on as any).mock.calls;
    const joinedCall = onCalls.find((call: any[]) => call[0] === "joined-meeting");
    const joinedHandler = joinedCall?.[1];

    if (joinedHandler) {
      joinedHandler();
      await tick(); // Ensure component re-renders after state change
      await tick(); // Extra tick for Svelte reactivity
    }

    await waitFor(() => {
      expect(screen.getByText("Leave Call")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("should call leave when leave button is clicked", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    // Wait for the join to be called
    await waitFor(() => {
      expect(mockCallFrame.join).toHaveBeenCalled();
    });

    // Simulate joined event by calling the callback that was registered
    const onCalls = (mockCallFrame.on as any).mock.calls;
    const joinedCall = onCalls.find((call: any[]) => call[0] === "joined-meeting");
    const joinedHandler = joinedCall?.[1];

    if (joinedHandler) {
      joinedHandler();
      await tick(); // Ensure component re-renders after state change
      await tick(); // Extra tick for Svelte reactivity
    }

    await waitFor(() => {
      expect(screen.getByText("Leave Call")).toBeInTheDocument();
    }, { timeout: 3000 });

    const leaveButton = screen.getByText("Leave Call");
    await fireEvent.click(leaveButton);

    expect(mockCallFrame.leave).toHaveBeenCalled();
  });

  it("should display error message on join error", async () => {
    const errorMessage = "Failed to join room";
    mockCallFrame.join = vi.fn().mockRejectedValue(new Error(errorMessage));

    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it("should display error from event handler", async () => {
    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(mockCallFrame.on).toHaveBeenCalled();
    });

    // Simulate error event
    const errorHandler = (mockCallFrame.on as any).mock.calls.find(
      (call: any[]) => call[0] === "error"
    )?.[1];

    if (errorHandler) {
      errorHandler({ errorMsg: "Connection failed" });
    }

    await waitFor(() => {
      expect(screen.getByText("Connection failed")).toBeInTheDocument();
    });
  });

  it("should prevent multiple join attempts", async () => {
    mockCallFrame.join = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(resolve, 500);
        })
    );

    render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);
    await fireEvent.click(joinButton); // Try clicking again
    await fireEvent.click(joinButton); // Try clicking again

    await waitFor(() => {
      // Should only be called once despite multiple clicks
      expect(mockCallFrame.join).toHaveBeenCalledTimes(1);
    });
  });

  it("should destroy frame on component unmount", async () => {
    const { unmount } = render(DailyCall, {
      props: {
        roomUrl: "https://test.daily.co/test-room",
      },
    });

    const joinButton = screen.getByText("Join Call");
    await fireEvent.click(joinButton);

    await waitFor(() => {
      expect(DailyIframe.createFrame).toHaveBeenCalled();
    });

    unmount();

    expect(mockCallFrame.destroy).toHaveBeenCalled();
  });
});

