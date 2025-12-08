<script lang="ts">
	import { onMount } from 'svelte';

	let token: string | null = null;
	let role: 'host' | 'candidate' | null = null;
	let error: string | null = null;

	onMount(() => {
		// Extract token from URL query parameter
		const urlParams = new URLSearchParams(window.location.search);
		token = urlParams.get('token');

		if (token) {
			// Store token in session storage
			sessionStorage.setItem('token', token);
			// TODO: Validate token and get role from backend
		} else {
			// Try to get token from session storage
			token = sessionStorage.getItem('token');
		}
	});
</script>

<div class="min-h-screen bg-gray-50">
	<div class="container mx-auto px-4 py-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">Bionic Interviewer</h1>

		{#if error}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{error}
			</div>
		{/if}

		{#if !token}
			<div class="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
				Please provide a token via URL query parameter (?token=...)
			</div>
		{:else}
			<div class="bg-white rounded-lg shadow p-6">
				<p class="text-gray-700">Token loaded. Role detection coming soon...</p>
			</div>
		{/if}
	</div>
</div>

