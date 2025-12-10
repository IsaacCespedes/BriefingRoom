<script lang="ts">
  import { onMount } from "svelte";
  import {
    getTranscript,
    downloadTranscript,
    fetchTranscriptFromDaily,
    downloadBlob,
    type TranscriptResponse,
  } from "$lib/transcripts";
  import {
    getTranscript as getLocalTranscript,
    transcriptToText,
    transcriptToStructured,
    type StoredTranscript,
  } from "$lib/transcriptStorage";

  export let interviewId: string;
  export let token: string;

  let transcript: TranscriptResponse | null = null;
  let localTranscript: StoredTranscript | null = null;
  let isLoading = false;
  let isFetching = false;
  let error: string | null = null;
  let selectedFormat: "txt" | "vtt" | "json" = "txt";
  let showPreview = false;
  let transcriptSource: "local" | "backend" | null = null; // Track where transcript came from

  onMount(() => {
    loadTranscript();
  });

  async function loadTranscript() {
    if (!token || !interviewId) {
      return;
    }

    isLoading = true;
    error = null;

    // First, check local storage
    localTranscript = getLocalTranscript(interviewId);

    if (localTranscript && localTranscript.segments.length > 0) {
      // Convert local transcript to TranscriptResponse format for display
      const structured = transcriptToStructured(localTranscript);
      const text = transcriptToText(localTranscript);

      transcript = {
        id: interviewId, // Use interview ID as placeholder
        interview_id: interviewId,
        daily_room_name: localTranscript.roomName,
        transcript_text: text,
        transcript_data: { segments: structured.segments },
        started_at: structured.started_at,
        ended_at: structured.ended_at,
        duration_seconds: structured.duration_seconds,
        participant_count: structured.segments.reduce((acc, seg) => {
          if (seg.speaker && !acc.includes(seg.speaker)) {
            acc.push(seg.speaker);
          }
          return acc;
        }, [] as string[]).length,
        status: localTranscript.isComplete ? "completed" : "processing",
        created_at: new Date(localTranscript.startedAt).toISOString(),
        updated_at: new Date(localTranscript.lastUpdatedAt).toISOString(),
      };
      transcriptSource = "local";
      isLoading = false;

      // Also try to load from backend in the background (for merging/backup)
      try {
        const backendTranscript = await getTranscript(interviewId, token);
        if (backendTranscript && backendTranscript.status === "completed") {
          // Backend has a complete transcript, prefer it
          transcript = backendTranscript;
          transcriptSource = "backend";
        }
      } catch {
        // Backend transcript not available, that's okay - we have local
      }

      return;
    }

    // No local transcript, try backend
    try {
      transcript = await getTranscript(interviewId, token);
      transcriptSource = "backend";
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Failed to load transcript";
      // If transcript not found, that's okay - user can fetch it
      if (errorMessage.includes("not found")) {
        transcript = null;
        error = null; // Don't show error for not found
      } else {
        error = errorMessage;
      }
    } finally {
      isLoading = false;
    }
  }

  async function handleFetchTranscript() {
    if (!token || !interviewId) {
      error = "Token or interview ID not available";
      return;
    }

    isFetching = true;
    error = null;

    try {
      transcript = await fetchTranscriptFromDaily(interviewId, token);
      // If transcript is still pending, show appropriate message
      if (transcript.status === "pending") {
        error =
          "Daily.co transcript is still being processed. The call may still be active, or Daily.co is processing the transcript. Your local transcript should be available immediately.";
        transcript = null;
      } else if (transcript.status === "processing") {
        error =
          "Daily.co transcript is currently being processed. Your local transcript should be available immediately.";
        transcript = null;
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Failed to fetch transcript";
      // Provide more helpful error messages
      if (errorMessage.includes("not found") || errorMessage.includes("not available")) {
        error =
          "Daily.co transcript not available yet. The call may still be active, or Daily.co is still processing. Your local transcript should be available immediately if you were in the call.";
      } else {
        error = errorMessage;
      }
      transcript = null;
    } finally {
      isFetching = false;
    }
  }

  async function handleDownload() {
    if (!interviewId || !transcript) {
      return;
    }

    try {
      // If transcript is from local storage, create blob directly
      if (transcriptSource === "local" && localTranscript) {
        let content = "";
        let mimeType = "text/plain";
        let extension = "txt";

        if (selectedFormat === "txt") {
          content = transcriptToText(localTranscript);
        } else if (selectedFormat === "json") {
          const structured = transcriptToStructured(localTranscript);
          content = JSON.stringify(
            {
              interview_id: interviewId,
              transcript_text: transcriptToText(localTranscript),
              transcript_data: { segments: structured.segments },
              started_at: structured.started_at,
              ended_at: structured.ended_at,
              duration_seconds: structured.duration_seconds,
              source: "local_storage",
            },
            null,
            2
          );
          mimeType = "application/json";
          extension = "json";
        } else {
          // VTT format - convert segments to WebVTT
          const structured = transcriptToStructured(localTranscript);
          content = "WEBVTT\n\n";
          structured.segments.forEach((seg) => {
            const start = formatWebVTTTime(seg.start_time);
            const end = formatWebVTTTime(seg.end_time);
            content += `${start} --> ${end}\n`;
            if (seg.speaker) {
              content += `${seg.speaker}: ${seg.text}\n\n`;
            } else {
              content += `${seg.text}\n\n`;
            }
          });
          mimeType = "text/vtt";
          extension = "vtt";
        }

        const blob = new Blob([content], { type: mimeType });
        const filename = `transcript-${interviewId}.${extension}`;
        downloadBlob(blob, filename);
      } else {
        // Download from backend
        if (!token) {
          error = "Token required for backend download";
          return;
        }
        const blob = await downloadTranscript(interviewId, selectedFormat, token);
        const extension =
          selectedFormat === "txt" ? "txt" : selectedFormat === "vtt" ? "vtt" : "json";
        const filename = `transcript-${interviewId}.${extension}`;
        downloadBlob(blob, filename);
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to download transcript";
    }
  }

  function formatWebVTTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${millis.toString().padStart(3, "0")}`;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case "completed":
        return "text-green-400";
      case "processing":
        return "text-yellow-400";
      case "pending":
        return "text-gray-400";
      case "failed":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  }

  function formatDuration(seconds?: number): string {
    if (!seconds) return "N/A";
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  }
</script>

<div class="space-y-4">
  <div class="flex justify-between items-center">
    <h3 class="text-lg font-semibold text-white">Transcript</h3>
    <div class="flex gap-2 items-center">
      {#if transcriptSource === "local"}
        <span
          class="px-2 py-1 text-xs text-blue-300 rounded bg-blue-700/50"
          title="From local storage"
        >
          Local
        </span>
      {:else if transcriptSource === "backend"}
        <span class="px-2 py-1 text-xs text-green-300 rounded bg-green-700/50" title="From backend">
          Backend
        </span>
      {/if}
      {#if transcript}
        <span class="text-sm px-2 py-1 rounded bg-slate-700/50 {getStatusColor(transcript.status)}">
          {transcript.status}
        </span>
      {/if}
    </div>
  </div>

  {#if error}
    <div
      class="px-4 py-3 text-sm text-red-300 rounded-lg border backdrop-blur-sm bg-red-900/30 border-red-700/50"
    >
      {error}
    </div>
  {/if}

  {#if isLoading}
    <div class="flex justify-center items-center py-8">
      <div class="text-gray-400">Loading transcript...</div>
    </div>
  {:else if !transcript}
    <div class="space-y-4">
      <div class="space-y-2 text-sm text-gray-400">
        <p>Transcripts are captured in real-time during the call.</p>
        <p class="text-xs text-gray-500">
          <strong>Note:</strong> The transcript will appear as conversation progresses.
        </p>
      </div>
      <button
        on:click={handleFetchTranscript}
        disabled={isFetching}
        class="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg transition-all duration-200 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isFetching ? "Fetching..." : "Fetch Transcript from Daily.co"}
      </button>
    </div>
  {:else if transcript.status === "completed"}
    <div class="space-y-4">
      <!-- Transcript Metadata -->
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-gray-500">Duration:</span>
          <span class="ml-2 text-gray-300">{formatDuration(transcript.duration_seconds)}</span>
        </div>
        {#if transcript.participant_count}
          <div>
            <span class="text-gray-500">Participants:</span>
            <span class="ml-2 text-gray-300">{transcript.participant_count}</span>
          </div>
        {/if}
      </div>

      <!-- Download Options -->
      <div class="space-y-3">
        <div class="flex gap-4 items-center">
          <label class="text-sm font-medium text-gray-300">Format:</label>
          <select
            bind:value={selectedFormat}
            class="px-3 py-1.5 text-sm text-white rounded-lg border bg-slate-700/50 border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="txt">Plain Text (.txt)</option>
            <option value="vtt">WebVTT (.vtt)</option>
            <option value="json">JSON (.json)</option>
          </select>
          <button
            on:click={handleDownload}
            class="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg transition-all duration-200 hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900"
          >
            Download
          </button>
        </div>
      </div>

      <!-- Preview Toggle -->
      <div>
        <button
          on:click={() => (showPreview = !showPreview)}
          class="text-sm text-blue-400 hover:text-blue-300 focus:outline-none"
        >
          {showPreview ? "Hide Preview" : "Show Preview"}
        </button>
        {#if showPreview}
          <div
            class="overflow-y-auto p-4 mt-3 max-h-64 rounded-lg border bg-slate-900/50 border-slate-600"
          >
            <pre
              class="font-mono text-sm text-gray-300 whitespace-pre-wrap">{transcript.transcript_text}</pre>
          </div>
        {/if}
      </div>
    </div>
  {:else if transcript.status === "pending" || transcript.status === "processing"}
    <div class="space-y-4">
      <div class="space-y-2 text-sm text-gray-400">
        <p>
          Daily.co transcript is {transcript.status === "pending" ? "pending" : "being processed"}.
        </p>
        <p class="text-xs text-gray-500">
          <strong>Note:</strong> Your local transcript (captured during the call) should be available
          immediately above. The Daily.co transcript may take 1-5 minutes after the call ends to process.
        </p>
      </div>
      <button
        on:click={handleFetchTranscript}
        disabled={isFetching}
        class="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg transition-all duration-200 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isFetching ? "Refreshing..." : "Refresh Status"}
      </button>
    </div>
  {:else if transcript.status === "failed"}
    <div class="space-y-4">
      <p class="text-sm text-red-400">Transcript processing failed. Please try fetching again.</p>
      <button
        on:click={handleFetchTranscript}
        disabled={isFetching}
        class="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg transition-all duration-200 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isFetching ? "Retrying..." : "Retry Fetch"}
      </button>
    </div>
  {/if}
</div>
