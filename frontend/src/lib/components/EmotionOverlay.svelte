<script lang="ts">
  import type { EmotionScores } from "$lib/emotionDetection";

  export let emotions: EmotionScores | null = null;
  export let participantName: string | null = null;
  export let position: "top-left" | "top-right" | "bottom-left" | "bottom-right" = "top-left";

  type EmotionItem = { emotion: string; percentage: number };

  let emotionList: EmotionItem[] = [];

  $: {
    emotionList = emotions
      ? Object.entries(emotions)
          .map(([emotion, score]: [string, number]) => ({
            emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
            percentage: Math.round(score * 100),
          }))
          .filter((item: EmotionItem) => item.percentage > 0)
          .sort((a: EmotionItem, b: EmotionItem) => b.percentage - a.percentage)
      : [];
  }

  $: positionClasses = {
    "top-left": "top-2 left-2",
    "top-right": "top-2 right-2",
    "bottom-left": "bottom-2 left-2",
    "bottom-right": "bottom-2 right-2",
  };
</script>

{#if emotions && emotionList.length > 0}
  <div
    class="emotion-overlay {positionClasses[position]}"
    role="region"
    aria-label="Emotion detection results"
  >
    {#if participantName}
      <div class="emotion-participant-name">{participantName}</div>
    {/if}
    <div class="emotion-list">
      {#each emotionList as { emotion, percentage }}
        <div class="emotion-item">
          <span class="emotion-label">{emotion}:</span>
          <span class="emotion-percentage">{percentage}%</span>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .emotion-overlay {
    position: absolute;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(8px);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    z-index: 50;
    min-width: 180px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    pointer-events: none;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .emotion-participant-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: #60a5fa;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .emotion-list {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .emotion-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
    line-height: 1.4;
  }

  .emotion-label {
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }

  .emotion-percentage {
    color: #10b981;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
</style>
