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

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900">
  <div class="container mx-auto px-4 py-8">
    <div class="mb-8">
      <h1
        class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-2"
      >
        Host Dashboard
      </h1>
      <p class="text-gray-400">Manage your interview session</p>
    </div>

    {#if data.error}
      <div
        class="bg-red-900/30 border border-red-700/50 text-red-300 px-6 py-4 rounded-xl mb-6 backdrop-blur-sm"
      >
        {data.error}
      </div>
    {:else}
      <div class="space-y-6">
        <!-- Interview Info -->
        <div
          class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
        >
          <h2 class="text-xl font-bold text-white mb-3">Interview Information</h2>
          <p class="text-gray-300">
            <span class="text-gray-500">Interview ID:</span>
            <span class="font-mono text-blue-400">{data.interviewId}</span>
          </p>
        </div>

        <!-- Interview Details Display -->
        {#if data.interview}
          <div
            class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
          >
            <h2 class="text-xl font-bold text-white mb-6">Interview Details</h2>

            <div class="space-y-6">
              <div>
                <h3 class="block text-sm font-semibold text-gray-300 mb-3">Job Description</h3>
                <div class="p-4 bg-slate-900/50 rounded-lg border border-slate-600">
                  <p class="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {data.interview.job_description}
                  </p>
                </div>
              </div>

              <div>
                <h3 class="block text-sm font-semibold text-gray-300 mb-3">Candidate Resume</h3>
                <div class="p-4 bg-slate-900/50 rounded-lg border border-slate-600">
                  <p class="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {data.interview.resume_text}
                  </p>
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Briefing Generation -->
        <div
          class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
        >
          <h2 class="text-xl font-bold text-white mb-4">Generate Briefing</h2>

          {#if error}
            <div
              class="bg-red-900/30 border border-red-700/50 text-red-300 px-6 py-4 rounded-xl mb-4 backdrop-blur-sm"
            >
              {error}
            </div>
          {/if}

          {#if !data.interview}
            <div
              class="bg-yellow-900/30 border border-yellow-700/50 text-yellow-300 px-6 py-4 rounded-xl mb-4 backdrop-blur-sm"
            >
              Interview details are not available. Please ensure the interview was created
              successfully.
            </div>
          {:else}
            <button
              on:click={handleGenerateBriefing}
              disabled={isLoading || !jobDescription.trim() || !resumeText.trim()}
              class="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-blue-500/50"
            >
              {isLoading ? "Generating..." : "Generate Briefing"}
            </button>
          {/if}

          {#if briefing}
            <div class="mt-6 p-5 bg-slate-900/50 rounded-lg border border-slate-600">
              <h3 class="text-lg font-semibold text-white mb-3">Generated Briefing</h3>
              <div
                class="prose prose-invert max-w-none text-gray-300 whitespace-pre-wrap leading-relaxed"
              >
                {briefing}
              </div>
            </div>
          {/if}
        </div>

        <!-- Vapi Orb Component -->
        {#if briefing}
          <div
            class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
          >
            <h2 class="text-xl font-bold text-white mb-4">Voice Briefing</h2>
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
          class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
        >
          <h2 class="text-xl font-bold text-white mb-4">Video Call</h2>

          {#if !roomUrl}
            <button
              on:click={handleCreateRoom}
              disabled={isLoadingRoom}
              class="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-green-500/50"
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
            class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-6 border border-slate-700/50"
          >
            <TranscriptDownload interviewId={data.interviewId} {token} />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
