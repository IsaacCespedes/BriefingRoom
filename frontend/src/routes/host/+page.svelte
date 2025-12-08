<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import VapiOrb from '$lib/components/VapiOrb.svelte';
	import DailyCall from '$lib/components/DailyCall.svelte';
	import { generateBriefing } from '$lib/briefing';
	import { createRoom, getRoomUrl } from '$lib/daily';

	export let data: PageData;

	let jobDescription = '';
	let resumeText = '';
	let briefing: string | null = null;
	let isLoading = false;
	let error: string | null = null;
	let token: string | null = null;
	let roomUrl: string | null = null;
	let roomToken: string | null = null;
	let isLoadingRoom = false;

	onMount(() => {
		// Get token from URL or session storage
		const urlParams = new URLSearchParams(window.location.search);
		token = urlParams.get('token') || sessionStorage.getItem('token');
	});

	async function handleGenerateBriefing() {
		if (!token) {
			error = 'No token available';
			return;
		}

		if (!jobDescription.trim() || !resumeText.trim()) {
			error = 'Please provide both job description and resume text';
			return;
		}

		isLoading = true;
		error = null;

		try {
			const response = await generateBriefing(
				{
					job_description: jobDescription,
					resume_text: resumeText
				},
				token
			);

			briefing = response.briefing;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to generate briefing';
		} finally {
			isLoading = false;
		}
	}

	async function handleCreateRoom() {
		if (!token || !data.interviewId) {
			error = 'Token or interview ID not available';
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
						interview_id: data.interviewId
					},
					token
				);
				roomUrl = newRoom.room_url;
				roomToken = newRoom.room_token || null;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create/get room';
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

				<!-- Briefing Generation Form -->
				<div class="bg-white rounded-lg shadow p-6">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Generate Briefing</h2>

					{#if error}
						<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
							{error}
						</div>
					{/if}

					<form on:submit|preventDefault={handleGenerateBriefing} class="space-y-4">
						<div>
							<label for="job-description" class="block text-sm font-medium text-gray-700 mb-2">
								Job Description
							</label>
							<textarea
								id="job-description"
								bind:value={jobDescription}
								rows="5"
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
								placeholder="Enter the job description..."
								required
							></textarea>
						</div>

						<div>
							<label for="resume-text" class="block text-sm font-medium text-gray-700 mb-2">
								Resume Text
							</label>
							<textarea
								id="resume-text"
								bind:value={resumeText}
								rows="10"
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
								placeholder="Paste the candidate's resume text..."
								required
							></textarea>
						</div>

						<button
							type="submit"
							disabled={isLoading}
							class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{isLoading ? 'Generating...' : 'Generate Briefing'}
						</button>
					</form>

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
							apiKey={import.meta.env.VITE_VAPI_API_KEY || ''}
							assistantId={import.meta.env.VITE_VAPI_ASSISTANT_ID || ''}
							interviewId={data.interviewId || ''}
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
							{isLoadingRoom ? 'Creating Room...' : 'Start Video Call'}
						</button>
					{:else}
						<DailyCall roomUrl={roomUrl} token={roomToken} />
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

