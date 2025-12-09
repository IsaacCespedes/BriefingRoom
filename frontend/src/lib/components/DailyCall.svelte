<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import DailyIframe from "@daily-co/daily-js";

  export let roomUrl: string;
  export let token: string | null = null;

  let isJoined = false;
  let isJoining = false;
  let error: string | null = null;
  let callFrame: any = null;
  let frameElement: HTMLDivElement | null = null;
  let showFrame = false;

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
            .on("joined-meeting", () => {
              isJoined = true;
              isJoining = false;
              error = null;
            })
            .on("left-meeting", () => {
              isJoined = false;
              isJoining = false;
            })
            .on("error", (e: any) => {
              error = e?.errorMsg || e?.error || "An error occurred during the call";
              isJoined = false;
              isJoining = false;
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

  function leaveCall() {
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
      <button
        on:click={leaveCall}
        class="px-6 py-3 rounded-full text-white font-semibold bg-red-500 hover:bg-red-600 transition-colors"
      >
        Leave Call
      </button>
    {/if}

    <!-- Always render the frame element - Daily.co needs it in the DOM -->
    <div
      bind:this={frameElement}
      class="w-full h-96 bg-gray-900 rounded-lg overflow-hidden {showFrame || isJoined
        ? ''
        : 'hidden'}"
      id="daily-call-frame"
    >
      <!-- Daily.co iframe will be inserted here -->
    </div>
  </div>
</div>

<style>
  .daily-call-container {
    @apply p-6 bg-white rounded-lg shadow-lg;
  }
</style>
