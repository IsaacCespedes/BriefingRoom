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

## Development Phases

See [project-spec.md](./project-spec.md) for the complete development plan.

- ✅ Phase 1: Foundation & Documentation
- ⏳ Phase 2: Backend (FastAPI)
- ⏳ Phase 3: Frontend (SvelteKit)
- ⏳ Phase 4: Docker & Deployment
- ⏳ Phase 5: Database (Supabase)

## Documentation

- [Architecture Documentation](./docs/architecture.md)
- [System Architecture Diagram](./docs/diagrams/system-architecture.md)
- [Component Diagram](./docs/diagrams/component-diagram.md)
- [Entity-Relationship Diagram](./docs/diagrams/erd.md)

## License

[To be determined]

