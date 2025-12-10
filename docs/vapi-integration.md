# Vapi Integration Documentation

This document describes the complete implementation of Vapi voice AI integration into the BriefingRoom application.

## Overview

Vapi is integrated to provide voice-based interactive briefings for interview hosts. The implementation uses a secure proxy pattern where API keys are kept on the backend, and the frontend SDK communicates through a backend proxy endpoint.

## Implementation Steps

### 1. Backend Proxy Implementation

**File: `backend/app/api/vapi.py`**

Created a new FastAPI router with the following endpoints:

- **`GET /api/vapi/public-key`**: Returns the Vapi public key for frontend SDK initialization
- **`POST /api/vapi/call`**: Convenience endpoint to create Vapi calls
- **`* /api/vapi/proxy/{path:path}`**: Generic proxy endpoint that forwards all requests to Vapi API

**Key Features:**
- All endpoints require authentication via token validation
- API keys are stored securely on the backend
- Proxy endpoint supports all HTTP methods (GET, POST, PUT, DELETE)
- Automatically injects `interviewId` into call context

**Security:**
- Vapi API key (`VAPI_API_KEY`) never exposed to frontend
- Only public key (`VAPI_PUBLIC_KEY`) is accessible to frontend
- All API calls go through authenticated backend proxy

### 2. Frontend SDK Integration

**File: `frontend/src/lib/components/VapiOrb.svelte`**

Completely rewrote the component to use the Vapi SDK properly:

**Initialization:**
- Fetches public key from backend if not provided via props
- Initializes Vapi SDK with public key and proxy URL
- Sets up comprehensive event listeners for call state management

**Event Handling:**
- `call-start`: Call connected
- `call-end`: Call disconnected
- `user-speech-start/end`: User speaking indicators
- `assistant-speech-start/end`: Assistant speaking indicators
- `error`: Error handling

**Methods:**
- `startBriefing()`: Starts a Vapi call with assistant ID and interview context
- `stopBriefing()`: Stops active call and cleans up

**File: `frontend/src/lib/vapi.ts`**

Created utility functions for Vapi API interactions:

- `getVapiPublicKey(token)`: Fetches public key from backend
- `createVapiCall(request, token)`: Creates a Vapi call via backend

### 3. Frontend Integration Updates

**File: `frontend/src/routes/host/+page.svelte`**

Updated to pass authentication token and use new prop names:
- Changed `apiKey` prop to `publicKey`
- Added `token` prop for authentication
- Removed direct environment variable usage (now uses backend)

### 4. Backend Router Registration

**File: `backend/app/main.py`**

- Added import for `vapi` router
- Registered router with `/api` prefix and `vapi` tag

### 5. Docker Compose Configuration

**File: `docker-compose.yml`**

**Backend Environment Variables:**
```yaml
- VAPI_API_KEY=${VAPI_API_KEY}
- VAPI_API_URL=${VAPI_API_URL:-https://api.vapi.ai}
- VAPI_PUBLIC_KEY=${VAPI_PUBLIC_KEY}
```

**Frontend Environment Variables:**
```yaml
- VITE_VAPI_PUBLIC_KEY=${VITE_VAPI_PUBLIC_KEY}
- VITE_VAPI_ASSISTANT_ID=${VITE_VAPI_ASSISTANT_ID}
```

## Required Environment Variables

### Backend (.env or environment)
- **`VAPI_API_KEY`** (Required): Your Vapi API key for server-side API calls
- **`VAPI_API_URL`** (Optional): Vapi API base URL (default: `https://api.vapi.ai`)
- **`VAPI_PUBLIC_KEY`** (Required): Your Vapi public key for frontend SDK initialization

### Frontend (build-time variables)
- **`VITE_VAPI_PUBLIC_KEY`** (Optional): Public key can be passed at build time, but preferred method is fetching from backend
- **`VITE_VAPI_ASSISTANT_ID`** (Required): Your Vapi assistant ID

## How to Set Up

### 1. Get Your Vapi Credentials

