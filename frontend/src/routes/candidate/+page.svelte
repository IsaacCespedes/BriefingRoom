<script lang="ts">
	import type { PageData } from './$types';

	export let data: PageData;
</script>

<div class="min-h-screen bg-gray-50">
	<div class="container mx-auto px-4 py-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">Candidate View</h1>

		{#if data.error}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{data.error}
			</div>
		{:else}
			<div class="bg-white rounded-lg shadow p-6">
				<p class="text-gray-700 mb-4">Interview ID: {data.interviewId}</p>
				<p class="text-gray-700">Candidate interface coming soon...</p>
			</div>
		{/if}
	</div>
</div>

