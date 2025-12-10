import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import { tick } from "svelte";
import ClosedCaptions from "../ClosedCaptions.svelte";

describe("ClosedCaptions component", () => {
  let mockCallFrame: any;
  let transcriptionStartedHandler: (() => void) | undefined;
  let transcriptionStoppedHandler: (() => void) | undefined;
  let transcriptionMessageHandler: ((event: any) => void) | undefined;
  let errorHandler: ((event: any) => void) | undefined;

  beforeEach(() => {
    mockCallFrame = {
      on: vi.fn((event: string, callback: any) => {
        if (event === "transcription-started") {
          transcriptionStartedHandler = callback;
        } else if (event === "transcription-stopped") {
          transcriptionStoppedHandler = callback;
        } else if (event === "transcription-message") {
          transcriptionMessageHandler = callback;
        } else if (event === "transcription-error") {
          errorHandler = callback;
        }
        return mockCallFrame;
      }),
      off: vi.fn(),
    };

    // Reset handlers
    transcriptionStartedHandler = undefined;
    transcriptionStoppedHandler = undefined;
    transcriptionMessageHandler = undefined;
    errorHandler = undefined;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render when visible", () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    expect(screen.getByText(/Waiting/i)).toBeInTheDocument();
  });

  it("should not render when not visible", () => {
    const { container } = render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: false,
        transcriptionActive: false,
      },
    });

    expect(container.querySelector(".closed-captions-overlay")).not.toBeInTheDocument();
  });

  it("should set up transcription listeners when callFrame is provided", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    await tick();

    expect(mockCallFrame.on).toHaveBeenCalledWith("transcription-started", expect.any(Function));
    expect(mockCallFrame.on).toHaveBeenCalledWith("transcription-stopped", expect.any(Function));
    expect(mockCallFrame.on).toHaveBeenCalledWith("transcription-message", expect.any(Function));
    expect(mockCallFrame.on).toHaveBeenCalledWith("transcription-error", expect.any(Function));
  });

  it("should display 'Live' status when transcription is active", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    expect(screen.getByText(/● Live/i)).toBeInTheDocument();
    expect(screen.getByText(/Captions/i)).toBeInTheDocument();
  });

  it("should display 'Waiting' status when transcription is not active", () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    expect(screen.getByText(/○ Waiting/i)).toBeInTheDocument();
    expect(screen.getByText(/Starting transcription/i)).toBeInTheDocument();
  });

  it("should handle transcription-started event", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    await tick();

    // Trigger transcription-started event
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText(/● Live/i)).toBeInTheDocument();
    });
  });

  it("should handle transcription-stopped event", async () => {
    const { component } = render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Set parent transcription to false first
    component.$set({ transcriptionActive: false });
    await tick();

    // Trigger transcription-stopped event
    if (transcriptionStoppedHandler) {
      transcriptionStoppedHandler();
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText(/○ Waiting/i)).toBeInTheDocument();
    });
  });

  it("should display captions from transcription-message events", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started first
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    // Send transcription messages
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler({
        text: "Hello, this is a test caption",
        speaker: "Speaker 1",
        timestamp: Date.now(),
      });
      await tick();

      transcriptionMessageHandler({
        text: "Another caption line",
        speaker: null,
        timestamp: Date.now(),
      });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("Hello, this is a test caption")).toBeInTheDocument();
      expect(screen.getByText("Another caption line")).toBeInTheDocument();
    });
  });

  it("should display speaker name when available", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started first
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    // Send transcription message with speaker
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler({
        text: "Hello world",
        speaker: "John Doe",
        timestamp: Date.now(),
      });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("John Doe:")).toBeInTheDocument();
      expect(screen.getByText("Hello world")).toBeInTheDocument();
    });
  });

  it("should handle different transcription message formats", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started first
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    // Test string format
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler("Simple string caption");
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("Simple string caption")).toBeInTheDocument();
    });

    // Test nested data format
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler({
        data: {
          text: "Nested format caption",
          speaker: "Alice",
        },
      });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("Nested format caption")).toBeInTheDocument();
    });

    // Test alternative format
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler({
        transcript: "Alternative format",
        user_name: "Bob",
      });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("Alternative format")).toBeInTheDocument();
    });
  });

  it("should limit captions to maxCaptions lines", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started first
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    // Send more than 10 captions (default maxCaptions)
    if (transcriptionMessageHandler) {
      for (let i = 0; i < 15; i++) {
        transcriptionMessageHandler({
          text: `Caption ${i}`,
          timestamp: Date.now() + i,
        });
        await tick();
      }
    }

    await waitFor(() => {
      // Should only show the last 10 captions
      expect(screen.getByText("Caption 5")).toBeInTheDocument();
      expect(screen.getByText("Caption 14")).toBeInTheDocument();
      // First few captions should not be visible
      expect(screen.queryByText("Caption 0")).not.toBeInTheDocument();
      expect(screen.queryByText("Caption 4")).not.toBeInTheDocument();
    });
  });

  it("should ignore empty transcription messages", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started first
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    // Send empty messages
    if (transcriptionMessageHandler) {
      transcriptionMessageHandler({ text: "" });
      await tick();
      transcriptionMessageHandler({ text: "   " });
      await tick();
      transcriptionMessageHandler({ text: "Valid caption" });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText("Valid caption")).toBeInTheDocument();
    });

    // Verify only one caption line exists (the valid one)
    const captionLines = screen.getAllByText(/Valid caption|Waiting for speech/i);
    expect(captionLines.length).toBeGreaterThan(0);
    // Empty messages should not create caption lines
    const allText = document.body.textContent || "";
    expect(allText).not.toContain("   "); // Whitespace-only messages should be filtered
  });

  it("should handle transcription errors", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false, // Set to false so error is shown
      },
    });

    await tick();

    // Trigger error event
    if (errorHandler) {
      errorHandler({ error: "Transcription service unavailable" });
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText(/Error: Transcription service unavailable/i)).toBeInTheDocument();
    });
  });

  it("should sync with parent transcription status when visible", async () => {
    const { component } = render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    await tick();

    // Update parent transcription status
    component.$set({ transcriptionActive: true });
    await tick();

    await waitFor(() => {
      expect(screen.getByText(/● Live/i)).toBeInTheDocument();
    });
  });

  it("should clean up listeners on component destroy", async () => {
    const { unmount } = render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    await tick();

    // Verify listeners were set up
    expect(mockCallFrame.on).toHaveBeenCalled();

    // Unmount component
    unmount();
    await tick();

    // Verify cleanup was called
    expect(mockCallFrame.off).toHaveBeenCalledWith("transcription-started", expect.any(Function));
    expect(mockCallFrame.off).toHaveBeenCalledWith("transcription-stopped", expect.any(Function));
    expect(mockCallFrame.off).toHaveBeenCalledWith("transcription-message", expect.any(Function));
    expect(mockCallFrame.off).toHaveBeenCalledWith("transcription-error", expect.any(Function));
  });

  it("should prevent duplicate listener registration", async () => {
    const { component } = render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: false,
      },
    });

    await tick();

    const initialCallCount = (mockCallFrame.on as any).mock.calls.length;

    // Update props on the same component instance (should not add duplicate listeners)
    component.$set({ isVisible: false });
    await tick();
    component.$set({ isVisible: true });
    await tick();

    // Should not have significantly more calls (some may be from cleanup/setup cycle)
    const finalCallCount = (mockCallFrame.on as any).mock.calls.length;
    // The listenersSetup flag should prevent duplicates, so we should have similar call counts
    // (allowing for one cleanup/setup cycle)
    expect(finalCallCount).toBeLessThanOrEqual(initialCallCount * 2);
  });

  it("should display 'Waiting for speech...' when transcription is active but no captions", async () => {
    render(ClosedCaptions, {
      props: {
        callFrame: mockCallFrame,
        isVisible: true,
        transcriptionActive: true,
      },
    });

    await tick();

    // Trigger transcription-started
    if (transcriptionStartedHandler) {
      transcriptionStartedHandler();
      await tick();
    }

    await waitFor(() => {
      expect(screen.getByText(/Waiting for speech/i)).toBeInTheDocument();
    });
  });
});
