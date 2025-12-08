# Component Diagram

```mermaid
graph LR
    subgraph "Frontend Components"
        Page[Page Components]
        Briefing[Briefing UI]
        Interview[Interview UI]
        VapiOrb[VapiOrb Component]
        DailyCall[Daily Call Component]
    end

    subgraph "Backend Modules"
        Routes[API Routes]
        CrewModule[Crew Module]
        Models[Pydantic Models]
        Services[Service Layer]
    end

    subgraph "Database Layer"
        InterviewsTable[(interviews)]
        NotesTable[(interview_notes)]
    end

    Page --> Briefing
    Page --> Interview
    Briefing --> VapiOrb
    Interview --> DailyCall
    
    Briefing --> Routes
    Interview --> Routes
    
    Routes --> Services
    Routes --> Models
    Services --> CrewModule
    Services --> InterviewsTable
    Services --> NotesTable

    style Page fill:#fff4e1
    style Routes fill:#ffe1f5
    style InterviewsTable fill:#e1ffe1
    style NotesTable fill:#e1ffe1
```

## Frontend Components

- **Page Components**: SvelteKit page components with role-based routing
- **Briefing UI**: Interface for viewing and interacting with candidate briefings
- **Interview UI**: Interface for conducting video interviews
- **VapiOrb Component**: Voice AI interaction component
- **Daily Call Component**: Video call interface component

## Backend Modules

- **API Routes**: FastAPI route handlers organized by feature
- **Crew Module**: CrewAI agent definitions and orchestration
- **Pydantic Models**: Data validation and serialization models
- **Service Layer**: Business logic separated from route handlers

## Database Tables

- **interviews**: Stores interview metadata and context
- **interview_notes**: Stores notes from interviews (from CrewAI or Host)
