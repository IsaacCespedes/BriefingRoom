<script lang="ts">
  import type { PageData } from "./$types";

  export let data: PageData;
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900">
  <div class="container mx-auto px-4 py-8">
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-2">Candidate View</h1>
      <p class="text-gray-400">Your interview session</p>
    </div>

    {#if data.error}
      <div class="bg-red-900/30 border border-red-700/50 text-red-300 px-6 py-4 rounded-xl mb-6 backdrop-blur-sm">
        {data.error}
      </div>
    {:else}
      <div class="bg-slate-800/50 backdrop-blur-md rounded-xl shadow-xl p-8 border border-slate-700/50">
        <div class="mb-6">
          <p class="text-gray-400 mb-2">Interview ID</p>
          <p class="text-blue-400 font-mono text-lg">{data.interviewId}</p>
        </div>
        <div class="p-6 bg-slate-900/50 rounded-lg border border-slate-600">
          <p class="text-gray-300 text-center">Candidate interface coming soon...</p>
        </div>
      </div>
    {/if}
  </div>
</div>
