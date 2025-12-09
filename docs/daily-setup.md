# Daily.co Video Call Setup Guide

This guide explains how to set up Daily.co video call functionality for the Bionic Interviewer application.

## Overview

The video call functionality uses Daily.co's REST API to create and manage video call rooms. The frontend is already implemented, and this guide will help you configure the backend.

## Step 1: Get Your Daily.co API Key

1. **Sign up or log in** to [Daily.co](https://www.daily.co)
2. **Choose a subdomain** during setup (e.g., `yourcompany.daily.co`)
3. **Get your API key**:
   - Navigate to the **Developers** section in your Daily.co dashboard
   - Find your **API key** and copy it
   - The API key looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 2: Configure Environment Variables

### For Local Development

Create a `.env` file in the project root (or add to your existing `.env` file):

```bash
DAILY_API_KEY=your_daily_api_key_here
DAILY_API_URL=https://api.daily.co/v1  # Optional, defaults to this value
```

### For Docker Compose

The `docker-compose.yml` file is already configured to read the `DAILY_API_KEY` from your environment. Make sure you have it set:

```bash
export DAILY_API_KEY=your_daily_api_key_here
docker-compose up
```

Or add it to your `.env` file and Docker Compose will automatically load it.

## Step 3: Verify the Setup

1. **Start the backend**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Check the logs** - The backend will raise an error at startup if `DAILY_API_KEY` is missing

3. **Test the endpoint** (requires authentication token):
   ```bash
   curl -X POST http://localhost:8000/api/daily/create-room \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"interview_id": "test-interview-123"}'
   ```

## How It Works

### Backend Flow

1. **Create Room** (`POST /api/daily/create-room`):
   - Takes an `interview_id`
   - Creates a Daily.co room named `interview-{interview_id}`
   - Generates a secure meeting token
   - Returns the room URL and token

2. **Get Room** (`GET /api/daily/room/{interview_id}`):
   - Retrieves an existing room for an interview
   - Generates a new meeting token if needed
   - Returns the room URL and token

### Frontend Flow

1. User clicks "Start Video Call" on the host page
2. Frontend calls `createRoom()` which hits `/api/daily/create-room`
3. Backend creates the Daily.co room and returns the URL
4. Frontend renders the `DailyCall` component with the room URL
5. User clicks "Join Call" to enter the video call

## Security Notes

- ✅ **API key is server-side only** - Never exposed to the frontend
- ✅ **Meeting tokens** - Generated per-request for secure access
- ✅ **Token expiration** - Meeting tokens expire after 24 hours
- ✅ **Authentication required** - All endpoints require a valid bearer token

## Room Configuration

The current implementation creates rooms with:
- **Privacy**: Public (anyone with the link can join)
- **Chat**: Enabled
- **Screen sharing**: Enabled
- **Recording**: Disabled (can be enabled in `backend/app/api/daily.py`)

To customize room properties, edit the `room_properties` dictionary in the `create_room` function in `backend/app/api/daily.py`.

## Troubleshooting

### Error: "DAILY_API_KEY must be set"
- Make sure you've set the `DAILY_API_KEY` environment variable
- Restart the backend after setting the variable

### Error: "Daily.co API error: 401"
- Your API key is invalid or expired
- Get a new API key from the Daily.co dashboard

### Error: "Room not found"
- The room hasn't been created yet
- Call the `create-room` endpoint first

### Video call not loading
- Check browser console for errors
- Ensure the Daily.co SDK is loaded (`@daily-co/daily-js` package)
- Verify the room URL is valid

## Additional Resources

- [Daily.co REST API Documentation](https://docs.daily.co/reference/rest-api)
- [Daily.co JavaScript SDK](https://docs.daily.co/reference/daily-js)
- [Daily.co Dashboard](https://dashboard.daily.co)

