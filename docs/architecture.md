# System Architecture: Bionic Interviewer

## Overview

The Bionic Interviewer is a monorepo application that provides an AI-powered briefing system for interview hosts. The system enables hosts to receive interactive briefings about candidates before interviews and provides real-time assistance during interviews.

## High-Level Architecture

The system follows a client-server architecture with the following components:

1. **Frontend (SvelteKit)**: Web-based user interface for hosts
2. **Backend (FastAPI)**: RESTful API server handling business logic
3. **Database (Supabase/PostgreSQL)**: Persistent storage for interviews and notes
   - **⚠️ Current Implementation**: Temporary in-memory storage (`backend/app/storage.py`)
   - Data is lost on server restart
   - Will be replaced with Supabase in Phase 5
4. **External Services**:
   - **Daily.co**: Video conferencing infrastructure
   - **Vapi**: Voice AI for interactive briefings
   - **OpenAI**: LLM provider for CrewAI agents

## Data Flow

1. **Briefing Generation Flow**:
   - Host uploads resume and job description
   - Frontend sends data to Backend `/generate-briefing` endpoint
   - Backend uses CrewAI to analyze and generate briefing
   - Briefing is stored in database and returned to frontend
   - Host can interact with briefing via Vapi voice interface

2. **Interview Flow**:
   - Host initiates video call via Daily.co
   - System provides real-time hints and cues during interview
   - Interview notes are captured and stored

## Technology Stack

- **Frontend**: SvelteKit, Tailwind CSS, Daily.co Web SDK, Vapi Web SDK
- **Backend**: FastAPI (Python), CrewAI, OpenAI
- **Database**: Supabase (PostgreSQL)
- **Orchestration**: Docker Compose

## Authentication & Authorization

The system uses a token-based authentication model designed for simplicity within a single organization.

### Token-Based Access Control

1. **Token Generation**: When an interview is created, the backend generates two tokens:
   - **Host Token**: Grants full access to the interview (view briefing, start video call, add notes)
   - **Candidate Token**: Grants limited access (join video call, view interview status)

2. **Token Storage**: Tokens are stored as hashed values for security. Each token is:
   - Associated with a specific interview (`interview_id`)
   - Assigned a role (`host` or `candidate`)
   - Optionally expires after a set duration
   - Can be revoked by setting `is_active = false`
   - **⚠️ Currently**: Stored in-memory (temporary solution, lost on restart)
   - **Future**: Will be stored in Supabase `tokens` table (Phase 5)

3. **Token Validation Flow**:
   - Frontend sends token in request headers or query parameters
   - Backend validates token against storage (checking hash, expiration, active status)
   - Backend extracts `interview_id` and `role` from token record
   - Access control enforced based on role and requested resource
   - **⚠️ Currently**: Validates against in-memory `tokens_store` (temporary)
   - **Future**: Will validate against Supabase database (Phase 5)

4. **Token Distribution**:
   - Host receives host token immediately upon interview creation
   - Candidate token is generated and can be shared via email, link, or manual distribution
   - Tokens can be passed via URL query parameter (`?token=...`) or stored client-side

### Security Considerations

- Tokens are hashed before storage (never store plain tokens)
- Token expiration for time-limited access
- Role-based access control (host vs. candidate)
- Secure API endpoints with input validation
- Environment variable management for secrets
- HTTPS required in production

## Scalability

- Stateless backend design for horizontal scaling
- Database connection pooling via Supabase
- Async/await patterns for non-blocking I/O
- Docker containerization for consistent deployments
