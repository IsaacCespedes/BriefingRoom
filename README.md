# Bionic Interviewer

An AI-powered briefing system for interview hosts that provides interactive briefings about candidates before interviews and real-time assistance during interviews.

## Project Structure

```
BriefingRoom/
├── docs/
│   ├── architecture.md
│   └── diagrams/
├── frontend/          # SvelteKit application
├── backend/           # FastAPI application
└── docker-compose.yml # Docker orchestration (to be created)
```

## Tech Stack

- **Frontend**: SvelteKit, Tailwind CSS, Daily.co Web SDK, Vapi Web SDK
- **Backend**: FastAPI (Python), CrewAI, OpenAI
- **Database**: Supabase (PostgreSQL)
- **Video**: Daily.co
- **Voice AI**: Vapi
- **Orchestration**: Docker Compose

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Supabase account

### Getting Started

1. Clone the repository
2. Set up environment variables (see `.env.example` - to be created)
3. Install dependencies:
   - Backend: `cd backend && pip install -r requirements.txt` (to be created)
   - Frontend: `cd frontend && npm install` (to be created)
4. Run with Docker Compose: `docker-compose up` (to be created)

### JWT Token Maintenance

The local Supabase instance uses JWT tokens for authentication. These tokens are pre-generated and stored in `.env` and `docker-compose.yml`.

**Token Validity:** Current tokens are valid for **1 year** (until December 9, 2026).

**When to regenerate:**
- Tokens expire (check expiration date above)
- You change the `JWT_SECRET` in docker-compose.yml
- Security concerns require token rotation

**How to regenerate:**

```bash
# Generate new tokens
python3 scripts/generate_jwt_tokens.py 'super-secret-jwt-token-with-at-least-32-characters-long'

# Update .env file with the output tokens (SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY)
# Update docker-compose.yml with the same tokens in two places:
#   - studio service (lines ~37-38)
#   - backend service (lines ~136-137)

# Restart containers
docker compose down && docker compose up -d
```

**Note:** The token generation script uses `time.time()` to avoid timezone issues and sets the `iat` (issued at) claim to 5 minutes in the past to prevent clock skew errors.

## Development Phases

See [project-spec.md](./project-spec.md) for the complete development plan.

- ✅ Phase 1: Foundation & Documentation
- ✅ Phase 2: Backend (FastAPI)
- ✅ Phase 3: Frontend (SvelteKit)
- ✅ Phase 4: Docker & Deployment
- ✅ Phase 5: Database (Supabase)

**Note:** The application now uses **Supabase PostgreSQL** for persistent storage of interviews, tokens, and interview notes.

## Documentation

- [Architecture Documentation](./docs/architecture.md)
- [System Architecture Diagram](./docs/diagrams/system-architecture.md)
- [Component Diagram](./docs/diagrams/component-diagram.md)
- [Entity-Relationship Diagram](./docs/diagrams/erd.md)

## License

[To be determined]

