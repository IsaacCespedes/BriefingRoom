/**
 * Local storage service for emotion detection data.
 * 
 * Stores emotion detections in local storage as they are detected during the call.
 * This provides immediate access and handles cases where the call is suddenly closed.
 */

import type { EmotionDetection } from "$lib/emotionDetection";

export interface StoredEmotionDetection {
  interviewId: string;
  detections: EmotionDetection[];
  startedAt: number; // Unix timestamp
  lastUpdatedAt: number; // Unix timestamp
  isComplete: boolean; // Whether the call has ended
}

const STORAGE_PREFIX = "emotions_";
const MAX_STORAGE_SIZE = 5 * 1024 * 1024; // 5MB limit per interview

/**
 * Get storage key for an interview
 */
function getStorageKey(interviewId: string): string {
  return `${STORAGE_PREFIX}${interviewId}`;
}

/**
 * Initialize emotion storage for an interview
 */
export function initializeEmotionStorage(interviewId: string): void {
  const key = getStorageKey(interviewId);
  const storage: StoredEmotionDetection = {
    interviewId,
    detections: [],
    startedAt: Date.now(),
    lastUpdatedAt: Date.now(),
    isComplete: false,
  };
  
  try {
    localStorage.setItem(key, JSON.stringify(storage));
  } catch (e) {
    console.error("[EmotionStorage] Failed to initialize storage:", e);
    // If storage is full, try to clear old data
    clearOldEmotionStorage();
    try {
      localStorage.setItem(key, JSON.stringify(storage));
    } catch (e2) {
      console.error("[EmotionStorage] Failed after cleanup:", e2);
    }
  }
}

/**
 * Add an emotion detection to storage
 */
export function addEmotionDetection(
  interviewId: string,
  detection: EmotionDetection
): void {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) {
      console.warn("[EmotionStorage] Storage not initialized, initializing now");
      initializeEmotionStorage(interviewId);
      // Retry after initialization
      addEmotionDetection(interviewId, detection);
      return;
    }
    
    const storage: StoredEmotionDetection = JSON.parse(stored);
    
    storage.detections.push(detection);
    storage.lastUpdatedAt = Date.now();
    
    // Check storage size
    const size = JSON.stringify(storage).length;
    if (size > MAX_STORAGE_SIZE) {
      console.warn("[EmotionStorage] Storage approaching size limit, keeping only recent detections");
      // Keep only the most recent 5000 detections
      storage.detections = storage.detections.slice(-5000);
    }
    
    localStorage.setItem(key, JSON.stringify(storage));
  } catch (e) {
    console.error("[EmotionStorage] Failed to add detection:", e);
  }
}

/**
 * Mark emotion storage as complete (call ended)
 */
export function markEmotionStorageComplete(interviewId: string): void {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return;
    
    const storage: StoredEmotionDetection = JSON.parse(stored);
    storage.isComplete = true;
    storage.lastUpdatedAt = Date.now();
    
    localStorage.setItem(key, JSON.stringify(storage));
  } catch (e) {
    console.error("[EmotionStorage] Failed to mark complete:", e);
  }
}

/**
 * Get emotion storage from local storage
 */
export function getEmotionStorage(interviewId: string): StoredEmotionDetection | null {
  const key = getStorageKey(interviewId);
  
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return null;
    
    return JSON.parse(stored) as StoredEmotionDetection;
  } catch (e) {
    console.error("[EmotionStorage] Failed to get storage:", e);
    return null;
  }
}

/**
 * Convert stored emotions to structured format (for backend)
 */
export function emotionsToStructured(storage: StoredEmotionDetection): {
  detections: Array<{
    participantId: string;
    participantName?: string;
    timestamp: number; // Unix timestamp
    emotions: {
      happy: number;
      sad: number;
      angry: number;
      fearful: number;
      disgusted: number;
      surprised: number;
      neutral: number;
    };
  }>;
  started_at: string; // ISO timestamp
  ended_at: string | null; // ISO timestamp
  duration_seconds: number;
} {
  const startTime = storage.startedAt;
  const endTime = storage.isComplete ? storage.lastUpdatedAt : Date.now();
  
  return {
    detections: storage.detections.map((detection) => ({
      participantId: detection.participantId,
      participantName: detection.participantName,
      timestamp: detection.timestamp,
      // Convert decimal values (0.0-1.0) to whole number percentages (0-100)
      emotions: {
        happy: Math.round(detection.emotions.happy * 100),
        sad: Math.round(detection.emotions.sad * 100),
        angry: Math.round(detection.emotions.angry * 100),
        fearful: Math.round(detection.emotions.fearful * 100),
        disgusted: Math.round(detection.emotions.disgusted * 100),
        surprised: Math.round(detection.emotions.surprised * 100),
        neutral: Math.round(detection.emotions.neutral * 100),
      },
    })),
    started_at: new Date(startTime).toISOString(),
    ended_at: storage.isComplete ? new Date(endTime).toISOString() : null,
    duration_seconds: Math.floor((endTime - startTime) / 1000),
  };
}

/**
 * Clear emotion storage from local storage
 */
export function clearEmotionStorage(interviewId: string): void {
  const key = getStorageKey(interviewId);
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.error("[EmotionStorage] Failed to clear storage:", e);
  }
}

/**
 * Clear old emotion storage (keep only the 10 most recent)
 */
function clearOldEmotionStorage(): void {
  try {
    const keys = Object.keys(localStorage).filter((key) => key.startsWith(STORAGE_PREFIX));
    
    if (keys.length <= 10) return;
    
    // Get all storages with their last updated times
    const storages = keys
      .map((key) => {
        try {
          const stored = localStorage.getItem(key);
          if (!stored) return null;
          const storage: StoredEmotionDetection = JSON.parse(stored);
          return { key, lastUpdated: storage.lastUpdatedAt };
        } catch {
          return null;
        }
      })
      .filter((t): t is { key: string; lastUpdated: number } => t !== null);
    
    // Sort by last updated (oldest first)
    storages.sort((a, b) => a.lastUpdated - b.lastUpdated);
    
    // Remove oldest storages (keep 10 most recent)
    const toRemove = storages.slice(0, storages.length - 10);
    toRemove.forEach(({ key }) => localStorage.removeItem(key));
    
    console.log(`[EmotionStorage] Cleared ${toRemove.length} old storages`);
  } catch (e) {
    console.error("[EmotionStorage] Failed to clear old storages:", e);
  }
}
