<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import DailyIframe from "@daily-co/daily-js";
  import ClosedCaptions from "./ClosedCaptions.svelte";

  export let roomUrl: string;
  export let token: string | null = null; // Daily.co room token (for joining the call)
  export let authToken: string | null = null; // Authentication token (for backend API calls)
  export let interviewId: string | null = null; // Pass interview ID explicitly
  export let userRole: "host" | "candidate" | null = null; // User's role for transcript labeling

  let isJoined = false;
  let isJoining = false;
  let error: string | null = null;
  let callFrame: any = null;
  let frameElement: HTMLDivElement | null = null;
  let showFrame = false;
  let showCaptions = true;
  let isTranscriptionActive = false;
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  $: if (!roomUrl) {
    error = "Room URL is required";
  } else {
    error = null;
  }

  onMount(() => {
    // Initialize the frame element reference when component mounts
    return () => {
      if (callFrame) {
        try {
          callFrame.destroy();
        } catch (e) {
          // Ignore errors during cleanup
        }
        callFrame = null;
      }
    };
  });

  onDestroy(() => {
    if (callFrame) {
      try {
        callFrame.destroy();
      } catch (e) {
        // Ignore errors during cleanup
      }
      callFrame = null;
    }
  });

  async function joinCall() {
    if (!roomUrl) {
      error = "Room URL is required";
      return;
    }

    if (isJoining || isJoined) {
      return; // Prevent multiple join attempts
    }

    isJoining = true;
    showFrame = true; // Show frame element before initializing
    error = null;

    try {
      // Wait for Svelte to update the DOM and ensure element is rendered
      await tick();

      // Give the browser a moment to render the element
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Ensure the frame element exists and is in the DOM
      if (!frameElement) {
        // Fallback: try to get element by ID
        frameElement = document.getElementById("daily-call-frame") as HTMLDivElement;
      }

      if (!frameElement || !frameElement.isConnected) {
        throw new Error("Daily call frame element not found or not in DOM.");
      }

      // Create frame if it doesn't exist
      if (!callFrame) {
        try {
          callFrame = DailyIframe.createFrame(frameElement, {
            showLeaveButton: true,
            iframeStyle: {
              position: "relative",
              width: "100%",
              height: "100%",
              border: "0",
            },
          });

          callFrame
            .on("joined-meeting", async () => {
              isJoined = true;
              isJoining = false;
              error = null;
              // Start transcription after joining
              await startTranscription();
            })
            .on("left-meeting", async () => {
              isJoined = false;
              isJoining = false;
              isTranscriptionActive = false;

              // Mark transcript as complete and send to backend
              if (interviewId && authToken) {
                await sendTranscriptToBackend();
              }

              // Don't try to stop transcription here - we've already left
              // The call will end when all participants leave, and Daily.co will process the transcript
            })
            .on("error", (e: any) => {
              error = e?.errorMsg || e?.error || "An error occurred during the call";
              isJoined = false;
              isJoining = false;
              isTranscriptionActive = false;
            });
        } catch (e) {
          error = e instanceof Error ? e.message : "Failed to initialize Daily.co";
          isJoining = false;
          return;
        }
      }

      // Only include token if it's a non-empty string
      const joinOptions: { url: string; token?: string } = { url: roomUrl };
      if (token && typeof token === "string" && token.trim() !== "") {
        joinOptions.token = token;
      }

      await callFrame.join(joinOptions);
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to join call";
      isJoined = false;
      isJoining = false;
    }
  }

  async function startTranscription() {
    if (!isJoined) {
      console.warn("[DailyCall] Cannot start transcription: not joined to call");
      return;
    }

    // Extract interview ID from either prop or room URL
    let idToUse = interviewId;
    if (!idToUse && roomUrl) {
      // Try to extract from URL format: https://domain.daily.co/interview-{uuid}
      const match = roomUrl.match(/interview-([a-f0-9-]+)/i);
      idToUse = match ? match[1] : null;
    }

    if (!idToUse) {
      console.error("[DailyCall] Cannot start transcription: interview ID not available");
      error = "Interview ID not available. Cannot start transcription.";
      return;
    }

    if (!authToken) {
      console.error("[DailyCall] Cannot start transcription: authToken not available");
      error = "Authentication token not available. Cannot start transcription.";
      return;
    }

    try {
      console.log("[DailyCall] Starting transcription via REST API for interview:", idToUse);
      // Wait a bit for the call to fully initialize
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Use REST API to start transcription (more reliable than SDK with Daily Prebuilt)
      // This uses the backend API key which has full permissions
      const response = await fetch(`${API_BASE_URL}/api/daily/start-transcription/${idToUse}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        const errorMessage =
          errorData.detail || `Failed to start transcription: ${response.statusText}`;

        // Check if error is about active stream - this is fine, transcription is already running
        if (
          errorMessage.toLowerCase().includes("active stream") ||
          errorMessage.toLowerCase().includes("already")
        ) {
          console.log(
            "[DailyCall] Transcription already active (this is expected when second person joins)"
          );
          isTranscriptionActive = true;
          error = null; // Don't show error for this case
          return;
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("[DailyCall] Transcription started via REST API:", data);

      // Check if response indicates transcription was already active
      if (data.status === "already_active") {
        console.log("[DailyCall] Transcription was already active");
      }

      isTranscriptionActive = true;
      error = null; // Clear any previous errors
    } catch (e: any) {
      const errorMessage =
        e?.message || "Failed to start transcription. Please check Daily.co settings.";

      // Suppress error if it's about active stream
      if (
        errorMessage.toLowerCase().includes("active stream") ||
        errorMessage.toLowerCase().includes("already")
      ) {
        console.log("[DailyCall] Transcription already active, suppressing error");
        isTranscriptionActive = true;
        error = null; // Don't show error
        return;
      }

      console.error("[DailyCall] Failed to start transcription:", e);
      isTranscriptionActive = false;
      // Only show error for actual failures, not for "already active" cases
      error = errorMessage;
    }
  }

  function stopTranscription() {
    if (!callFrame || !isJoined) {
      // Only stop transcription if we're actually joined
      return;
    }

    try {
      callFrame.stopTranscription();
      isTranscriptionActive = false;
    } catch (e) {
      // Silently ignore errors - transcription may have already stopped
      // or the call may have already ended
      console.warn("Could not stop transcription (call may have already ended):", e);
    }
  }

  async function leaveCall() {
    // Stop transcription before leaving
    stopTranscription();

    // Mark transcript as complete and send to backend
    if (interviewId && authToken) {
      await sendTranscriptToBackend();
    }

    if (callFrame) {
      try {
        callFrame.leave();
      } catch (e) {
        error = e instanceof Error ? e.message : "Failed to leave call";
      }
    }
    isJoined = false;
    isJoining = false;
    showFrame = false;
    isTranscriptionActive = false;
  }

  async function sendTranscriptToBackend() {
    if (!interviewId || !authToken) return;

    try {
      const { getTranscript, transcriptToStructured } = await import("$lib/transcriptStorage");
      const transcript = getTranscript(interviewId);

      if (!transcript || transcript.segments.length === 0) {
        console.log("[DailyCall] No transcript segments to send");
        return;
      }

      const structured = transcriptToStructured(transcript);

      // Send to backend
      const response = await fetch(`${API_BASE_URL}/api/transcripts/${interviewId}/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          transcript_data: structured,
          source: "local_storage", // Indicate this came from local storage
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        console.error("[DailyCall] Failed to save transcript:", error);
        // Don't throw - this is a background operation
      } else {
        console.log("[DailyCall] Transcript saved to backend successfully");
      }
    } catch (e) {
      console.error("[DailyCall] Error sending transcript to backend:", e);
      // Don't throw - this is a background operation, local storage still has it
    }
  }

  function toggleCaptions() {
    showCaptions = !showCaptions;
  }
