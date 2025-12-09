# Project Spec: Bionic Interviewer

This document outlines the project-specific plan for building the "Bionic Interviewer" application.

---

## 1. Project Overview

The "Bionic Interviewer" is a tool that provides a host with an interactive, AI-powered briefing about a candidate before an interview. It uses a combination of AI agents to analyze a candidate's resume, generate a summary, and provide strategic questions. The host can interact with the briefing agent via voice. During the interview, the tool can provide real-time hints and cues.

---

## 2. Tech Stack

-   **Frontend:** SvelteKit, Tailwind CSS, Daily.co Web SDK, Vapi Web SDK
-   **Backend:** FastAPI (Python), CrewAI, OpenAI
-   **Database:** Supabase (PostgreSQL)
-   **Video:** Daily.co
-   **Voice AI:** Vapi
-   **Orchestration:** Docker Compose

---

## 3. System Architecture

See the [Architecture Documentation](./docs/architecture.md) for detailed system design.

-   **System Architecture Diagram:** [docs/diagrams/system-architecture.md](./docs/diagrams/system-architecture.md)
-   **Component Diagram:** [docs/diagrams/component-diagram.md](./docs/diagrams/component-diagram.md)
-   **Entity-Relationship Diagram (ERD):** [docs/diagrams/erd.md](./docs/diagrams/erd.md)

---

## 4. Project Setup

The project will be organized as a monorepo. A `docs/` directory will be created to hold architecture documents and diagrams.

```
/interview-bionic
├── docs/
│   ├── architecture.md
│   └── diagrams/
├── docker-compose.yml
├── .env
│
├── frontend/ (SvelteKit)
│   ├── Dockerfile
│   ├── src/
│
└── backend/ (FastAPI)
    ├── Dockerfile
    ├── app/
    └── tests/
```

---

## 5. Development Plan (Spec-Driven)

### Phase 1: Foundation & Documentation ✅

-   [x] **Task 1: Setup Project Structure.**
    -   Create the monorepo structure with `frontend`, `backend`, and `docs` directories.
-   [x] **Task 2: Initial Documentation.**
    -   Create `docs/architecture.md` to describe the high-level design.
    -   Create initial diagrams (System Architecture, ERD) and place them in `docs/diagrams`.
-   [x] **Task 3: Setup Tooling.**
    -   Initialize `ruff` for the Python backend.
    -   Initialize `prettier` and `svelte-check` for the SvelteKit frontend.
    -   Setup `pytest` and `vitest`.

### Phase 2: Backend (FastAPI) ✅

-   [x] **Task 1: Setup FastAPI.**
    -   Create a new FastAPI project in `backend`.
    -   Write a failing test for a health check endpoint.
    -   Implement the health check endpoint `/health` to pass the test.
-   [x] **Task 2: Database Models & Migrations.**
    -   Define Pydantic models in `backend/app/models/`.
    -   Create Supabase migrations for `interviews` and `interview_notes` tables.
-   [x] **Task 3: CrewAI Logic.**
    -   Write tests for the `create_briefing_crew` function.
    -   Implement the crew logic in `backend/app/crew/` to pass the tests.
-   [x] **Task 4: `/generate-briefing` Endpoint.**
    -   Write integration tests for the `POST /generate-briefing` endpoint.
    -   Implement the endpoint in `backend/app/api/` to pass the tests.

### Phase 3: Frontend (SvelteKit) ✅

-   [x] **Task 1: Setup SvelteKit.**
    -   Create a new SvelteKit project in `frontend`.
    -   Set up TypeScript, Vite, Tailwind CSS, and project structure.
    -   Created routes for host and candidate interfaces.
-   [x] **Task 2: Role-Based Access.**
    -   Write tests for the token validation and role detection logic.
    -   Implement the `+page.server.ts` logic to pass the tests.
    -   Created backend `/api/validate-token` endpoint.
    -   Implemented role-based routing (host/candidate).
-   [x] **Task 3: Vapi Integration.**
    -   Write tests for the briefing functionality.
    -   Implement the `VapiOrb` component and the briefing trigger logic.
    -   Created briefing API functions and integrated into host dashboard.
-   [x] **Task 4: Daily.co Integration.**
    -   Write tests for the video call setup.
    -   Implement the Daily.co integration.
    -   Created `DailyCall` component and room management API functions.

### Phase 4: Docker & Deployment

-   [ ] **Task 1: Dockerize services.**
    -   Create `Dockerfile` for frontend and backend.
-   [ ] **Task 2: Docker Compose.**
    -   Create `docker-compose.yml`.

### Phase 5: Database (Supabase)

**⚠️ Current Status: Temporary In-Memory Storage**

The application currently uses in-memory storage (`backend/app/storage.py`) as a temporary development solution. This means:
- Data (interviews, tokens) is stored in memory and lost on server restart
- This is sufficient for development and testing but not for production
- The code is structured to easily migrate to Supabase when Phase 5 is completed

**Implementation Notes:**
- Token validation (`backend/app/api/auth.py`) uses the in-memory `tokens_store`
- Interview creation (`backend/app/api/interviews.py`) uses the in-memory `interviews_store`
- All storage operations are centralized in `backend/app/storage.py` for easy migration

- [ ] **Task 1: Create tables.**
  - In the Supabase dashboard, create the `interviews`, `interview_notes`, and `tokens` tables with the following schemas:

  **`interviews`**
  - `id` (uuid, primary key)
  - `created_at` (timestamp with time zone)
  - `job_description` (text)
  - `resume_text` (text)
  - `status` (text)

  **`interview_notes`**
  - `id` (uuid, primary key)
  - `interview_id` (uuid, foreign key to `interviews.id`)
  - `created_at` (timestamp with time zone)
  - `note` (text)
  - `source` (text, e.g., "CrewAI", "Host")

  **`tokens`**
  - `id` (uuid, primary key)
  - `interview_id` (uuid, foreign key to `interviews.id`)
  - `token_hash` (text, unique) - hashed version of the token
  - `role` (text, check constraint: 'host' or 'candidate')
  - `created_at` (timestamp with time zone)
  - `expires_at` (timestamp with time zone, nullable)
  - `is_active` (boolean, default true)
