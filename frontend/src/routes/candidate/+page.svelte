<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";
  import DailyCall from "$lib/components/DailyCall.svelte";
  import { createRoom, getRoomUrl } from "$lib/daily";

  export let data: PageData;

  let error: string | null = null;
  let token: string | null = null;
  let roomUrl: string | null = null;
  let roomToken: string | null = null;
  let isLoadingRoom = false;

  onMount(() => {
    // Get token from URL or session storage
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get("token") || sessionStorage.getItem("token");
  });

  async function handleCreateRoom() {
    if (!token || !data.interviewId) {
      error = "Token or interview ID not available";
      return;
    }

    isLoadingRoom = true;
    error = null;

    try {
      // Try to get existing room first
      try {
        const existingRoom = await getRoomUrl(data.interviewId, token);
        roomUrl = existingRoom.room_url;
        roomToken = existingRoom.room_token || null;
      } catch {
        // If room doesn't exist, create a new one
        const newRoom = await createRoom(
          {
            interview_id: data.interviewId,
          },
          token
        );
        roomUrl = newRoom.room_url;
        roomToken = newRoom.room_token || null;
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to create/get room";
    } finally {
      isLoadingRoom = false;
    }
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-900 to-gray-900 via-slate-800">
  <div class="container px-4 py-8 mx-auto">
    <div class="mb-8">
      <h1
        class="mb-2 text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500"
      >
        Candidate View
      </h1>
      <p class="text-gray-400">Your interview session</p>
    </div>

    {#if data.error}
      <div
        class="px-6 py-4 mb-6 text-red-300 rounded-xl border backdrop-blur-sm bg-red-900/30 border-red-700/50"
      >
        {data.error}
      </div>
    {:else}
      <div class="space-y-6">
        <!-- Interview Info -->
        <div
          class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
        >
          <h2 class="mb-3 text-xl font-bold text-white">Interview Information</h2>
          <p class="text-gray-300">
            <span class="text-gray-500">Interview ID:</span>
            <span class="font-mono text-blue-400">{data.interviewId}</span>
          </p>
        </div>

        <!-- Daily.co Video Call -->
        <div
          class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
        >
          <h2 class="mb-4 text-xl font-bold text-white">Video Call</h2>

          {#if error}
            <div
              class="px-6 py-4 mb-4 text-red-300 rounded-xl border backdrop-blur-sm bg-red-900/30 border-red-700/50"
            >
              {error}
            </div>
          {/if}

          {#if !roomUrl}
            <button
              on:click={handleCreateRoom}
              disabled={isLoadingRoom}
              class="px-6 py-3 font-semibold text-white bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg shadow-lg transition-all duration-200 hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-green-500/50"
            >
              {isLoadingRoom ? "Creating Room..." : "Start Video Call"}
            </button>
          {:else}
            <DailyCall
              {roomUrl}
              token={roomToken}
              authToken={token}
              interviewId={data.interviewId}
            />
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
