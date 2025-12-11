<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Vapi, { type Vapi as VapiType } from "@vapi-ai/web";
  import { getVapiPublicKey } from "$lib/vapi";

  export let publicKey: string;
  export let assistantId: string;
  export let interviewId: string;
  export let token: string = ""; // Authentication token for backend API
  export let textToRead: string;
  export let startLabel: string = "Briefing";

  let vapi: VapiType | null = null;
  let isConnected = false;
  let isListening = false;
  let isSpeaking = false;
  let error: string | null = null;
  let isLoading = true;

  // Get API base URL for proxy
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  onMount(async () => {
    try {
      isLoading = true;
      error = null;

      // Validate token is available
      if (!token) {
        error = "Authentication token is required";
        isLoading = false;
        return;
      }

      // If public key is not provided, fetch it from backend
      let apiKey = publicKey;
      if (!apiKey && token) {
        try {
          apiKey = await getVapiPublicKey(token);
        } catch (e) {
          console.error("Failed to fetch public key:", e);
          error = "Failed to fetch Vapi public key from server";
          isLoading = false;
          return;
        }
      }

      if (!apiKey) {
        error = "Vapi public key is required";
        isLoading = false;
        return;
      }

      // Build proxy URL with token in the path
      // This avoids issues with the SDK appending paths to URLs with query parameters
      // Format: /api/vapi/proxy/{token}/...
      const proxyUrl = `${API_BASE_URL}/api/vapi/proxy/${encodeURIComponent(token)}`;

      // Initialize Vapi SDK with public key and proxy URL
      vapi = new Vapi(apiKey, proxyUrl);

      // Set up event listeners
      vapi.on("call-start", () => {
        isConnected = true;
        isListening = true;
        error = null;
        console.log("Vapi call started");
      });

      vapi.on("call-end", () => {
        isConnected = false;
        isListening = false;
        isSpeaking = false;
        console.log("Vapi call ended");
      });

      vapi.on("user-speech-start", () => {
        isListening = true;
        console.log("User is speaking");
      });

      vapi.on("user-speech-end", () => {
        isListening = false;
        console.log("User finished speaking");
      });

      vapi.on("assistant-speech-start", () => {
        isSpeaking = true;
        console.log("Assistant is speaking");
      });

      vapi.on("assistant-speech-end", () => {
        isSpeaking = false;
        console.log("Assistant finished speaking");
      });

      vapi.on("error", (errorEvent: any) => {
        const errorMsg =
          errorEvent?.error?.message || errorEvent?.message || "An error occurred with Vapi";

        // Provide helpful error messages for common issues
        if (errorMsg.includes("WebRTC") || errorMsg.includes("getUserMedia")) {
          error =
            "WebRTC is required but not available. Please:\n1. Use HTTPS or localhost (not 0.0.0.0)\n2. Allow microphone permissions\n3. Disable WebRTC-blocking extensions\n4. Use a modern browser (Chrome, Firefox, Safari)";
        } else {
          error = errorMsg;
        }

        console.error("Vapi error:", errorEvent);
      });

      isLoading = false;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to initialize Vapi";
      isLoading = false;
      console.error("Vapi initialization error:", e);
    }
  });

  onDestroy(() => {
    // Cleanup Vapi connection
    if (vapi) {
      try {
        // Stop any active call
        if (isConnected) {
          vapi.stop();
        }
        // Remove all event listeners
        vapi.removeAllListeners();
      } catch (e) {
        console.error("Error cleaning up Vapi:", e);
      }
      vapi = null;
    }
  });

  async function requestMicrophonePermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop the stream immediately - we just needed to request permission
      stream.getTracks().forEach((track) => track.stop());
      return true;
    } catch (e) {
      console.error("Microphone permission denied:", e);
      error =
        "Microphone permission is required for voice calls. Please allow microphone access and try again.";
      return false;
    }
  }

  async function checkWebRTCSupport() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      error =
        "WebRTC is not supported in this browser. Please use a modern browser like Chrome, Firefox, or Safari.";
      return false;
    }
    return true;
  }

  async function startReading() {
    if (!vapi) {
      error = "Vapi not initialized";
      return;
    }

    if (isConnected) {
      // Already connected, do nothing
      return;
    }

    try {
      error = null;

      // Check WebRTC support first
      if (!(await checkWebRTCSupport())) {
        return;
      }

      // Request microphone permission
      if (!(await requestMicrophonePermission())) {
        return;
      }

      // Start Vapi call with the briefing as the first message override
      await vapi.start({
        firstMessage: textToRead,
      });
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Failed to start briefing";
      error = errorMessage;
      isConnected = false;
      isListening = false;
      console.error("Error starting Vapi call:", e);

      // Provide helpful error messages
      if (errorMessage.includes("WebRTC") || errorMessage.includes("getUserMedia")) {
        error =
          "WebRTC or microphone access is required. Please check your browser permissions and ensure you're using HTTPS or localhost.";
      }
    }
  }

  function stopReading() {
    if (!vapi || !isConnected) return;

    try {
      vapi.stop();
      isConnected = false;
      isListening = false;
      isSpeaking = false;
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to stop briefing";
      console.error("Error stopping Vapi call:", e);
    }
  }
</script>

<div class="vapi-orb-container">
  {#if error}
    <div class="px-4 py-3 mb-4 text-red-700 bg-red-50 rounded border border-red-200">
      {error}
    </div>
  {/if}

  <div class="flex flex-col gap-4 items-center">
    {#if isLoading}
      <div class="flex gap-2 items-center text-gray-500">
        <div
          class="w-4 h-4 rounded-full border-2 border-gray-300 animate-spin border-t-blue-500"
        ></div>
        <span class="text-sm">Initializing...</span>
      </div>
    {:else if vapi}
      <button
        on:click={isConnected ? stopReading : startReading}
        class="px-6 py-3 rounded-full text-white font-semibold transition-colors {isConnected
          ? 'bg-red-500 hover:bg-red-600'
          : 'bg-blue-500 hover:bg-blue-600'}"
        disabled={!vapi}
      >
        {isConnected ? `Stop ${startLabel}` : `Start ${startLabel}`}
      </button>

      {#if isConnected}
        <div class="flex flex-col gap-2 items-center">
          {#if isListening}
            <div class="flex gap-2 items-center text-green-600">
              <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span class="text-sm">Listening...</span>
            </div>
          {/if}
          {#if isSpeaking}
            <div class="flex gap-2 items-center text-blue-600">
              <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <span class="text-sm">Assistant Speaking...</span>
            </div>
          {/if}
          {#if !isListening && !isSpeaking && isConnected}
            <div class="flex gap-2 items-center text-gray-400">
              <div class="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span class="text-sm">Connected</span>
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .vapi-orb-container {
    @apply p-6 rounded-lg shadow-lg;
  }
</style>
