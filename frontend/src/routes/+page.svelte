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

<div class="min-h-screen bg-gray-50">
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-6">Bionic Interviewer</h1>

    {#if hasTokenError}
      <div
        class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 max-w-3xl mx-auto"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="font-semibold">Token Validation Failed</p>
            <p class="text-sm mt-1">{data.error}</p>
          </div>
          <button
            on:click={handleClearToken}
            class="ml-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            Clear Token & Start Over
          </button>
        </div>
      </div>
    {/if}

    {#if error}
      <div
        class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 max-w-3xl mx-auto"
      >
        {error}
      </div>
    {/if}

    {#if showForm}
      <div class="bg-white rounded-lg shadow p-6 max-w-3xl mx-auto">
        <h2 class="text-2xl font-semibold text-gray-900 mb-4">Create New Interview</h2>
        <p class="text-gray-600 mb-6">
          Enter the job description and candidate resume to create a new interview session.
        </p>

        <form on:submit|preventDefault={handleCreateInterview} class="space-y-4">
          <div>
            <label for="job-description" class="block text-sm font-medium text-gray-700 mb-2">
              Job Description
            </label>
            <textarea
              id="job-description"
              bind:value={jobDescription}
              rows="6"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter the job description..."
              required
            ></textarea>
          </div>

          <div>
            <label for="resume-text" class="block text-sm font-medium text-gray-700 mb-2">
              Candidate Resume
            </label>
            <textarea
              id="resume-text"
              bind:value={resumeText}
              rows="12"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Paste the candidate's resume text..."
              required
            ></textarea>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Creating Interview..." : "Create Interview"}
          </button>
        </form>
      </div>
    {/if}
  </div>
</div>
