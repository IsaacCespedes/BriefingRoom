<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";
  import VapiOrb from "$lib/components/VapiOrb.svelte";
  import DailyCall from "$lib/components/DailyCall.svelte";
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

<div class="min-h-screen bg-gray-50">
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-4">Host Dashboard</h1>

    {#if data.error}
      <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
        {data.error}
      </div>
    {:else}
      <div class="space-y-6">
        <!-- Interview Info -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Interview Information</h2>
          <p class="text-gray-700">Interview ID: {data.interviewId}</p>
        </div>

        <!-- Interview Details Display -->
        {#if data.interview}
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Interview Details</h2>

            <div class="space-y-6">
              <div>
                <h3 class="block text-sm font-medium text-gray-700 mb-2">Job Description</h3>
                <div class="p-4 bg-gray-50 rounded-md border border-gray-200">
                  <p class="text-gray-700 whitespace-pre-wrap">{data.interview.job_description}</p>
                </div>
              </div>

              <div>
                <h3 class="block text-sm font-medium text-gray-700 mb-2">Candidate Resume</h3>
                <div class="p-4 bg-gray-50 rounded-md border border-gray-200">
                  <p class="text-gray-700 whitespace-pre-wrap">{data.interview.resume_text}</p>
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Briefing Generation -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Generate Briefing</h2>

          {#if error}
            <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          {/if}

          {#if !data.interview}
            <div
              class="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded mb-4"
            >
              Interview details are not available. Please ensure the interview was created
              successfully.
            </div>
          {:else}
            <button
              on:click={handleGenerateBriefing}
              disabled={isLoading || !jobDescription.trim() || !resumeText.trim()}
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Generating..." : "Generate Briefing"}
            </button>
          {/if}

          {#if briefing}
            <div class="mt-6 p-4 bg-gray-50 rounded-md">
              <h3 class="text-lg font-semibold text-gray-900 mb-2">Generated Briefing</h3>
              <div class="prose max-w-none text-gray-700 whitespace-pre-wrap">{briefing}</div>
            </div>
          {/if}
        </div>

        <!-- Vapi Orb Component -->
        {#if briefing}
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Voice Briefing</h2>
            <VapiOrb
              apiKey={import.meta.env.VITE_VAPI_API_KEY || ""}
              assistantId={import.meta.env.VITE_VAPI_ASSISTANT_ID || ""}
              interviewId={data.interviewId || ""}
            />
          </div>
        {/if}

        <!-- Daily.co Video Call -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Video Call</h2>

          {#if !roomUrl}
            <button
              on:click={handleCreateRoom}
              disabled={isLoadingRoom}
              class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoadingRoom ? "Creating Room..." : "Start Video Call"}
            </button>
          {:else}
            <DailyCall {roomUrl} token={roomToken} />
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
