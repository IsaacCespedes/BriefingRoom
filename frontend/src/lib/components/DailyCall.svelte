<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import DailyIframe from "@daily-co/daily-js";
  import ClosedCaptions from "./ClosedCaptions.svelte";
  import EmotionOverlay from "./EmotionOverlay.svelte";
  import {
    EmotionDetector,
    type EmotionScores,
    type EmotionDetection,
  } from "$lib/emotionDetection";
  import {
    addEmotionDetection,
    initializeEmotionStorage,
    markEmotionStorageComplete,
    getEmotionStorage,
    emotionsToStructured,
  } from "$lib/emotionStorage";

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

  // Emotion detection state
  // For candidate: always detecting (showEmotions not used, always true)
  // For host: showEmotions controls whether to display received emotions
  let showEmotions = false;
  let emotionDetector: EmotionDetector | null = null;
  let isModelsLoading = false;
  let modelsLoaded = false;
  let detectionInterval: number | null = null;
  // For candidate: stores detected emotions (sent to host)
  // For host: stores received emotions from candidate (displayed)
  let candidateEmotions: EmotionScores | null = null;
  let candidateName: string | null = null;
  // Hidden video element for candidate's own video (candidate side only)
  let localVideoElement: HTMLVideoElement | null = null;
  // App message handler for host to receive emotions (host side only)
  let appMessageHandler: ((event: any) => void) | null = null;

  $: if (!roomUrl) {
    error = "Room URL is required";
  } else {
    error = null;
  }

  onMount(async () => {
    // Only load models on candidate side (they need to detect emotions)
    // Host doesn't need models, just receives emotion data via app messages
    if (userRole === "candidate") {
      emotionDetector = new EmotionDetector();
      isModelsLoading = true;
      try {
        await emotionDetector.loadModels();
        modelsLoaded = true;
        console.log("[DailyCall] Emotion detection models loaded (candidate)");
      } catch (e) {
        console.error("[DailyCall] Failed to load emotion models:", e);
      } finally {
        isModelsLoading = false;
      }
    } else {
      // Host doesn't need models
      modelsLoaded = true;
      console.log(
        "[DailyCall] Host side - no models needed, will receive emotions via app messages"
      );
    }

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
      stopEmotionDetection();
    };
  });

  onDestroy(() => {
    stopEmotionDetection();
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

              // Initialize emotion storage
              // Candidate: stores for backend sync
              // Host: stores locally for display only
              if (interviewId) {
                initializeEmotionStorage(interviewId);
              }

              // Host: Set up listener to receive emotions from candidate
              if (userRole === "host") {
                setupEmotionReceiver();
                // Host defaults to showing emotions
                showEmotions = true;
              }

              // Candidate: Start detection automatically when joined (continuous, no toggle)
              if (userRole === "candidate" && modelsLoaded) {
                // Wait a bit for video to be ready
                setTimeout(() => {
                  startEmotionDetection();
                }, 2000);
              }
            })
            .on("participant-joined", () => {
              // When a participant joins, video tracks may become available
              // Restart detection if it's already running
              if (showEmotions && modelsLoaded && detectionInterval !== null) {
                // Tracks will be picked up in the next detection cycle
              }
            })
            .on("participant-updated", () => {
              // When participant tracks update, ensure we have video elements
              if (showEmotions && modelsLoaded && detectionInterval !== null) {
                // Tracks will be picked up in the next detection cycle
              }
            })
            .on("left-meeting", async () => {
              isJoined = false;
              isJoining = false;
              isTranscriptionActive = false;
              stopEmotionDetection();

              // Clean up app message listener (host side)
              if (userRole === "host" && appMessageHandler) {
                callFrame?.off("app-message", appMessageHandler);
                appMessageHandler = null;
              }

              // Mark transcript as complete and send to backend
              if (interviewId && authToken) {
                await sendTranscriptToBackend();
              }

              // Only candidate sends emotions to backend (they're the source of truth)
              // Host stores emotions locally only for display purposes
              if (userRole === "candidate" && interviewId && authToken) {
                await sendEmotionsToBackend();
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

    // Only candidate sends emotions to backend (they're the source of truth)
    // Host stores emotions locally only for display purposes
    if (userRole === "candidate" && interviewId && authToken) {
      await sendEmotionsToBackend();
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

  /**
   * Store emotion detection in local storage
   */
  async function storeEmotionDetection(
    interviewId: string,
    detection: EmotionDetection
  ): Promise<void> {
    try {
      addEmotionDetection(interviewId, detection);
    } catch (e) {
      console.error("[DailyCall] Error storing emotion detection:", e);
    }
  }

  /**
   * Send emotion detections to backend after call ends
   * Only candidate sends (they're the source of truth)
   * Host stores emotions locally only for display purposes
   */
  async function sendEmotionsToBackend() {
    if (!interviewId || !authToken) return;

    try {
      const storage = getEmotionStorage(interviewId);

      if (!storage || storage.detections.length === 0) {
        console.log("[DailyCall] No emotion detections to send");
        return;
      }

      // Mark as complete
      markEmotionStorageComplete(interviewId);

      const structured = emotionsToStructured(storage);

      // Send to backend
      const response = await fetch(`${API_BASE_URL}/api/emotions/${interviewId}/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          emotion_data: structured,
          source: "local_storage",
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        console.error("[DailyCall] Failed to save emotions:", error);
        // Don't throw - this is a background operation
      } else {
        console.log("[DailyCall] Emotions saved to backend successfully");
      }
    } catch (e) {
      console.error("[DailyCall] Error sending emotions to backend:", e);
      // Don't throw - this is a background operation, local storage still has it
    }
  }

  function toggleCaptions() {
    showCaptions = !showCaptions;
  }

  function toggleEmotions() {
    // Only host can toggle (candidate detection is always on)
    if (userRole === "host") {
      showEmotions = !showEmotions;
      console.log("[DailyCall] Emotion display toggled:", showEmotions);
    } else {
      // Candidate detection runs continuously - no toggle needed
      console.log("[DailyCall] Candidate emotion detection is always active");
    }
  }

  /**
   * Get the candidate's own local video element (candidate side only)
   * Uses getUserMedia to get direct access to the camera stream
   * This is more reliable than trying to extract tracks from Daily.co iframe
   */
  async function getLocalVideoElement(): Promise<HTMLVideoElement | null> {
    if (!isJoined || userRole !== "candidate") {
      return null;
    }

    try {
      // Get or create hidden video element
      if (!localVideoElement) {
        localVideoElement = document.createElement("video");
        localVideoElement.autoplay = true;
        localVideoElement.playsInline = true;
        localVideoElement.muted = true;
        localVideoElement.style.position = "absolute";
        localVideoElement.style.width = "1px";
        localVideoElement.style.height = "1px";
        localVideoElement.style.opacity = "0";
        localVideoElement.style.pointerEvents = "none";
        localVideoElement.style.zIndex = "-1";
        document.body.appendChild(localVideoElement);
      }

      // If video element already has a stream and it's active, use it
      if (localVideoElement.srcObject) {
        const stream = localVideoElement.srcObject as MediaStream;
        const videoTrack = stream.getVideoTracks()[0];
        if (videoTrack && videoTrack.readyState === "live") {
          // Check if video is ready
          if (
            localVideoElement.readyState >= 2 &&
            localVideoElement.videoWidth > 0 &&
            localVideoElement.videoHeight > 0
          ) {
            // Ensure video is playing
            if (localVideoElement.paused) {
              await localVideoElement.play().catch((e) => {
                console.warn("[DailyCall] Could not play local video:", e);
              });
            }
            return localVideoElement;
          }
        } else {
          // Track is not active, get a new stream
          stream.getTracks().forEach((track) => track.stop());
          localVideoElement.srcObject = null;
        }
      }

      // Get user media directly (candidate already granted camera permission for Daily.co)
      // Note: Browser may reuse existing permission from Daily.co
      console.log("[DailyCall] Getting camera stream via getUserMedia");
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: "user", // Front-facing camera
          },
          audio: false, // Don't need audio for emotion detection
        });
      } catch (e: any) {
        if (e.name === "NotAllowedError" || e.name === "PermissionDeniedError") {
          console.error("[DailyCall] Camera permission denied for emotion detection:", e);
        } else if (e.name === "NotFoundError" || e.name === "DevicesNotFoundError") {
          console.error("[DailyCall] No camera found:", e);
        } else {
          console.error("[DailyCall] Error accessing camera:", e);
        }
        // Clean up on error
        if (localVideoElement?.srcObject) {
          const existingStream = localVideoElement.srcObject as MediaStream;
          existingStream.getTracks().forEach((track) => track.stop());
          localVideoElement.srcObject = null;
        }
        return null;
      }

      const videoTrack = stream.getVideoTracks()[0];
      if (!videoTrack) {
        console.log("[DailyCall] No video track in getUserMedia stream");
        stream.getTracks().forEach((track) => track.stop());
        return null;
      }

      // Set the stream on the video element
      localVideoElement.srcObject = stream;

      // Wait for video metadata to load
      await new Promise<void>((resolve) => {
        const onLoadedMetadata = () => {
          localVideoElement?.removeEventListener("loadedmetadata", onLoadedMetadata);
          localVideoElement?.play().catch((e) => {
            console.warn("[DailyCall] Could not autoplay local video:", e);
          });
          resolve();
        };
        localVideoElement?.addEventListener("loadedmetadata", onLoadedMetadata);
        setTimeout(() => {
          localVideoElement?.removeEventListener("loadedmetadata", onLoadedMetadata);
          resolve();
        }, 5000);
      });

      // Check if video is ready
      if (
        localVideoElement.readyState >= 2 &&
        localVideoElement.videoWidth > 0 &&
        localVideoElement.videoHeight > 0
      ) {
        console.log(
          `[DailyCall] Local video element ready: ${localVideoElement.videoWidth}x${localVideoElement.videoHeight}`
        );
        return localVideoElement;
      } else {
        console.log(
          `[DailyCall] Video element not ready yet: readyState=${localVideoElement.readyState}, dimensions=${localVideoElement.videoWidth}x${localVideoElement.videoHeight}`
        );
      }
    } catch (e) {
      console.error("[DailyCall] Error getting local video element:", e);
      // Clean up on error
      if (localVideoElement?.srcObject) {
        const stream = localVideoElement.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
        localVideoElement.srcObject = null;
      }
    }

    return null;
  }

  /**
   * Set up app message receiver for host to receive emotions from candidate
   */
  function setupEmotionReceiver() {
    if (!callFrame || userRole !== "host" || appMessageHandler) {
      return;
    }

    appMessageHandler = (event: any) => {
      // Only process emotion messages
      if (event?.data?.type !== "emotion-detection") {
        return;
      }

      const emotionData = event.data;
      console.log("[DailyCall] Received emotion data from candidate:", emotionData);

      // Update displayed emotions
      if (emotionData.emotions) {
        candidateEmotions = emotionData.emotions;
        candidateName = emotionData.participantName || "Candidate";
        console.log("[DailyCall] Updated candidate emotions for display:", candidateEmotions);

        // Store emotion detection locally for display (host doesn't send to backend,
        // candidate is the source of truth and will send their stored emotions)
        if (interviewId && emotionData.participantId) {
          const detection: EmotionDetection = {
            participantId: emotionData.participantId,
            participantName: emotionData.participantName,
            emotions: emotionData.emotions,
            timestamp: emotionData.timestamp || Date.now(),
          };
          // Host stores locally for display purposes only
          storeEmotionDetection(interviewId, detection);
        }
      }
    };

    callFrame.on("app-message", appMessageHandler);
    console.log("[DailyCall] Set up emotion receiver (host)");
  }

  /**
   * Start emotion detection loop (candidate side only)
   * Detects emotions on candidate's own video and sends to host via app messages
   */
  function startEmotionDetection() {
    // Only run on candidate side
    if (userRole !== "candidate") {
      console.log("[DailyCall] Emotion detection only runs on candidate side");
      return;
    }

    if (!emotionDetector || !modelsLoaded || !isJoined || detectionInterval !== null) {
      return;
    }

    console.log("[DailyCall] Starting emotion detection (candidate side - continuous)");

    // Detection at 5 FPS = 200ms interval
    detectionInterval = window.setInterval(async () => {
      if (!emotionDetector || !isJoined || userRole !== "candidate") {
        return;
      }

      try {
        // Get candidate's own video element
        const videoElement = await getLocalVideoElement();

        if (!videoElement) {
          console.log("[DailyCall] Local video element not ready yet");
          return;
        }

        const participants = callFrame?.participants();
        const localParticipant = participants?.local;
        const participantId =
          localParticipant?.session_id ||
          localParticipant?.user_id ||
          localParticipant?.participant_id ||
          localParticipant?.id ||
          "candidate";
        const participantName = localParticipant?.user_name || "Candidate";

        console.log(
          `[DailyCall] Detecting emotions on own video, readyState: ${videoElement.readyState}, dimensions: ${videoElement.videoWidth}x${videoElement.videoHeight}`
        );

        const detection = await emotionDetector.detectEmotions(
          videoElement,
          participantId,
          participantName
        );

        if (detection) {
          console.log(`[DailyCall] Detected own emotions:`, detection.emotions);

          // Store locally for backend
          if (interviewId) {
            await storeEmotionDetection(interviewId, detection);
          }

          // Send to host via app message
          if (callFrame) {
            try {
              callFrame.sendAppMessage(
                {
                  type: "emotion-detection",
                  participantId: detection.participantId,
                  participantName: detection.participantName,
                  emotions: detection.emotions,
                  timestamp: detection.timestamp,
                },
                "*" // Broadcast to all (host will receive it)
              );
              console.log("[DailyCall] Sent emotion data to host");
            } catch (e) {
              console.warn("[DailyCall] Error sending emotion data:", e);
            }
          }
        } else {
          console.log("[DailyCall] No face detected");
        }
      } catch (e) {
        console.warn("[DailyCall] Error in emotion detection loop:", e);
      }
    }, 200); // 5 FPS = 200ms
  }

  /**
   * Stop emotion detection loop
   */
  function stopEmotionDetection() {
    if (detectionInterval !== null) {
      clearInterval(detectionInterval);
      detectionInterval = null;
      console.log("[DailyCall] Stopped emotion detection");
    }

    // Clean up local video element and stream (candidate side)
    if (localVideoElement) {
      if (localVideoElement.srcObject) {
        const stream = localVideoElement.srcObject as MediaStream;
        // Stop all tracks to release camera
        stream.getTracks().forEach((track) => {
          track.stop();
          console.log("[DailyCall] Stopped video track:", track.label);
        });
      }
      localVideoElement.srcObject = null;
      if (localVideoElement.parentNode) {
        localVideoElement.parentNode.removeChild(localVideoElement);
      }
      localVideoElement = null;
    }

    // Clear emotion state
    candidateEmotions = null;
    candidateName = null;
  }

  // Auto-start detection when call is joined and models are loaded (candidate side - always on)
  $: if (isJoined && modelsLoaded && detectionInterval === null && userRole === "candidate") {
    // Wait a bit for video to be ready
    setTimeout(() => {
      startEmotionDetection();
    }, 2000);
  }

  // Stop detection when call ends
  $: if (!isJoined && detectionInterval !== null) {
    stopEmotionDetection();
  }

  // Ensure host sets up receiver when joined
  $: if (isJoined && userRole === "host" && !appMessageHandler) {
    setupEmotionReceiver();
  }
</script>

<div class="daily-call-container">
  {#if error}
    <div class="px-4 py-3 mb-4 text-red-700 bg-red-50 rounded border border-red-200">
      {error}
    </div>
  {/if}

  <div class="flex flex-col gap-4 items-center">
    {#if !isJoined && !isJoining}
      <button
        on:click={joinCall}
        class="px-6 py-3 font-semibold text-white bg-green-500 rounded-full transition-colors hover:bg-green-600"
        disabled={!!error}
      >
        Join Call
      </button>
    {:else if isJoining}
      <button
        disabled
        class="px-6 py-3 font-semibold text-white bg-gray-500 rounded-full transition-colors cursor-not-allowed"
      >
        Joining...
      </button>
    {:else}
      <div class="flex gap-2 items-center">
        <button
          on:click={toggleCaptions}
          class="px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-lg transition-colors hover:bg-gray-700"
          title={showCaptions ? "Hide Captions" : "Show Captions"}
        >
          {showCaptions ? "Hide Captions" : "Show Captions"}
        </button>
        {#if userRole === "host"}
          <button
            on:click={toggleEmotions}
            class="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors {showEmotions
              ? 'bg-blue-600 hover:bg-blue-700'
              : 'bg-gray-600 hover:bg-gray-700'}"
            title={showEmotions ? "Hide Emotions" : "Show Emotions"}
          >
            {showEmotions ? "Hide Emotions" : "Show Emotions"}
          </button>
        {/if}
        <button
          on:click={leaveCall}
          class="px-6 py-3 font-semibold text-white bg-red-500 rounded-full transition-colors hover:bg-red-600"
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

      <!-- Emotion Overlays (host-only, shows candidate emotions) -->
      {#if showEmotions && isJoined && userRole === "host"}
        {#if candidateEmotions}
          <EmotionOverlay
            emotions={candidateEmotions}
            participantName={candidateName}
            position="top-right"
          />
        {/if}
      {/if}

      <!-- Loading indicator for models (candidate side only) -->
      {#if isModelsLoading && userRole === "candidate"}
        <div
          class="absolute inset-0 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm z-40"
        >
          <div class="text-center text-white">
            <div class="mb-2 text-lg font-semibold">Loading Emotion Detection</div>
            <div class="text-sm text-gray-300">Loading AI models...</div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .daily-call-container {
    @apply p-6 rounded-lg shadow-lg;
  }
</style>
