<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import type { Vapi } from "@vapi-ai/web";

  export let apiKey: string;
  export let assistantId: string;
  export let interviewId: string;

  let vapi: Vapi | null = null;
  let isConnected = false;
  let isListening = false;
  let error: string | null = null;

  onMount(() => {
    // Initialize Vapi SDK
    // Note: This is a placeholder - actual Vapi SDK initialization will depend on the SDK API
    try {
      // TODO: Initialize Vapi with apiKey and assistantId
      // vapi = new Vapi({ apiKey, assistantId });
      console.log("Vapi initialization placeholder", { apiKey, assistantId, interviewId });
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to initialize Vapi";
    }
  });

  onDestroy(() => {
    // Cleanup Vapi connection
    if (vapi) {
      // TODO: Disconnect Vapi
      vapi = null;
    }
  });

  async function startBriefing() {
    if (!vapi) {
      error = "Vapi not initialized";
      return;
    }

    try {
      // TODO: Start Vapi call with briefing context
      // await vapi.start({ assistantId, context: { interviewId } });
      isConnected = true;
      isListening = true;
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to start briefing";
      isConnected = false;
      isListening = false;
    }
  }

  function stopBriefing() {
    if (!vapi) return;

    try {
      // TODO: Stop Vapi call
      // await vapi.stop();
      isConnected = false;
      isListening = false;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to stop briefing";
    }
  }
</script>

<div class="vapi-orb-container">
  {#if error}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  <div class="flex flex-col items-center gap-4">
    <button
      on:click={isConnected ? stopBriefing : startBriefing}
      class="px-6 py-3 rounded-full text-white font-semibold transition-colors {isConnected
        ? 'bg-red-500 hover:bg-red-600'
        : 'bg-blue-500 hover:bg-blue-600'}"
      disabled={!vapi && !error}
    >
      {isConnected ? "Stop Briefing" : "Start Briefing"}
    </button>

    {#if isListening}
      <div class="flex items-center gap-2 text-green-600">
        <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
        <span class="text-sm">Listening...</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .vapi-orb-container {
    @apply p-6 bg-white rounded-lg shadow-lg;
  }
</style>
