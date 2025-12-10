<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let callFrame: any;
  export let isVisible: boolean = true;
  export let transcriptionActive: boolean = false; // Pass transcription status from parent

  let captions: Array<{
    id: number;
    text: string;
    speaker: string | null;
    timestamp: number;
  }> = [];
  let captionIdCounter = 0;
  let isTranscriptionActive = false;
  let maxCaptions = 10; // Keep last 10 caption lines
  let debugInfo = "";

  // Keep track of transcription event handlers
  let transcriptionStartedHandler: (() => void) | null = null;
  let transcriptionStoppedHandler: (() => void) | null = null;
  let transcriptionMessageHandler: ((event: any) => void) | null = null;
  let errorHandler: ((event: any) => void) | null = null;
  let appMessageHandler: ((event: any) => void) | null = null;
  let listenersSetup = false; // Track if listeners have been set up to prevent duplicates

  onMount(() => {
    // Set up listeners when component mounts or when callFrame becomes available
    if (callFrame) {
      setupTranscriptionListeners();
    }
  });

  onDestroy(() => {
    cleanupTranscriptionListeners();
  });

  function setupTranscriptionListeners() {
    if (!callFrame) {
      console.warn("[ClosedCaptions] callFrame not available yet");
      return;
    }

    // Prevent duplicate listener registration
    if (listenersSetup) {
      console.warn("[ClosedCaptions] Listeners already set up, skipping");
      return;
    }

    // Clean up any existing listeners first (just in case)
    cleanupTranscriptionListeners();

    console.log("[ClosedCaptions] Setting up transcription listeners");

    transcriptionStartedHandler = () => {
      console.log("[ClosedCaptions] Transcription started event received");
      isTranscriptionActive = true;
      captions = []; // Clear previous captions
      captionIdCounter = 0;
      debugInfo = "Transcription active";
    };

    transcriptionStoppedHandler = () => {
      console.log("[ClosedCaptions] Transcription stopped event received");
      isTranscriptionActive = false;
      debugInfo = "Transcription stopped";
    };

    // Sync with parent's transcription status when it becomes visible or when parent status changes
    // This handles the case where transcription was started before component was visible
    $: if (isVisible && transcriptionActive && !isTranscriptionActive) {
      console.log("[ClosedCaptions] Syncing with parent transcription status");
      isTranscriptionActive = true;
    }

    // Also sync when parent status becomes false
    $: if (!transcriptionActive && isTranscriptionActive) {
      console.log("[ClosedCaptions] Syncing with parent - transcription stopped");
      isTranscriptionActive = false;
    }

    transcriptionMessageHandler = (event: any) => {
      console.log("[ClosedCaptions] Transcription message:", event);

      // Handle different event formats
      let text = "";
      let speaker = null;

      if (typeof event === "string") {
        // If event is just a string
        text = event;
      } else if (event?.text) {
        // Standard format
        text = event.text;
        speaker = event.speaker || null;
      } else if (event?.data?.text) {
        // Nested data format
        text = event.data.text;
        speaker = event.data.speaker || null;
      } else if (event?.transcript) {
        // Alternative format
        text = event.transcript;
        speaker = event.user_name || null;
      }

      if (!text || !text.trim()) {
        console.warn("[ClosedCaptions] Empty text in transcription message:", event);
        return;
      }

      // Add new caption
      const newCaption = {
        id: captionIdCounter++,
        text: text.trim(),
        speaker: speaker,
        timestamp: event.timestamp || event.time || Date.now(),
      };

      captions = [...captions, newCaption];

      // Keep only the last maxCaptions lines
      if (captions.length > maxCaptions) {
        captions = captions.slice(-maxCaptions);
      }

      // Auto-scroll to bottom (handled by CSS)
      requestAnimationFrame(() => {
        const container = document.getElementById("captions-container");
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    };

    errorHandler = (event: any) => {
      console.error("[ClosedCaptions] Transcription error:", event);
      debugInfo = `Error: ${event?.error || "Unknown error"}`;
    };

    // Register event listeners
    // Only register the standard transcription-message event to avoid duplicates
    try {
      callFrame.on("transcription-started", transcriptionStartedHandler);
      callFrame.on("transcription-stopped", transcriptionStoppedHandler);
      callFrame.on("transcription-message", transcriptionMessageHandler);
      callFrame.on("transcription-error", errorHandler);

      // Only register app-message if needed, and make sure it's a separate handler
      appMessageHandler = (event: any) => {
        // Only process if it's a transcription message and we haven't already handled it
        if (event?.type === "transcription" || event?.type === "transcription-message") {
          // Check if this is the same as the transcription-message event to avoid duplicates
          // The transcription-message event should handle most cases
          console.log("[ClosedCaptions] App message transcription event (may be duplicate)");
        }
      };
      // Don't register app-message by default - only use transcription-message
      // callFrame.on("app-message", appMessageHandler);

      listenersSetup = true;
      console.log("[ClosedCaptions] Event listeners registered");
    } catch (e) {
      console.error("[ClosedCaptions] Error setting up listeners:", e);
    }
  }

  function cleanupTranscriptionListeners() {
    if (!callFrame) return;

    try {
      if (transcriptionStartedHandler) {
        callFrame.off("transcription-started", transcriptionStartedHandler);
      }
      if (transcriptionStoppedHandler) {
        callFrame.off("transcription-stopped", transcriptionStoppedHandler);
      }
      if (transcriptionMessageHandler) {
        callFrame.off("transcription-message", transcriptionMessageHandler);
      }
      if (errorHandler) {
        callFrame.off("transcription-error", errorHandler);
      }
      if (appMessageHandler) {
        callFrame.off("app-message", appMessageHandler);
      }

      listenersSetup = false;
    } catch (e) {
      console.error("[ClosedCaptions] Error cleaning up listeners:", e);
    }
  }

  // Watch for callFrame changes and set up listeners once when it becomes available
  $: if (callFrame && !listenersSetup) {
    setupTranscriptionListeners();
  }
</script>

{#if isVisible}
  <div class="closed-captions-overlay">
    <div class="captions-header">
      {#if isTranscriptionActive || transcriptionActive}
        <span class="captions-status">● Live</span>
        <span class="captions-label">Captions</span>
      {:else}
        <span class="captions-status" style="color: #fbbf24">○ Waiting</span>
        <span class="captions-label">Starting transcription...</span>
      {/if}
    </div>
    {#if isTranscriptionActive || transcriptionActive}
      <div id="captions-container" class="captions-container">
        {#if captions.length === 0}
          <div class="caption-line" style="opacity: 0.6; font-style: italic;">
            Waiting for speech...
          </div>
        {:else}
          {#each captions as caption (caption.id)}
            <div class="caption-line">
              {#if caption.speaker}
                <span class="caption-speaker">{caption.speaker}:</span>
              {/if}
              <span class="caption-text">{caption.text}</span>
            </div>
          {/each}
        {/if}
      </div>
    {:else}
      <div class="captions-container" style="opacity: 0.6;">
        {#if debugInfo}
          <div class="caption-line" style="font-size: 0.85rem;">
            {debugInfo}
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .closed-captions-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(
      to top,
      rgba(0, 0, 0, 0.85) 0%,
      rgba(0, 0, 0, 0.7) 80%,
      transparent 100%
    );
    color: white;
    padding: 1rem 1.5rem;
    z-index: 100;
    pointer-events: none;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .captions-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    opacity: 0.8;
  }

  .captions-status {
    color: #10b981;
    font-weight: 600;
  }

  .captions-label {
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
  }

  .captions-container {
    max-height: 120px;
    overflow-y: auto;
    scroll-behavior: smooth;
    padding-right: 0.5rem;
  }

  /* Hide scrollbar but keep functionality */
  .captions-container::-webkit-scrollbar {
    width: 4px;
  }

  .captions-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .captions-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }

  .caption-line {
    margin-bottom: 0.5rem;
    line-height: 1.5;
    font-size: 0.95rem;
    word-wrap: break-word;
    animation: fadeIn 0.3s ease-in;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(5px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .caption-speaker {
    font-weight: 600;
    margin-right: 0.5rem;
    color: #60a5fa;
  }

  .caption-text {
    color: white;
  }
</style>
