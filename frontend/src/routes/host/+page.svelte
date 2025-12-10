<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";
  import VapiOrb from "$lib/components/VapiOrb.svelte";
  import DailyCall from "$lib/components/DailyCall.svelte";
  import TranscriptDownload from "$lib/components/TranscriptDownload.svelte";
  import { generateBriefing } from "$lib/briefing";
  import { createRoom, getRoomUrl } from "$lib/daily";

  export let data: PageData;

  let briefing: string | null = null;
  let isLoading = false;
  let error: string | null = null;
  let token: string | null = null;
  let roomUrl: string | null = null;
  let roomToken: string | null = null;
  let isLoadingRoom = false;

  // Get job description and resume from server data
  $: jobDescription = data.interview?.job_description || "";
  $: resumeText = data.interview?.resume_text || "";

  onMount(() => {
    // Get token from URL or session storage
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get("token") || sessionStorage.getItem("token");
  });

  async function handleGenerateBriefing() {
    if (!token) {
      error = "No token available";
      return;
    }

    if (!jobDescription.trim() || !resumeText.trim()) {
      error = "Job description and resume are required";
      return;
    }

    isLoading = true;
    error = null;

    try {
      const response = await generateBriefing(
        {
          job_description: jobDescription,
          resume_text: resumeText,
        },
        token
      );

      briefing = response.briefing;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to generate briefing";
    } finally {
      isLoading = false;
    }
  }

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
        Host Dashboard
      </h1>
      <p class="text-gray-400">Manage your interview session</p>
    </div>

    {#if data.error}
      <div
        class="px-6 py-4 mb-6 text-red-300 rounded-xl border backdrop-blur-sm bg-red-900/30 border-red-700/50"
      >
        {data.error}
      </div>
    {:else}
      <div class="space-y-6">
        <!-- Briefing Generation -->
        <div
          class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
        >
          <h2 class="mb-4 text-xl font-bold text-white">Generate Briefing</h2>

          {#if error}
            <div
              class="px-6 py-4 mb-4 text-red-300 rounded-xl border backdrop-blur-sm bg-red-900/30 border-red-700/50"
            >
              {error}
            </div>
          {/if}

          {#if !data.interview}
            <div
              class="px-6 py-4 mb-4 text-yellow-300 rounded-xl border backdrop-blur-sm bg-yellow-900/30 border-yellow-700/50"
            >
              Interview details are not available. Please ensure the interview was created
              successfully.
            </div>
          {:else}
            <button
              on:click={handleGenerateBriefing}
              disabled={isLoading || !jobDescription.trim() || !resumeText.trim()}
              class="px-6 py-3 font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg transition-all duration-200 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-blue-500/50"
            >
              {isLoading ? "Generating..." : "Generate Briefing"}
            </button>
          {/if}

          {#if briefing}
            <div class="p-5 mt-6 rounded-lg border bg-slate-900/50 border-slate-600">
              <h3 class="mb-3 text-lg font-semibold text-white">Generated Briefing</h3>
              <div
                class="max-w-none leading-relaxed text-gray-300 whitespace-pre-wrap prose prose-invert"
              >
                {briefing}
              </div>
            </div>
          {/if}
        </div>

        <!-- Vapi Orb Component -->
        {#if briefing}
          <div
            class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
          >
            <h2 class="mb-4 text-xl font-bold text-white">Voice Briefing</h2>
            <VapiOrb
              publicKey={import.meta.env.VITE_VAPI_PUBLIC_KEY || ""}
              assistantId={import.meta.env.VITE_VAPI_ASSISTANT_ID || ""}
              interviewId={data.interviewId || ""}
              token={token || ""}
              briefing={briefing || ""}
            />
          </div>
        {/if}

        <!-- Daily.co Video Call -->
        <div
          class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
        >
          <h2 class="mb-4 text-xl font-bold text-white">Video Call</h2>

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
              userRole="host"
            />
          {/if}
        </div>

        <!-- Transcript Download -->
        {#if token && data.interviewId}
          <div
            class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
          >
            <TranscriptDownload interviewId={data.interviewId} {token} />
          </div>
        {/if}

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

        <!-- Interview Details Display -->
        {#if data.interview}
          <div
            class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
          >
            <h2 class="mb-6 text-xl font-bold text-white">Interview Details</h2>

            <div class="space-y-6">
              <div>
                <h3 class="block mb-3 text-sm font-semibold text-gray-300">Job Description</h3>
                <div class="p-4 rounded-lg border bg-slate-900/50 border-slate-600">
                  <p class="leading-relaxed text-gray-300 whitespace-pre-wrap">
                    {data.interview.job_description}
                  </p>
                </div>
              </div>

              <div>
                <h3 class="block mb-3 text-sm font-semibold text-gray-300">Candidate Resume</h3>
                <div class="p-4 rounded-lg border bg-slate-900/50 border-slate-600">
                  <p class="leading-relaxed text-gray-300 whitespace-pre-wrap">
                    {data.interview.resume_text}
                  </p>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
