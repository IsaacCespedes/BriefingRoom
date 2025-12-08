# System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
    end

    subgraph "Frontend (SvelteKit)"
        UI[User Interface]
        VapiOrb[Vapi Orb Component]
        DailySDK[Daily.co SDK]
    end

    subgraph "Backend (FastAPI)"
        API[API Routes]
        CrewAI[CrewAI Orchestration]
        Services[Business Logic Services]
    end

    subgraph "Database (Supabase)"
        DB[(PostgreSQL)]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        Daily[Daily.co Service]
        Vapi[Vapi Service]
    end

    Browser --> UI
    UI --> VapiOrb
    UI --> DailySDK
    UI --> API
    
    VapiOrb --> Vapi
    DailySDK --> Daily
    
    API --> Services
    API --> CrewAI
    Services --> DB
    CrewAI --> OpenAI
    CrewAI --> DB

    style Browser fill:#e1f5ff
    style UI fill:#fff4e1
    style API fill:#ffe1f5
    style DB fill:#e1ffe1
    style OpenAI fill:#f5e1ff
    style Daily fill:#f5e1ff
    style Vapi fill:#f5e1ff
```

## Component Descriptions

- **Web Browser**: User's browser accessing the application
- **User Interface**: SvelteKit frontend with Tailwind CSS
- **Vapi Orb Component**: Voice AI interface component
- **Daily.co SDK**: Video conferencing integration
- **API Routes**: FastAPI REST endpoints
- **CrewAI Orchestration**: AI agent coordination for briefing generation
- **Business Logic Services**: Core application logic
- **PostgreSQL**: Supabase database for persistent storage
- **OpenAI API**: LLM provider for CrewAI agents
- **Daily.co Service**: Video conferencing infrastructure
- **Vapi Service**: Voice AI service
