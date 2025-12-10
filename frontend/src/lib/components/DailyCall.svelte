<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import DailyIframe from "@daily-co/daily-js";
  import ClosedCaptions from "./ClosedCaptions.svelte";
  import EmotionOverlay from "./EmotionOverlay.svelte";
  import { EmotionDetector, type EmotionScores } from "$lib/emotionDetection";

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
  let showEmotions = false;
  let emotionDetector: EmotionDetector | null = null;
  let isModelsLoading = false;
  let modelsLoaded = false;
  let detectionInterval: number | null = null;
  let localEmotions: EmotionScores | null = null;
  let remoteEmotions: EmotionScores | null = null;
  let localParticipantName: string | null = null;
  let remoteParticipantName: string | null = null;
  // Hidden video elements for emotion detection
  let hiddenVideoElements: Map<string, HTMLVideoElement> = new Map();
  // Store video tracks by participant ID
  let participantVideoTracks: Map<string, MediaStreamTrack> = new Map();
  let trackStartedHandler: ((event: any) => void) | null = null;

  $: if (!roomUrl) {
    error = "Room URL is required";
  } else {
    error = null;
  }

  onMount(async () => {
    // Initialize emotion detector and load models eagerly
    emotionDetector = new EmotionDetector();
    isModelsLoading = true;
    try {
      await emotionDetector.loadModels();
      modelsLoaded = true;
      console.log("[DailyCall] Emotion detection models loaded");
    } catch (e) {
      console.error("[DailyCall] Failed to load emotion models:", e);
    } finally {
      isModelsLoading = false;
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
              // Start emotion detection if enabled
              if (showEmotions && modelsLoaded) {
                // Wait a bit for video tracks to be ready
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
            .on("track-started", (event: any) => {
              // Listen for track-started events to capture video tracks
              if (event.track && event.track.kind === "video") {
                const participantId =
                  event.participant?.session_id ||
                  event.participant?.user_id ||
                  event.participant?.participant_id ||
                  event.participant?.id;
                
                if (participantId && event.track) {
                  console.log(`[DailyCall] Track started for participant ${participantId}`);
                  participantVideoTracks.set(participantId, event.track);
                }
              }
            })
            .on("track-stopped", (event: any) => {
              // Clean up when tracks stop
              if (event.track && event.track.kind === "video") {
                const participantId =
                  event.participant?.session_id ||
                  event.participant?.user_id ||
                  event.participant?.participant_id ||
                  event.participant?.id;
                
                if (participantId) {
                  console.log(`[DailyCall] Track stopped for participant ${participantId}`);
                  participantVideoTracks.delete(participantId);
                }
              }
            })
            .on("left-meeting", async () => {
              isJoined = false;
              isJoining = false;
              isTranscriptionActive = false;
              stopEmotionDetection();

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

  function toggleEmotions() {
    showEmotions = !showEmotions;
    if (showEmotions && isJoined && modelsLoaded) {
      startEmotionDetection();
    } else {
      stopEmotionDetection();
    }
  }

  /**
   * Get video elements from Daily.co participant tracks
   * Creates hidden video elements from participant video tracks
   */
  async function getVideoElements(): Promise<Array<{ element: HTMLVideoElement; participantId: string; name: string }>> {
    const videos: Array<{ element: HTMLVideoElement; participantId: string; name: string }> = [];

    if (!callFrame || !isJoined) {
      return videos;
    }

    try {
      const participants = callFrame.participants();
      if (!participants) {
        return videos;
      }

      const localParticipant = participants.local;
      const allParticipants = Object.values(participants) as any[];

      for (const participant of allParticipants) {
        // Skip if participant doesn't have video track
        if (!participant.tracks?.video) {
          console.log(`[DailyCall] Participant ${participant.session_id || participant.user_id || 'unknown'} has no video track`);
          continue;
        }
        
        if (participant.tracks.video.state !== "playable") {
          console.log(`[DailyCall] Participant ${participant.session_id || participant.user_id || 'unknown'} video track state: ${participant.tracks.video.state}`);
          continue;
        }

        // Try multiple ways to get the video track
        let videoTrack = participant.tracks.video.track;
        
        // If track is not directly available, try to get it from stored tracks (from track-started event)
        if (!videoTrack) {
          const participantId =
            participant.session_id ||
            participant.user_id ||
            participant.participant_id ||
            participant.id;
          videoTrack = participantId ? participantVideoTracks.get(participantId) : undefined;
        }
        
        // If track is not directly available, try to get it from the track object
        if (!videoTrack && participant.tracks.video.persistentTrack) {
          videoTrack = participant.tracks.video.persistentTrack;
        }
        
        // For local participant, try to get from input devices
        if (!videoTrack && participant.local) {
          try {
            const inputDevices = await callFrame.getInputDevices();
            if (inputDevices?.camera) {
              const stream = await navigator.mediaDevices.getUserMedia({ video: true });
              videoTrack = stream.getVideoTracks()[0];
              console.log(`[DailyCall] Got local video track from getUserMedia`);
            }
          } catch (e) {
            console.warn(`[DailyCall] Could not get local video track:`, e);
          }
        }
        
        if (!videoTrack) {
          console.log(`[DailyCall] Participant ${participant.session_id || participant.user_id || 'unknown'} has no accessible video track. Track object:`, participant.tracks.video);
          // Log all properties of the track object to debug
          console.log(`[DailyCall] Available track properties:`, Object.keys(participant.tracks.video));
          console.log(`[DailyCall] Stored tracks:`, Array.from(participantVideoTracks.keys()));
          continue;
        }
        
        console.log(`[DailyCall] Found playable video track for participant ${participant.session_id || participant.user_id || 'unknown'}`);

        // Get participant ID
        const participantId =
          participant.session_id ||
          participant.user_id ||
          participant.participant_id ||
          participant.id ||
          `participant-${Date.now()}`;

        // Get or create hidden video element for this participant
        let videoElement = hiddenVideoElements.get(participantId);

        if (!videoElement) {
          // Create a new hidden video element
          videoElement = document.createElement("video");
          videoElement.autoplay = true;
          videoElement.playsInline = true;
          videoElement.muted = true; // Mute to prevent feedback
          videoElement.style.position = "absolute";
          videoElement.style.width = "1px";
          videoElement.style.height = "1px";
          videoElement.style.opacity = "0";
          videoElement.style.pointerEvents = "none";
          videoElement.style.zIndex = "-1";
          document.body.appendChild(videoElement);
          hiddenVideoElements.set(participantId, videoElement);
        }

        // Update video element with the track if it's not already set
        if (!videoElement.srcObject) {
          const mediaStream = new MediaStream([videoTrack]);
          videoElement.srcObject = mediaStream;
          console.log(`[DailyCall] Created video element for ${name}, waiting for video to load...`);
          
          // Wait for video metadata to load and start playing
          await new Promise<void>((resolve) => {
            const onLoadedMetadata = () => {
              videoElement.removeEventListener("loadedmetadata", onLoadedMetadata);
              // Try to play the video
              videoElement.play().catch((e) => {
                console.warn(`[DailyCall] Could not autoplay video for ${name}:`, e);
              });
              resolve();
            };
            videoElement.addEventListener("loadedmetadata", onLoadedMetadata);
            // Timeout after 5 seconds
            setTimeout(() => {
              videoElement.removeEventListener("loadedmetadata", onLoadedMetadata);
              resolve();
            }, 5000);
          });
        } else {
          // Ensure video is playing
          if (videoElement.paused) {
            videoElement.play().catch((e) => {
              console.warn(`[DailyCall] Could not play video for ${name}:`, e);
            });
          }
        }

        // Check if video is ready and has dimensions
        if (videoElement.readyState >= 2 && videoElement.videoWidth > 0 && videoElement.videoHeight > 0) {
          // Determine participant name
          const isLocal = participant === localParticipant || participant.local === true;
          const name =
            participant.user_name ||
            (isLocal
              ? userRole === "host"
                ? "Host"
                : "Candidate"
              : userRole === "host"
                ? "Candidate"
                : "Host");

          videos.push({ element: videoElement, participantId, name });
        }
      }
    } catch (e) {
      console.warn("[DailyCall] Error getting video elements from tracks:", e);
    }

    return videos;
  }

  /**
   * Start emotion detection loop
   */
  function startEmotionDetection() {
    if (!emotionDetector || !modelsLoaded || !isJoined || detectionInterval !== null) {
      return;
    }

    console.log("[DailyCall] Starting emotion detection");

    // Detection at 10 FPS = 100ms interval
    detectionInterval = window.setInterval(async () => {
      if (!emotionDetector || !isJoined || !showEmotions) {
        return;
      }

      try {
        const videos = await getVideoElements();
        console.log(`[DailyCall] Found ${videos.length} video element(s) for emotion detection`);
        
        if (videos.length === 0) {
          console.log("[DailyCall] No video elements available. Participants:", callFrame?.participants());
          return;
        }
        
        // Detect emotions for each video
        for (const { element, participantId, name } of videos) {
          try {
            console.log(`[DailyCall] Detecting emotions for ${name} (${participantId}), video readyState: ${element.readyState}, dimensions: ${element.videoWidth}x${element.videoHeight}`);
            
            const detection = await emotionDetector.detectEmotions(element, participantId, name);
            
            if (detection) {
              console.log(`[DailyCall] Detected emotions for ${name}:`, detection.emotions);
              
              // Determine if this is local or remote participant
              const participants = callFrame?.participants();
              const localParticipant = participants?.local;
              const isLocal = localParticipant && (
                localParticipant.session_id === participantId ||
                localParticipant.user_id === participantId ||
                localParticipant.participant_id === participantId ||
                localParticipant.id === participantId
              );

              console.log(`[DailyCall] Participant ${name} is ${isLocal ? 'local' : 'remote'}`);

              if (isLocal) {
                localEmotions = detection.emotions;
                localParticipantName = name;
                console.log("[DailyCall] Updated localEmotions:", localEmotions);
              } else {
                remoteEmotions = detection.emotions;
                remoteParticipantName = name;
                console.log("[DailyCall] Updated remoteEmotions:", remoteEmotions);
              }
            } else {
              console.log(`[DailyCall] No face detected for ${name}`);
            }
          } catch (e) {
            console.warn(`[DailyCall] Error detecting emotions for ${name}:`, e);
          }
        }
      } catch (e) {
        console.warn("[DailyCall] Error in emotion detection loop:", e);
      }
    }, 100); // 10 FPS = 100ms
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
    localEmotions = null;
    remoteEmotions = null;
    localParticipantName = null;
    remoteParticipantName = null;

    // Clean up hidden video elements
    hiddenVideoElements.forEach((videoElement) => {
      if (videoElement.srcObject) {
        const stream = videoElement.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
      videoElement.srcObject = null;
      if (videoElement.parentNode) {
        videoElement.parentNode.removeChild(videoElement);
      }
    });
    hiddenVideoElements.clear();
    participantVideoTracks.clear();
  }

  // Auto-start detection when emotions are enabled and call is joined
  $: if (showEmotions && isJoined && modelsLoaded && detectionInterval === null) {
    startEmotionDetection();
  }

  // Stop detection when call ends
  $: if (!isJoined && detectionInterval !== null) {
    stopEmotionDetection();
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
        <button
          on:click={toggleEmotions}
          disabled={!modelsLoaded || isModelsLoading}
          class="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors {showEmotions
            ? 'bg-blue-600 hover:bg-blue-700'
            : 'bg-gray-600 hover:bg-gray-700'} disabled:opacity-50 disabled:cursor-not-allowed"
          title={isModelsLoading
            ? "Loading emotion models..."
            : showEmotions
              ? "Hide Emotions"
              : "Show Emotions"}
        >
          {isModelsLoading
            ? "Loading..."
            : showEmotions
              ? "Hide Emotions"
              : "Show Emotions"}
        </button>
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

      <!-- Emotion Overlays -->
      {#if showEmotions && isJoined && modelsLoaded}
        {#if localEmotions}
          <EmotionOverlay
            emotions={localEmotions}
            participantName={localParticipantName}
            position="top-left"
          />
        {/if}
        {#if remoteEmotions}
          <EmotionOverlay
            emotions={remoteEmotions}
            participantName={remoteParticipantName}
            position="top-right"
          />
        {/if}
      {/if}

      <!-- Loading indicator for models -->
      {#if isModelsLoading}
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
