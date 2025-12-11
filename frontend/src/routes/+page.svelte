<script lang="ts">
  import { invalidateAll } from "$app/navigation";
  import { createInterview } from "$lib/interviews";
  import MultiInput from "$lib/components/MultiInput.svelte";
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";

  export let data: PageData;

  let error: string | null = null;
  let copyError: string | null = null;
  let jobDescriptionContent: string | File | null = null;
  let resumeContent: string | File | null = null;
  let jobDescriptionMetadata: any = null;
  let resumeMetadata: any = null;
  let isLoading = false;
  let hostToken: string | null = null;
  let candidateToken: string | null = null;
  let interviewId: string | null = null;
  let hostLinkCopied = false;
  let candidateLinkCopied = false;

  // Check if we have a token validation error from the server
  $: hasTokenError = data.error && data.error !== "No token provided";
  $: showForm =
    !data.role &&
    (!data.error || data.error === "No token provided" || hasTokenError) &&
    !interviewId;
  $: showLinks = interviewId && hostToken && candidateToken;

  $: hostLink = browser && hostToken ? `${window.location.origin}/host?token=${hostToken}` : "";
  $: candidateLink =
    browser && candidateToken ? `${window.location.origin}/candidate?token=${candidateToken}` : "";

  function handleJobDescriptionChange(event: CustomEvent) {
    jobDescriptionContent = event.detail.content;
    jobDescriptionMetadata = event.detail.metadata;
  }

  function handleResumeChange(event: CustomEvent) {
    resumeContent = event.detail.content;
    resumeMetadata = event.detail.metadata;
  }

  async function handleCreateInterview() {
    if (!jobDescriptionContent || !resumeContent) {
      error = "Please provide both job description and resume";
      return;
    }

    isLoading = true;
    error = null;

    try {
      // Build request based on content types
      const request: any = {};

      // Handle job description
      if (jobDescriptionMetadata?.type === "file") {
        request.job_description_file = jobDescriptionContent as File;
        request.job_description_type = "file";
      } else if (jobDescriptionMetadata?.type === "url") {
        request.job_description_url = jobDescriptionContent as string;
        request.job_description_type = "url";
      } else {
        request.job_description = jobDescriptionContent as string;
        request.job_description_type = "text";
      }

      // Handle resume
      if (resumeMetadata?.type === "file") {
        request.resume_file = resumeContent as File;
        request.resume_type = "file";
      } else if (resumeMetadata?.type === "url") {
        request.resume_url = resumeContent as string;
        request.resume_type = "url";
      } else {
        request.resume_text = resumeContent as string;
        request.resume_type = "text";
      }

      const response = await createInterview(request);

      interviewId = response.interview_id;
      hostToken = response.host_token;
      candidateToken = response.candidate_token;
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to create interview";
    } finally {
      isLoading = false;
    }
  }

  async function copyToClipboard(text: string, type: "host" | "candidate") {
    if (!text || text.trim() === "") {
      copyError = "Link is not available yet. Please wait a moment.";
      setTimeout(() => (copyError = null), 3000);
      return;
    }

    copyError = null;

    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
          const successful = document.execCommand("copy");
          if (!successful) {
            throw new Error("Copy command failed");
          }
        } finally {
          document.body.removeChild(textArea);
        }
      }

      // Show success feedback
      if (type === "host") {
        hostLinkCopied = true;
        setTimeout(() => (hostLinkCopied = false), 2000);
      } else {
        candidateLinkCopied = true;
        setTimeout(() => (candidateLinkCopied = false), 2000);
      }
    } catch (err) {
      console.error("Failed to copy:", err);
      copyError = "Failed to copy link to clipboard. Please try selecting and copying manually.";
      setTimeout(() => (copyError = null), 5000);
    }
  }

  function handleCreateAnother() {
    interviewId = null;
    hostToken = null;
    candidateToken = null;
    jobDescriptionContent = null;
    resumeContent = null;
    jobDescriptionMetadata = null;
    resumeMetadata = null;
    error = null;
    copyError = null;
    hostLinkCopied = false;
    candidateLinkCopied = false;
  }

  function handleClearToken() {
    // Clear session storage
    sessionStorage.removeItem("token");
    // Clear cookies by setting an expired cookie
    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    // Reload the page to clear server-side state
    invalidateAll();
    window.location.href = "/";
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900">
  <div class="container mx-auto px-4 py-12">
    <!-- Hero Section -->
    <div class="text-center mb-12">
      <h1
        class="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-4"
      >
        Bionic Interviewer
      </h1>
      <p class="text-gray-400 text-lg">AI-Powered Interview Management Platform</p>
    </div>

    {#if hasTokenError}
      <div
        class="bg-red-900/30 border border-red-700/50 text-red-300 px-6 py-4 rounded-xl mb-6 max-w-3xl mx-auto backdrop-blur-sm"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="font-semibold text-red-200">Token Validation Failed</p>
            <p class="text-sm mt-1">{data.error}</p>
          </div>
          <button
            on:click={handleClearToken}
            class="ml-4 px-6 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-200 shadow-lg hover:shadow-red-500/50"
          >
            Clear Token & Start Over
          </button>
        </div>
      </div>
    {/if}

    {#if error}
      <div
        class="bg-red-900/30 border border-red-700/50 text-red-300 px-6 py-4 rounded-xl mb-6 max-w-3xl mx-auto backdrop-blur-sm"
      >
        {error}
      </div>
    {/if}

    {#if showForm}
      <div
        class="bg-slate-800/50 backdrop-blur-md rounded-2xl shadow-2xl p-8 max-w-3xl mx-auto border border-slate-700/50"
      >
        <h2 class="text-3xl font-bold text-white mb-3">Create New Interview</h2>
        <p class="text-gray-400 mb-8">
          Enter the job description and candidate resume to create a new interview session.
        </p>

        <form on:submit|preventDefault={handleCreateInterview} class="space-y-6">
          <MultiInput
            fieldName="job-description"
            label="Job Description"
            required={true}
            on:change={handleJobDescriptionChange}
          />

          <MultiInput
            fieldName="resume"
            label="Candidate Resume"
            required={true}
            on:change={handleResumeChange}
          />

          <button
            type="submit"
            disabled={isLoading}
            class="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-blue-500/50"
          >
            {isLoading ? "Creating Interview..." : "Create Interview"}
          </button>
        </form>
      </div>
    {/if}

    {#if showLinks}
      <div
        class="bg-slate-800/50 backdrop-blur-md rounded-2xl shadow-2xl p-8 max-w-3xl mx-auto border border-slate-700/50"
      >
        <div class="text-center mb-8">
          <div
            class="inline-flex items-center justify-center w-16 h-16 bg-green-500/20 rounded-full mb-4"
          >
            <svg
              class="w-8 h-8 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              ></path>
            </svg>
          </div>
          <h2 class="text-3xl font-bold text-white mb-2">Interview Created Successfully!</h2>
          <p class="text-gray-400">
            Share these links with the host and candidate. Each link provides a unique experience.
          </p>
        </div>

        {#if copyError}
          <div
            class="bg-yellow-900/30 border border-yellow-700/50 text-yellow-300 px-6 py-4 rounded-xl mb-6 backdrop-blur-sm"
          >
            {copyError}
          </div>
        {/if}

        <div class="space-y-6">
          <!-- Host Link -->
          <div class="bg-slate-900/50 rounded-xl p-6 border border-slate-700/50">
            <div class="flex items-center justify-between mb-3">
              <label class="block text-sm font-semibold text-gray-300"> Host Link </label>
              <span class="text-xs text-gray-500 bg-slate-800/50 px-2 py-1 rounded"
                >For Interviewer</span
              >
            </div>
            <div class="flex items-center gap-3">
              <input
                type="text"
                readonly
                value={hostLink}
                class="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg text-gray-200 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                on:click={() => copyToClipboard(hostLink, "host")}
                class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all duration-200 shadow-lg hover:shadow-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                disabled={hostLinkCopied || !hostLink}
              >
                {#if hostLinkCopied}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    ></path>
                  </svg>
                  Copied!
                {:else}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  Copy
                {/if}
              </button>
            </div>
          </div>

          <!-- Candidate Link -->
          <div class="bg-slate-900/50 rounded-xl p-6 border border-slate-700/50">
            <div class="flex items-center justify-between mb-3">
              <label class="block text-sm font-semibold text-gray-300"> Candidate Link </label>
              <span class="text-xs text-gray-500 bg-slate-800/50 px-2 py-1 rounded"
                >For Interviewee</span
              >
            </div>
            <div class="flex items-center gap-3">
              <input
                type="text"
                readonly
                value={candidateLink}
                class="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg text-gray-200 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                on:click={() => copyToClipboard(candidateLink, "candidate")}
                class="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all duration-200 shadow-lg hover:shadow-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                disabled={candidateLinkCopied || !candidateLink}
              >
                {#if candidateLinkCopied}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    ></path>
                  </svg>
                  Copied!
                {:else}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  Copy
                {/if}
              </button>
            </div>
          </div>
        </div>

        <div class="mt-8 pt-6 border-t border-slate-700/50">
          <button
            on:click={handleCreateAnother}
            class="w-full px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all duration-200"
          >
            Create Another Interview
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
