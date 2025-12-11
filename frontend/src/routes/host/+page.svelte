<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";
  import VapiOrb from "$lib/components/VapiOrb.svelte";
  import DailyCall from "$lib/components/DailyCall.svelte";
  import TranscriptDownload from "$lib/components/TranscriptDownload.svelte";
  import { generateBriefing } from "$lib/briefing";
  import { createRoom, getRoomUrl } from "$lib/daily";
  import { generateReview, getReview } from "$lib/review";
  import { getTranscript } from "$lib/transcripts";
  import { getTranscript as getLocalTranscript, transcriptToText } from "$lib/transcriptStorage";

  export let data: PageData;

  let briefing: string | null = null;
  let isLoading = false;
  let error: string | null = null;
  let token: string | null = null;
  let roomUrl: string | null = null;
  let roomToken: string | null = null;
  let isLoadingRoom = false;
  let review: string | null = null;
  let isLoadingReview = false;
  let reviewError: string | null = null;
  let transcriptStatus: string | null = null;

  // Get job description and resume from server data
  // Handle text, file paths, or URLs
  $: jobDescription = data.interview?.job_description || data.interview?.job_description_path || "";
  $: resumeText = data.interview?.resume_text || data.interview?.resume_path || "";

  // Get source types for briefing generation
  $: jobDescriptionSource = data.interview?.job_description_source || "text";
  $: resumeSource = data.interview?.resume_source || "text";

  onMount(async () => {
    // Get token from URL or session storage
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get("token") || sessionStorage.getItem("token");
  });

  async function handleGenerateReview() {
    if (!token || !data.interviewId) {
      reviewError = "Token or interview ID not available";
      return;
    }

    isLoadingReview = true;
    reviewError = null;

    try {
      // Use local storage transcript ONLY
      const localTranscript = getLocalTranscript(data.interviewId);
      let transcriptText: string | undefined = undefined;

      if (localTranscript && localTranscript.segments.length > 0) {
        // Use local storage transcript (same one that would be downloaded)
        transcriptText = transcriptToText(localTranscript);
      } else {
        reviewError =
          "No local transcript available. Please complete the interview to generate a review.";
        return; // Exit if no local transcript
      }

      // Generate review with transcript text (sends as string to backend)
      const response = await generateReview(data.interviewId, token, transcriptText);
      review = response.review;
    } catch (e) {
      reviewError = e instanceof Error ? e.message : "Failed to generate review";
    } finally {
      isLoadingReview = false;
    }
  }

  async function handleGenerateBriefing() {
    if (!token) {
      error = "No token available";
    }

    // Validate that we have at least one input method for each field
    const hasJobDescription =
      (data.interview?.job_description && data.interview.job_description.trim()) ||
      data.interview?.job_description_path;
    const hasResume =
      (data.interview?.resume_text && data.interview.resume_text.trim()) ||
      data.interview?.resume_path;

    if (!hasJobDescription || !hasResume) {
      error = "Job description and resume are required";
      return;
    }

    isLoading = true;
    error = null;

    try {
      // Build request with proper source types and paths
      const request: any = {
        job_description: data.interview?.job_description || null,
        resume_text: data.interview?.resume_text || null,
        job_description_path: data.interview?.job_description_path || null,
        resume_path: data.interview?.resume_path || null,
        job_description_source: jobDescriptionSource,
        resume_source: resumeSource,
      };

      const response = await generateBriefing(request, token);

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
              textToRead={briefing || ""}
              startLabel="Briefing"
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

        <!-- Interview Review -->
        {#if token && data.interviewId}
          <div
            class="p-6 rounded-xl border shadow-xl backdrop-blur-md bg-slate-800/50 border-slate-700/50"
          >
            <h2 class="mb-4 text-xl font-bold text-white">Interview Review</h2>

            {#if reviewError}
              <div
                class="px-6 py-4 mb-4 text-red-300 rounded-xl border backdrop-blur-sm bg-red-900/30 border-red-700/50"
              >
                {reviewError}
              </div>
            {/if}

            {#if !review}
              <button
                on:click={handleGenerateReview}
                disabled={isLoadingReview}
                class="px-6 py-3 font-semibold text-white bg-gradient-to-r from-indigo-600 to-pink-600 rounded-lg shadow-lg transition-all duration-200 hover:from-indigo-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-indigo-500/50"
              >
                {isLoadingReview ? "Generating Review..." : "Generate Interview Review"}
              </button>
            {:else}
              <div class="p-5 mt-6 rounded-lg border bg-slate-900/50 border-slate-600">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-lg font-semibold text-white">Interview Review</h3>
                  <button
                    on:click={handleGenerateReview}
                    disabled={isLoadingReview}
                    class="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg transition-all duration-200 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoadingReview ? "Regenerating..." : "Regenerate Review"}
                  </button>
                </div>
                <div
                  class="max-w-none leading-relaxed text-gray-300 whitespace-pre-wrap prose prose-invert"
                >
                  {review}
                </div>

                <!-- Add VapiOrb for review here -->
                <div class="mt-6 border-t pt-4 border-slate-700">
                  <h4 class="mb-2 text-md font-semibold text-white">Voice Review</h4>
                  <VapiOrb
                    publicKey={import.meta.env.VITE_VAPI_PUBLIC_KEY || ""}
                    assistantId={import.meta.env.VITE_VAPI_ASSISTANT_ID || ""}
                    interviewId={data.interviewId || ""}
                    token={token || ""}
                    textToRead={review || ""}
                    startLabel="Review"
                  />
                </div>
              </div>
            {/if}
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
                  {#if data.interview.job_description}
                    <p class="leading-relaxed text-gray-300 whitespace-pre-wrap">
                      {data.interview.job_description}
                    </p>
                  {:else if data.interview.job_description_path}
                    <div class="space-y-2">
                      <p class="text-sm text-gray-400">
                        Source: {data.interview.job_description_source || "file"}
                      </p>
                      {#if data.interview.job_description_source === "url"}
                        <a
                          href={data.interview.job_description_path}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 underline transition-colors"
                        >
                          <svg
                            class="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                            ></path>
                          </svg>
                          Link
                        </a>
                      {:else}
                        <div class="space-y-2">
                          {#if data.interview.job_description_metadata?.filename}
                            <p class="text-xs text-gray-500">
                              File: {data.interview.job_description_metadata.filename}
                            </p>
                          {/if}
                          <a
                            href={data.interview.job_description_path}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 underline transition-colors"
                          >
                            <svg
                              class="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                              xmlns="http://www.w3.org/2000/svg"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                              ></path>
                            </svg>
                            Link
                          </a>
                        </div>
                      {/if}
                    </div>
                  {:else}
                    <p class="text-gray-500 italic">No job description provided</p>
                  {/if}
                </div>
              </div>

              <div>
                <h3 class="block mb-3 text-sm font-semibold text-gray-300">Candidate Resume</h3>
                <div class="p-4 rounded-lg border bg-slate-900/50 border-slate-600">
                  {#if data.interview.resume_text}
                    <p class="leading-relaxed text-gray-300 whitespace-pre-wrap">
                      {data.interview.resume_text}
                    </p>
                  {:else if data.interview.resume_path}
                    <div class="space-y-2">
                      <p class="text-sm text-gray-400">
                        Source: {data.interview.resume_source || "file"}
                      </p>
                      {#if data.interview.resume_source === "url"}
                        <a
                          href={data.interview.resume_path}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 underline transition-colors"
                        >
                          <svg
                            class="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                            ></path>
                          </svg>
                          Link
                        </a>
                      {:else}
                        <div class="space-y-2">
                          {#if data.interview.resume_metadata?.filename}
                            <p class="text-xs text-gray-500">
                              File: {data.interview.resume_metadata.filename}
                            </p>
                          {/if}
                          <a
                            href={data.interview.resume_path}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 underline transition-colors"
                          >
                            <svg
                              class="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                              xmlns="http://www.w3.org/2000/svg"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                              ></path>
                            </svg>
                            Link
                          </a>
                        </div>
                      {/if}
                    </div>
                  {:else}
                    <p class="text-gray-500 italic">No resume provided</p>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
