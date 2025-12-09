<script lang="ts">
  import { goto } from "$app/navigation";
  import { invalidateAll } from "$app/navigation";
  import { createInterview } from "$lib/interviews";
  import type { PageData } from "./$types";

  export let data: PageData;

  let error: string | null = null;
  let jobDescription = "";
  let resumeText = "";
  let isLoading = false;
  let candidateToken: string | null = null;
  let interviewId: string | null = null;

  // Check if we have a token validation error from the server
  $: hasTokenError = data.error && data.error !== "No token provided";
  $: showForm = !data.role && (!data.error || data.error === "No token provided" || hasTokenError);

  async function handleCreateInterview() {
    if (!jobDescription.trim() || !resumeText.trim()) {
      error = "Please provide both job description and resume text";
      return;
    }

    isLoading = true;
    error = null;

    try {
      const response = await createInterview({
        job_description: jobDescription,
        resume_text: resumeText,
      });

      interviewId = response.interview_id;
      candidateToken = response.candidate_token;

      // Redirect to host page with token - server will handle validation and cookie storage
      goto(`/host?token=${response.host_token}`);
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to create interview";
    } finally {
      isLoading = false;
    }
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
      <h1 class="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-4">
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
      <div class="bg-slate-800/50 backdrop-blur-md rounded-2xl shadow-2xl p-8 max-w-3xl mx-auto border border-slate-700/50">
        <h2 class="text-3xl font-bold text-white mb-3">Create New Interview</h2>
        <p class="text-gray-400 mb-8">
          Enter the job description and candidate resume to create a new interview session.
        </p>

        <form on:submit|preventDefault={handleCreateInterview} class="space-y-6">
          <div>
            <label for="job-description" class="block text-sm font-semibold text-gray-300 mb-3">
              Job Description
            </label>
            <textarea
              id="job-description"
              bind:value={jobDescription}
              rows="6"
              class="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-200 placeholder-gray-500 transition-all duration-200"
              placeholder="Enter the job description..."
              required
            ></textarea>
          </div>

          <div>
            <label for="resume-text" class="block text-sm font-semibold text-gray-300 mb-3">
              Candidate Resume
            </label>
            <textarea
              id="resume-text"
              bind:value={resumeText}
              rows="12"
              class="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-200 placeholder-gray-500 transition-all duration-200"
              placeholder="Paste the candidate's resume text..."
              required
            ></textarea>
          </div>

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
  </div>
</div>
