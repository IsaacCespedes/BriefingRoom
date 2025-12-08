import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createRoom, getRoomUrl } from '../daily';

describe('Daily.co API', () => {
	const originalFetch = global.fetch;
	const API_BASE_URL = 'http://localhost:8000';
	const mockToken = 'test-token';

	beforeEach(() => {
		global.fetch = vi.fn();
	});

	afterEach(() => {
		global.fetch = originalFetch;
		vi.clearAllMocks();
	});

	describe('createRoom', () => {
		it('should create a room successfully', async () => {
			const request = {
				interview_id: 'interview-123'
			};

			const mockResponse = {
				room_url: 'https://test.daily.co/test-room',
				room_token: 'test-token'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockResponse
			});

			const result = await createRoom(request, mockToken);

			expect(global.fetch).toHaveBeenCalledWith(
				`${API_BASE_URL}/api/daily/create-room`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${mockToken}`
					},
					body: JSON.stringify(request)
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should throw error when request fails', async () => {
			const request = {
				interview_id: 'interview-123'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: false,
				status: 500,
				statusText: 'Internal Server Error',
				json: async () => ({ detail: 'Failed to create room' })
			});

			await expect(createRoom(request, mockToken)).rejects.toThrow('Failed to create room');
		});
	});

	describe('getRoomUrl', () => {
		it('should get room URL successfully', async () => {
			const interviewId = 'interview-123';
			const mockResponse = {
				room_url: 'https://test.daily.co/test-room',
				room_token: 'test-token'
			};

			(global.fetch as any).mockResolvedValueOnce({
				ok: true,
				json: async () => mockResponse
			});

			const result = await getRoomUrl(interviewId, mockToken);

			expect(global.fetch).toHaveBeenCalledWith(
				`${API_BASE_URL}/api/daily/room/${interviewId}`,
				{
					method: 'GET',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${mockToken}`
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should throw error when room not found', async () => {
			const interviewId = 'non-existent';

			(global.fetch as any).mockResolvedValueOnce({
				ok: false,
				status: 404,
				statusText: 'Not Found',
				json: async () => ({ detail: 'Room not found' })
			});

			await expect(getRoomUrl(interviewId, mockToken)).rejects.toThrow('Room not found');
		});
	});
});

