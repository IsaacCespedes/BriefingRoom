import type { TokenInfo } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Validates a token and returns the role and interview_id
 */
export async function validateToken(token: string): Promise<TokenInfo> {
	const response = await fetch(`${API_BASE_URL}/api/validate-token?token=${encodeURIComponent(token)}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json'
		}
	});

	if (!response.ok) {
		if (response.status === 401) {
			throw new Error('Invalid or expired token');
		}
		throw new Error(`Token validation failed: ${response.statusText}`);
	}

	return response.json();
}