</script>

<div class="daily-call-container">
  {#if error}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  <div class="flex flex-col items-center gap-4">
    {#if !isJoined && !isJoining}
      <button
        on:click={joinCall}
        class="px-6 py-3 rounded-full text-white font-semibold bg-green-500 hover:bg-green-600 transition-colors"
        disabled={!!error}
      >
        Join Call
      </button>
    {:else if isJoining}
      <button
        disabled
        class="px-6 py-3 rounded-full text-white font-semibold bg-gray-500 cursor-not-allowed transition-colors"
      >
        Joining...
      </button>
    {:else}
      <div class="flex gap-2 items-center">
        <button
          on:click={toggleCaptions}
          class="px-4 py-2 rounded-lg text-white font-medium bg-gray-600 hover:bg-gray-700 transition-colors text-sm"
          title={showCaptions ? "Hide Captions" : "Show Captions"}
        >
          {showCaptions ? "Hide Captions" : "Show Captions"}
        </button>
        <button
          on:click={leaveCall}
          class="px-6 py-3 rounded-full text-white font-semibold bg-red-500 hover:bg-red-600 transition-colors"
        >
          Leave Call
        </button>
      </div>
    {/if}

    <!-- Always render the frame element - Daily.co needs it in the DOM -->
    <div
      bind:this={frameElement}
      class="relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden {showFrame || isJoined
        ? ''
        : 'hidden'}"
      id="daily-call-frame"
    >
      <!-- Daily.co iframe will be inserted here -->

      <!-- Closed Captions Overlay -->
      <!-- Always render to capture transcription events, even when hidden -->
      {#if callFrame && isJoined}
        <ClosedCaptions
          {callFrame}
          isVisible={showCaptions}
          transcriptionActive={isTranscriptionActive}
          {interviewId}
          {userRole}
        />
      {/if}
    </div>
  </div>
</div>

<style>
  .daily-call-container {
    @apply p-6 bg-white rounded-lg shadow-lg;
  }
</style>
