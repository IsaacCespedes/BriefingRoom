<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import DailyIframe from "@daily-co/daily-js";

  export let roomUrl: string;
  export let token: string | null = null;

  let isJoined = false;
  let error: string | null = null;
  let callFrame: any = null;

  $: if (!roomUrl) {
    error = "Room URL is required";
  } else {
    error = null;
  }

  onMount(() => {
    // No-op
  });

  onDestroy(() => {
    if (callFrame) {
      callFrame.destroy();
      callFrame = null;
    }
  });

  async function joinCall() {
    if (!roomUrl) {
      error = "Room URL is required";
      return;
    }

    isJoined = true;

    // Use a timeout to allow Svelte to render the component
    setTimeout(async () => {
      if (!callFrame) {
        try {
          const frame = document.getElementById("daily-call-frame");
          if (!frame) {
            throw new Error("Daily call frame element not found.");
          }

          callFrame = DailyIframe.createFrame(frame, {
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
              error = null;
            })
            .on("left-meeting", () => {
              isJoined = false;
            })
            .on("error", (e: any) => {
              error = e?.errorMsg || "An error occurred during the call";
              isJoined = false;
            });
        } catch (e) {
          error = e instanceof Error ? e.message : "Failed to initialize Daily.co";
          isJoined = false;
          return;
        }
      }

      try {
        await callFrame.join({
          url: roomUrl,
          token: token || undefined,
        });
      } catch (e) {
        error = e instanceof Error ? e.message : "Failed to join call";
      }
    }, 0);
  }

  function leaveCall() {
    if (callFrame) {
      callFrame.leave();
    }
  }
</script>

<div class="daily-call-container">
  {#if error}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  <div class="flex flex-col items-center gap-4">
    {#if !isJoined}
      <button
        on:click={joinCall}
        class="px-6 py-3 rounded-full text-white font-semibold bg-green-500 hover:bg-green-600 transition-colors"
        disabled={!!error}
      >
        Join Call
      </button>
    {:else}
      <button
        on:click={leaveCall}
        class="px-6 py-3 rounded-full text-white font-semibold bg-red-500 hover:bg-red-600 transition-colors"
      >
        Leave Call
      </button>
    {/if}

    {#if isJoined}
      <div class="w-full h-96 bg-gray-900 rounded-lg overflow-hidden" id="daily-call-frame">
        <!-- Daily.co iframe will be inserted here -->
      </div>
    {/if}
  </div>
</div>

<style>
  .daily-call-container {
    @apply p-6 bg-white rounded-lg shadow-lg;
  }
</style>
