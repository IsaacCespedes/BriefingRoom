import { describe, it, expect, vi, beforeEach } from 'vitest';
import { load } from '../+page.server';
import { validateToken } from '$lib/api';

vi.mock('$lib/api');

describe('host +page.server load function', () => {
	const mockUrl = {
		searchParams: {
			get: vi.fn()
		}
	} as any;

	const mockCookies = {
		get: vi.fn()
	} as any;

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should return 401 when no token is provided', async () => {
		mockUrl.searchParams.get.mockReturnValue(null);
		mockCookies.get.mockReturnValue(null);

		const result = await load({ url: mockUrl, cookies: mockCookies } as any);

		expect(result.status).toBe(401);
		expect(result.data).toHaveProperty('error', 'No token provided');
		expect(result.data).toHaveProperty('role', null);
		expect(result.data).toHaveProperty('interviewId', null);
	});

	it('should return role and interview_id for valid host token', async () => {
		const token = 'host-token';
		mockUrl.searchParams.get.mockReturnValue(token);
		mockCookies.get.mockReturnValue(null);

		vi.mocked(validateToken).mockResolvedValue({
			role: 'host',
			interview_id: 'interview-123'
		});

		const result = await load({ url: mockUrl, cookies: mockCookies } as any);

		expect(result).toEqual({
			role: 'host',
			interviewId: 'interview-123',
			error: null
		});
	});

	it('should return 403 when token has candidate role', async () => {
		const token = 'candidate-token';
		mockUrl.searchParams.get.mockReturnValue(token);
		mockCookies.get.mockReturnValue(null);

		vi.mocked(validateToken).mockResolvedValue({
			role: 'candidate',
			interview_id: 'interview-456'
		});

		const result = await load({ url: mockUrl, cookies: mockCookies } as any);

		expect(result.status).toBe(403);
		expect(result.data).toHaveProperty('error', 'Access denied. Host role required.');
		expect(result.data).toHaveProperty('role', 'candidate');
		expect(result.data).toHaveProperty('interviewId', 'interview-456');
	});

	it('should return 401 when token validation fails', async () => {
		const token = 'invalid-token';
		mockUrl.searchParams.get.mockReturnValue(token);
		mockCookies.get.mockReturnValue(null);

		vi.mocked(validateToken).mockRejectedValue(new Error('Invalid or expired token'));

		const result = await load({ url: mockUrl, cookies: mockCookies } as any);

		expect(result.status).toBe(401);
		expect(result.data).toHaveProperty('error', 'Invalid or expired token');
		expect(result.data).toHaveProperty('role', null);
		expect(result.data).toHaveProperty('interviewId', null);
	});

	it('should use token from cookie if query parameter is not present', async () => {
		const token = 'cookie-token';
		mockUrl.searchParams.get.mockReturnValue(null);
		mockCookies.get.mockReturnValue(token);

		vi.mocked(validateToken).mockResolvedValue({
			role: 'host',
			interview_id: 'interview-789'
		});

		const result = await load({ url: mockUrl, cookies: mockCookies } as any);

		expect(validateToken).toHaveBeenCalledWith(token);
		expect(result.role).toBe('host');
	});
});

