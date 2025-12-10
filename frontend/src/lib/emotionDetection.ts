import * as faceapi from "@vladmandic/face-api";

export interface EmotionScores {
  happy: number;
  sad: number;
  angry: number;
  fearful: number;
  disgusted: number;
  surprised: number;
  neutral: number;
}

export interface EmotionDetection {
  participantId: string;
  participantName?: string;
  emotions: EmotionScores;
  timestamp: number;
}

export class EmotionDetector {
  private isModelLoaded = false;
  private isLoading = false;
  private modelPath = "/models";

  /**
   * Load face-api.js models
   */
  async loadModels(): Promise<void> {
    if (this.isModelLoaded) {
      return;
    }

    if (this.isLoading) {
      // Wait for ongoing load to complete
      while (this.isLoading) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      return;
    }

    this.isLoading = true;

    try {
      console.log("[EmotionDetector] Loading face-api.js models...");

      // Load the required models
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(this.modelPath),
        faceapi.nets.faceExpressionNet.loadFromUri(this.modelPath),
      ]);

      this.isModelLoaded = true;
      this.isLoading = false;
      console.log("[EmotionDetector] Models loaded successfully");
    } catch (error) {
      this.isLoading = false;
      console.error("[EmotionDetector] Error loading models:", error);
      throw new Error(`Failed to load emotion detection models: ${error}`);
    }
  }

  /**
   * Check if models are loaded
   */
  get modelsLoaded(): boolean {
    return this.isModelLoaded;
  }

  /**
   * Check if models are currently loading
   */
  get modelsLoading(): boolean {
    return this.isLoading;
  }

  /**
   * Detect emotions from a video element
   */
  async detectEmotions(
    videoElement: HTMLVideoElement,
    participantId: string,
    participantName?: string
  ): Promise<EmotionDetection | null> {
    if (!this.isModelLoaded) {
      throw new Error("Models not loaded. Call loadModels() first.");
    }

    if (!videoElement) {
      console.log("[EmotionDetector] No video element provided");
      return null;
    }

    if (videoElement.readyState < 2) {
      console.log(`[EmotionDetector] Video not ready, readyState: ${videoElement.readyState}`);
      return null;
    }

    if (videoElement.videoWidth === 0 || videoElement.videoHeight === 0) {
      console.log(`[EmotionDetector] Video has no dimensions: ${videoElement.videoWidth}x${videoElement.videoHeight}`);
      return null;
    }

    try {
      console.log(`[EmotionDetector] Detecting faces in video ${videoElement.videoWidth}x${videoElement.videoHeight}`);
      
      // Detect faces and expressions
      const detections = await faceapi
        .detectAllFaces(videoElement, new faceapi.TinyFaceDetectorOptions())
        .withFaceExpressions();

      console.log(`[EmotionDetector] Found ${detections.length} face(s)`);

      if (detections.length === 0) {
        // No face detected
        return null;
      }

      // Use the first detected face (or largest face if multiple)
      const detection = detections.length === 1 
        ? detections[0] 
        : detections.reduce((prev, current) => 
            (current.detection.score > prev.detection.score ? current : prev)
          );

      const expressions = detection.expressions;

      return {
        participantId,
        participantName,
        emotions: {
          happy: expressions.happy || 0,
          sad: expressions.sad || 0,
          angry: expressions.angry || 0,
          fearful: expressions.fearful || 0,
          disgusted: expressions.disgusted || 0,
          surprised: expressions.surprised || 0,
          neutral: expressions.neutral || 0,
        },
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error("[EmotionDetector] Error detecting emotions:", error);
      return null;
    }
  }

  /**
   * Format emotion scores as percentages
   */
  formatEmotionPercentages(emotions: EmotionScores): Array<{ emotion: string; percentage: number }> {
    return Object.entries(emotions)
      .map(([emotion, score]) => ({
        emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
        percentage: Math.round(score * 100),
      }))
      .filter((item) => item.percentage > 0) // Only show emotions with > 0%
      .sort((a, b) => b.percentage - a.percentage); // Sort by percentage descending
  }

  /**
   * Get the dominant emotion
   */
  getDominantEmotion(emotions: EmotionScores): string {
    const entries = Object.entries(emotions);
    const maxEntry = entries.reduce((max, current) =>
      current[1] > max[1] ? current : max
    );
    return maxEntry[0].charAt(0).toUpperCase() + maxEntry[0].slice(1);
  }
}