1. Sign up for a Vapi account at [vapi.ai](https://vapi.ai)
2. Get your API key from the dashboard (for backend use)
3. Get your public key from the dashboard (for frontend SDK)
4. Create an assistant and note its ID

### 2. Configure Environment Variables

**For Local Development:**

Create or update `.env` file in project root:
```bash
# Backend Vapi configuration
VAPI_API_KEY=your-api-key-here
VAPI_PUBLIC_KEY=your-public-key-here
VAPI_API_URL=https://api.vapi.ai

# Frontend Vapi configuration
VITE_VAPI_ASSISTANT_ID=your-assistant-id-here
VITE_VAPI_PUBLIC_KEY=your-public-key-here  # Optional, can be fetched from backend
```

**For Docker Compose:**

Add the same variables to your `.env` file or set them in your shell environment before running `docker-compose up`.

### 3. How It Works

1. **Frontend Initialization:**
   - `VapiOrb` component mounts
   - If `publicKey` prop is not provided, fetches it from `/api/vapi/public-key`
   - Initializes Vapi SDK with public key and proxy URL (`http://backend:8000/api/vapi/proxy`)

2. **Starting a Call:**
   - User clicks "Start Briefing"
   - Component calls `vapi.start()` with assistant ID
   - SDK makes request to proxy URL with authentication
   - Backend forwards request to Vapi API with API key
   - Backend injects `interviewId` into call context
   - Call starts and events are streamed back to frontend

3. **During Call:**
   - Event listeners update UI state (listening, speaking, etc.)
   - Audio streams through Vapi service
   - Conversation context includes interview ID

4. **Stopping a Call:**
   - User clicks "Stop Briefing"
   - Component calls `vapi.stop()`
   - SDK sends stop request through proxy
   - Call ends and state resets

## Security Considerations

1. **API Key Protection:**
   - API key never leaves the backend
   - Frontend only has access to public key (limited permissions)
   - All API calls go through authenticated proxy

2. **Authentication:**
   - All proxy endpoints require valid token
   - Token validation ensures user has access to specific interview
   - Interview ID is automatically injected from token context

3. **Proxy Pattern:**
   - Frontend SDK configured to use backend proxy URL
   - Backend acts as intermediary for all Vapi API calls
   - Headers and query parameters are properly forwarded

## Testing

1. **Backend Endpoints:**
   ```bash
   # Get public key
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/vapi/public-key
   
   # Create a call (example)
   curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"assistantId": "your-assistant-id"}' \
     http://localhost:8000/api/vapi/call
   ```

2. **Frontend Component:**
   - Navigate to host dashboard
   - Generate a briefing
   - Click "Start Briefing" button
   - Verify call connects and audio works
   - Test stop functionality

## Troubleshooting

### Common Issues

1. **"Vapi not initialized" error:**
   - Check that `VAPI_PUBLIC_KEY` is set in backend
   - Verify token is being passed to component
   - Check browser console for initialization errors

2. **"Failed to fetch public key":**
   - Verify backend is running
   - Check authentication token is valid
   - Verify `VAPI_PUBLIC_KEY` environment variable is set

3. **"Failed to start briefing":**
   - Verify `VITE_VAPI_ASSISTANT_ID` is set
   - Check assistant ID is correct
   - Verify backend `VAPI_API_KEY` is valid
   - Check backend logs for proxy errors

4. **No audio:**
   - Check browser permissions for microphone
   - Verify Vapi account has sufficient credits
   - Check browser console for WebRTC errors

## Architecture Diagram

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. Initialize SDK with public key
       │ 2. Start/Stop calls via SDK
       ▼
┌─────────────────────────────────────┐
│     Vapi SDK (@vapi-ai/web)        │
│  - Uses public key                  │
│  - Routes requests through proxy    │
└──────┬──────────────────────────────┘
       │
       │ HTTP requests to proxy
       ▼
┌─────────────────────────────────────┐
│   Backend Proxy (/api/vapi/proxy)  │
│  - Validates authentication         │
│  - Adds API key to requests         │
│  - Forwards to Vapi API             │
└──────┬──────────────────────────────┘
       │
       │ Authenticated requests
       ▼
┌─────────────────────────────────────┐
│      Vapi API (api.vapi.ai)        │
│  - Processes voice calls            │
│  - Manages assistants               │
└─────────────────────────────────────┘
```

## Future Enhancements

- [ ] Add call recording capabilities
- [ ] Implement call analytics and transcripts
- [ ] Add custom voice settings
- [ ] Support for multiple assistants
- [ ] Real-time conversation insights
- [ ] Integration with interview notes

## References

- [Vapi Documentation](https://docs.vapi.ai)
- [Vapi Web SDK](https://github.com/VapiAI/client-sdk-web)
- [Vapi Security Best Practices](https://docs.vapi.ai/security-and-privacy/proxy-server)

