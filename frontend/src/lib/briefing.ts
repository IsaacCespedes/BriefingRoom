import type { Interview } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface GenerateBriefingRequest {
	job_description: string;
	resume_text: string;
}

export interface GenerateBriefingResponse {
	interview_id: string;
	briefing: string;
}

/**
 * Generate a briefing for an interview
 */
export async function generateBriefing(
	request: GenerateBriefingRequest,
	token: string
): Promise<GenerateBriefingResponse> {
	const response = await fetch(`${API_BASE_URL}/generate-briefing`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(request)
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: response.statusText }));
		throw new Error(error.detail || `Failed to generate briefing: ${response.statusText}`);
	}

	return response.json();
}

/**
 * Get interview details
 */
export async function getInterview(interviewId: string, token: string): Promise<Interview> {
	const response = await fetch(`${API_BASE_URL}/api/interviews/${interviewId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: response.statusText }));
		throw new Error(error.detail || `Failed to get interview: ${response.statusText}`);
	}

	return response.json();
}

