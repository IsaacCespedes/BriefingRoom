# CrewAI Agent Expansion Plan

## Executive Summary

This document outlines a comprehensive plan to expand the current CrewAI briefing system from a simple 2-agent sequential workflow to a robust 7-agent quality-assured architecture with **parallel processing**, **quality validation**, **cross-referencing capabilities**, **automatic trigger on interview creation**, and **real-time progress tracking**.

### Key Updates (Latest Revision)

#### ✅ Automatic Briefing Generation
- Briefing generation now triggers **automatically** when an interview is created
- No manual button press required
- Interview creation endpoint returns immediately (non-blocking)
- Briefing generation runs as a background task

#### ✅ Real-Time Progress Updates
- UI displays **live progress updates** as briefing generates
- Each agent step (start/complete) updates the UI in real-time
- Progress percentage, current agent, and status message shown to user
- Implemented via **Server-Sent Events (SSE)** with polling fallback

#### ✅ CrewAI Event System Confirmed
After consulting official CrewAI documentation, we have **confirmed** that CrewAI supports:
- ✅ **Task-level callbacks** - Functions triggered when tasks start/complete
- ✅ **Step-level callbacks** - Monitor individual agent steps
- ✅ **Custom Event Listeners** - `BaseEventListener` for granular event handling
- ✅ **Real-time status tracking** - Can update database at each step

This means **real-time status updates are fully possible** and supported by the framework.

#### 🗄️ New Database Table: `briefing_status`
Tracks briefing generation progress with:
- Current status (e.g., `processing_resume_analyzer`, `completed`)
- Progress percentage (0-100)
- Status message (e.g., "Analyzing resume quality...")
- Current agent name
- Timestamps for tracking

#### 🔌 New API Endpoints
- `GET /api/briefing/status/{interview_id}` - Poll for current status
- `GET /api/briefing/status/{interview_id}/stream` - SSE stream for real-time updates
- `POST /api/interviews` - Modified to trigger async briefing generation
- `POST /api/briefing/generate/{interview_id}` - Retry briefing generation (for failed attempts)

#### 🎨 New UI Components
- Progress status component (Svelte) - replaces "Generate Brief" button in host view
- SSE/polling integration for real-time updates
- Simple text label with percentage (e.g., "Reviewing resume (14%)")
- Error display with retry button
- No progress bar - just concise text labels

#### 📋 New Implementation Phase
**Phase 0: Real-Time Status Infrastructure** added before existing phases to establish the async + real-time tracking foundation.

---

### New User Flow with Real-Time Updates

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Interview Creation                                     │
│  ───────────────────────────────────────────────────────────    │
│  1. User submits job description + resume                       │
│     ↓                                                            │
│  2. POST /api/interviews                                         │
│     • Creates interview record in database                       │
│     • Generates host/candidate tokens                            │
│     • Creates initial briefing_status (status: "initializing")  │
│     • Triggers async background task for briefing generation     │
│     • Returns immediately with interview_id                      │
│     ↓                                                            │
│  3. UI receives interview_id + tokens                            │
│     • Shows success page with host/candidate links               │
│     • NO progress indicator on this page                         │
│     • User can immediately click host link                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  STEP 2: Host Accesses Interview Room                           │
│  ───────────────────────────────────────────────────────────    │
│  4. Host clicks host link → Opens interview room                │
│     ↓                                                            │
│  5. Host page loads, checks briefing status                      │
│     • GET /api/briefing/status/{interview_id}                   │
│     • Connects to SSE stream for real-time updates               │
│     ↓                                                            │
│  6. Briefing section displays current status:                    │
│     • If generating: "⏳ Reviewing resume (14%)"                │
│     • If complete: Shows full briefing content                   │
│     • If failed: Shows error + retry button                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  STEP 3: Background Processing (Async)                          │
│  ───────────────────────────────────────────────────────────    │
│  7. Background: CrewAI Crew executes                             │
│     ┌──────────────────────────────────────────────────┐        │
│     │  Custom Event Listener monitors each task:       │        │
│     │  • TaskStartedEvent → Update DB with status      │        │
│     │  • TaskCompletedEvent → Update DB with progress  │        │
│     └──────────────────────────────────────────────────┘        │
│     ↓                                                            │
│  8. Host UI receives real-time updates via SSE:                  │
│     • "Reviewing resume (0%)"                                    │
│     • "Reviewing resume (14%)"                                   │
│     • "Checking resume analysis (14%)"                           │
│     • "Checking resume analysis (29%)"                           │
│     • "Reviewing job description (29%)"                          │
│     • ... (continues for all 7 agents)                           │
│     • "Creating briefing (86%)"                                  │
│     • "Briefing ready (100%)"                                    │
│     ↓                                                            │
│  9. Final status: "completed" (100%)                             │
│     • Status label replaced with full briefing content           │
│     • Host can now review and use briefing for interview         │
└─────────────────────────────────────────────────────────────────┘
```

### Old vs New Comparison

| Aspect | **Old (Current)** | **New (Proposed)** |
|--------|-------------------|-------------------|
| **Trigger** | Manual "Generate Brief" button in host view | Automatic on interview creation |
| **Execution** | Synchronous (blocking) | Asynchronous (background task) |
| **User waits** | Yes, until complete (~30-60s) | No, returns immediately |
| **Progress visibility** | None (black box) | Real-time updates in host view |
| **UI feedback** | Loading spinner only | Simple text label with percentage |
| **Progress location** | On button | In host interview room (replaces button) |
| **Status tracking** | None | Database-backed with full audit trail |
| **Error handling** | Generic error message | Error message + "Retry" button |
| **Concurrency** | Blocks other requests | Multiple briefings can generate simultaneously |
| **Host access** | Must wait for briefing | Can access room while generating |

---

## Current State Analysis

### Existing Architecture
- **Agents**: 2 (Resume Analyst, Briefing Generator)
- **Tasks**: 2 (Analyze Resume, Generate Briefing)
- **Process**: Sequential
- **Quality Assurance**: None
- **Trigger**: Manual (via `/generate-briefing` API endpoint)
- **Status Updates**: None (synchronous blocking operation)
- **Weaknesses**:
  - No validation of analysis quality
  - Single-pass processing without verification
  - Job description and resume analyzed together (not specialized)
  - No cross-validation between job requirements and candidate qualifications
  - No mechanisms to catch errors or incomplete analysis
  - No real-time progress visibility for users
  - Blocking synchronous operation prevents UI responsiveness

## Proposed Architecture

### Agent Hierarchy Overview

```
                    ┌─────────────────────────────────┐
                    │    Final Briefing Synthesizer   │
                    │         (Agent 7)               │
                    └──────────────▲──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
          ┌─────────┴────────┐         ┌─────────┴────────┐
          │  Resume Analysis │         │ Job Description  │
          │     Branch       │         │    Branch        │
          └──────────────────┘         └──────────────────┘
                    │                             │
          ┌─────────┴────────┐         ┌─────────┴────────┐
          │                  │         │                  │
    ┌─────▼─────┐     ┌─────▼─────┐   │   ┌─────▼─────┐  │  ┌─────▼─────┐
    │  Resume   │────▶│  Resume   │   │   │    Job    │──│─▶│    Job    │
    │ Analyzer  │     │  Quality  │   │   │Description│  │  │Description│
    │(Agent 1)  │     │  Checker  │   │   │ Analyzer  │  │  │  Quality  │
    └───────────┘     │(Agent 2)  │   │   │(Agent 3)  │  │  │  Checker  │
                      └───────────┘   │   └───────────┘  │  │(Agent 4)  │
                                      │                  │  └───────────┘
                                      └──────────────────┘
```

### Agent Definitions

#### Branch 1: Resume Analysis Pipeline

**Agent 1: Resume Analyzer**
- **Role**: Specialized Resume Analyst
- **Goal**: Extract comprehensive information from candidate resumes with focus on skills, experience, achievements, and red flags
- **Responsibilities**:
  - Parse resume structure and content into **4 required sections** (Skills, Experience, Education, Red Flags)
  - Extract technical skills, soft skills, and domain expertise
  - Analyze work experience chronology and progression
  - Identify education, certifications, and credentials
  - Flag gaps in employment or potential concerns
  - Note unique qualifications or standout achievements
- **Output Format**: **Structured JSON with explicit schema** (see Task 1 for full schema)
- **Quality Metrics**: Completeness, accuracy of extraction, proper categorization
- **Structured Output Approach**: Agent is instructed to output ONLY valid JSON matching the exact schema, no additional text. This ensures downstream agents receive consistent, parseable data.

**Agent 2: Resume Quality Checker**
- **Role**: Resume Analysis Quality Assurance Specialist
- **Goal**: Validate the completeness and accuracy of resume analysis
- **Responsibilities**:
  - Verify all resume sections were analyzed
  - Check for missing or overlooked information
  - Validate skill categorizations (technical vs soft skills)
  - Ensure experience timeline makes sense
  - Confirm red flags are legitimate concerns
  - Request re-analysis if quality thresholds not met
- **Input**: Agent 1's analysis + original resume text
- **Output Format**: Validation report + approved/revised analysis
- **Quality Gates**:
  - All major resume sections covered (✓ Skills, ✓ Experience, ✓ Education)
  - At least 80% of technical terms properly identified
  - Chronological inconsistencies flagged
  - Pass/Fail decision with specific feedback

#### Branch 2: Job Description Analysis Pipeline

**Agent 3: Job Description Analyzer**
- **Role**: Specialized Job Requirements Analyst
- **Goal**: Extract and structure all requirements, responsibilities, and evaluation criteria from job descriptions
- **Responsibilities**:
  - Parse job requirements into **7 required sections** (Required Skills, Preferred Skills, Technical Requirements, Soft Skills & Culture, Experience Level, Responsibilities, Role Context)
  - Clearly distinguish must-have vs nice-to-have requirements
  - Extract technical requirements and skill expectations
  - Identify soft skill requirements and cultural fit indicators
  - Note experience level expectations
  - Extract key responsibilities and scope of role
  - Identify growth opportunities and career progression signals
- **Output Format**: **Structured JSON with explicit schema** (see Task 3 for full schema)
- **Quality Metrics**: Requirement completeness, proper prioritization, clarity
- **Structured Output Approach**: Agent is instructed to output ONLY valid JSON matching the exact schema, no additional text. This ensures clear separation of required vs preferred qualifications.

**Agent 4: Job Description Quality Checker**
- **Role**: Job Requirements Quality Assurance Specialist
- **Goal**: Validate the completeness and accuracy of job description analysis
- **Responsibilities**:
  - Verify all requirement types extracted (technical, experience, education, soft skills)
  - Confirm must-have vs nice-to-have categorization is accurate
  - Ensure no critical requirements were missed
  - Validate that experience level expectations are clear
  - Check that role scope and responsibilities are comprehensive
  - Request re-analysis if quality thresholds not met
- **Input**: Agent 3's analysis + original job description
- **Output Format**: Validation report + approved/revised analysis
- **Quality Gates**:
  - All requirement categories identified
  - Clear distinction between required and preferred qualifications
  - Technical requirements properly categorized
  - Pass/Fail decision with specific feedback

#### Final Synthesis Stage

**Agent 5: Cross-Reference Matcher**
- **Role**: Candidate-Role Alignment Specialist
- **Goal**: Perform detailed cross-referencing between validated resume and job analyses
- **Responsibilities**:
  - Match candidate skills against job requirements
  - Calculate fit scores for each requirement category
  - Identify strong alignment areas
  - Flag gaps or misalignments
  - Note areas requiring clarification in interview
  - Assess experience level match
  - Evaluate potential for growth into the role
- **Input**: Validated outputs from Agents 2 and 4
- **Output Format**: Alignment matrix with scoring and gap analysis
- **Quality Metrics**: Accuracy of matching, thoroughness of gap identification

**Agent 6: Strategic Question Generator**
- **Role**: Interview Strategy Specialist
- **Goal**: Generate targeted, strategic interview questions based on cross-reference analysis
- **Responsibilities**:
  - Create questions to probe skill gaps
  - Design questions to verify claimed experience
  - Generate behavioral questions for soft skill assessment
  - Formulate scenario-based questions for technical evaluation
  - Prioritize questions by importance and risk
  - Include questions to explore growth potential
  - Design questions to clarify resume ambiguities
- **Input**: Output from Agent 5
- **Output Format**: Prioritized question bank with rationales
- **Question Categories**:
  - Gap Exploration (address missing qualifications)
  - Verification (validate resume claims)
  - Depth Assessment (probe technical expertise)
  - Behavioral (evaluate soft skills and culture fit)
  - Growth Potential (assess learning ability)

**Agent 7: Final Briefing Synthesizer**
- **Role**: Master Briefing Compiler
- **Goal**: Synthesize all validated analyses into a comprehensive, actionable interview briefing
- **Responsibilities**:
  - Compile executive summary of candidate-role fit
  - Present resume highlights relevant to role
  - Summarize job requirements and priorities
  - Include alignment scores and gap analysis
  - Integrate strategic question recommendations
  - Provide interview strategy and focus areas
  - Flag critical evaluation points
  - Format briefing for easy consumption by interviewer
- **Input**: Outputs from Agents 2, 4, 5, and 6
- **Output Format**: Formatted interview briefing document (markdown/HTML)
- **Structure**:
  1. Executive Summary (fit score, key takeaways)
  2. Candidate Profile (validated resume analysis)
  3. Role Requirements (validated job analysis)
  4. Alignment Analysis (match matrix, gaps)
  5. Strategic Questions (prioritized question bank)
  6. Interview Strategy (focus areas, red flags to probe)
  7. Decision Criteria (evaluation framework)

### Process Flow Architecture

#### Parallel Processing Strategy

```
Stage 1: Parallel Analysis (Agents 1 & 3 run simultaneously)
    ├─ Resume Analyzer (Agent 1)
    └─ Job Description Analyzer (Agent 3)

Stage 2: Parallel Quality Checks (Agents 2 & 4 run simultaneously)
    ├─ Resume Quality Checker (Agent 2) ← validates Agent 1
    └─ Job Description Quality Checker (Agent 4) ← validates Agent 3

Stage 3: Sequential Synthesis
    ├─ Cross-Reference Matcher (Agent 5) ← uses outputs from Agents 2 & 4
    ├─ Strategic Question Generator (Agent 6) ← uses output from Agent 5
    └─ Final Briefing Synthesizer (Agent 7) ← uses all prior outputs
```

#### Quality Gate Thresholds

**Resume Analysis Quality Gates**:
- All major sections identified: Yes/No
- Skills extraction completeness: ≥ 80%
- Experience timeline validated: Yes/No
- Education/credentials extracted: Yes/No

**Job Description Quality Gates**:
- Requirements categorization: Must-have/Nice-to-have
- Technical requirements identified: ≥ 90%
- Soft skills identified: Yes/No
- Experience level clarified: Yes/No

**Cross-Reference Quality Gates**:
- All job requirements addressed: 100%
- Gap analysis completed: Yes/No
- Alignment scores calculated: Yes/No
- Strategic focus areas identified: ≥ 3

### Task Definitions

#### Task 1: Analyze Resume
- **Agent**: Agent 1 (Resume Analyzer)
- **Description**: "Thoroughly analyze the candidate's resume. Extract and categorize all information into the following REQUIRED sections:
  1. **SKILLS**: Extract technical skills, soft skills, tools, programming languages, frameworks, certifications
  2. **EXPERIENCE**: Analyze work history chronologically with company names, dates, titles, responsibilities, and achievements
  3. **EDUCATION**: Extract degrees, institutions, graduation dates, relevant coursework, academic achievements
  4. **RED FLAGS**: Identify employment gaps, inconsistencies, concerns, or areas requiring clarification

  Pay special attention to career progression, skill development trajectory, and quantifiable achievements. Output MUST be valid JSON format only, no additional text."
- **Expected Output**: "A structured JSON object with this exact schema:
```json
{
  "skills": {
    "technical": ["skill1", "skill2"],
    "soft_skills": ["skill1", "skill2"],
    "tools_and_technologies": ["tool1", "tool2"],
    "certifications": ["cert1", "cert2"]
  },
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "dates": "Jan 2020 - Present",
      "duration_years": 3.5,
      "responsibilities": ["resp1", "resp2"],
      "achievements": ["achievement1 with quantifiable results"],
      "technologies_used": ["tech1", "tech2"]
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Bachelor of Science in Computer Science",
      "graduation_date": "2018",
      "gpa": "3.8/4.0",
      "relevant_coursework": ["course1", "course2"]
    }
  ],
  "red_flags": [
    {
      "type": "employment_gap",
      "description": "6-month gap between jobs",
      "severity": "medium"
    }
  ],
  "summary": "Brief narrative of candidate's career progression and standout qualities"
}
```"

#### Task 2: Validate Resume Analysis
- **Agent**: Agent 2 (Resume Quality Checker)
- **Description**: "Review the resume analysis from Agent 1 against the original resume text. Verify completeness, accuracy, and proper categorization. Check for: missing sections, uncategorized skills, chronological inconsistencies, unaddressed red flags, and ambiguous interpretations. If quality gates are not met (completeness < 80%, major sections missing), flag for re-analysis and provide specific feedback."
- **Expected Output**: "A validation report containing: quality_score (0-100), missing_elements (list), accuracy_issues (list), pass/fail status, and if passed, the approved/revised analysis structure."
- **Context Dependencies**: Requires Task 1 output + original resume text

#### Task 3: Analyze Job Description
- **Agent**: Agent 3 (Job Description Analyzer)
- **Description**: "Thoroughly analyze the job description. Extract and categorize all information into the following REQUIRED sections:
  1. **REQUIRED SKILLS** (must-have): Technical and soft skills that are mandatory
  2. **PREFERRED SKILLS** (nice-to-have): Skills that are desired but not mandatory
  3. **TECHNICAL REQUIREMENTS**: Specific technologies, tools, languages, frameworks
  4. **SOFT SKILLS & CULTURE**: Behavioral requirements, values, team fit, communication style
  5. **EXPERIENCE LEVEL**: Years of experience, seniority expectations, leadership requirements
  6. **RESPONSIBILITIES**: Day-to-day duties, project scope, key deliverables
  7. **ROLE CONTEXT**: Growth opportunities, challenges, team structure, scope

  Ensure clear distinction between required and preferred qualifications. Output MUST be valid JSON format only, no additional text."
- **Expected Output**: "A structured JSON object with this exact schema:
```json
{
  "required_skills": {
    "technical": ["Python", "API design", "SQL"],
    "soft_skills": ["communication", "problem-solving"],
    "experience": ["5+ years backend development", "Led engineering teams"]
  },
  "preferred_skills": {
    "technical": ["Kubernetes", "GraphQL"],
    "soft_skills": ["mentoring", "public speaking"],
    "experience": ["Startup experience", "Open source contributions"]
  },
  "technical_requirements": {
    "languages": ["Python", "JavaScript"],
    "frameworks": ["Django", "FastAPI"],
    "tools": ["Docker", "CI/CD"],
    "platforms": ["AWS", "GCP"]
  },
  "soft_skills_and_culture": {
    "values": ["collaboration", "innovation", "ownership"],
    "working_style": "Agile, remote-first, async communication",
    "team_dynamics": "Cross-functional, collaborative"
  },
  "experience_level": {
    "years_required": "5-7 years",
    "seniority": "Senior",
    "leadership_required": true,
    "team_size_managed": "3-5 engineers"
  },
  "responsibilities": [
    "Design and implement scalable backend services",
    "Mentor junior engineers",
    "Collaborate with product team on roadmap"
  ],
  "role_context": {
    "scope": "Full ownership of backend infrastructure",
    "growth_opportunities": ["Path to Staff Engineer", "Technical leadership"],
    "challenges": ["Scaling to 10M users", "Microservices migration"],
    "team_structure": "Engineering team of 15, reporting to VP Engineering"
  }
}
```"

#### Task 4: Validate Job Description Analysis
- **Agent**: Agent 4 (Job Description Quality Checker)
- **Description**: "Review the job description analysis from Agent 3 against the original job description. Verify completeness, accurate requirement prioritization, and clear categorization. Check for: missed requirements, incorrect must-have/nice-to-have classifications, ambiguous technical requirements, and unclear experience expectations. If quality gates are not met (technical requirements < 90%, unclear prioritization), flag for re-analysis."
- **Expected Output**: "A validation report containing: quality_score (0-100), missing_requirements (list), categorization_issues (list), pass/fail status, and if passed, the approved/revised analysis structure."
- **Context Dependencies**: Requires Task 3 output + original job description

#### Task 5: Cross-Reference and Match
- **Agent**: Agent 5 (Cross-Reference Matcher)
- **Description**: "Perform detailed cross-referencing between the validated resume analysis (from Agent 2) and validated job description analysis (from Agent 4). For each job requirement:
  1. Determine match status: MEETS, PARTIALLY_MEETS, or DOES_NOT_MEET
  2. Calculate alignment scores by category (0-100 scale)
  3. Identify strong matches with supporting evidence from resume
  4. Flag gaps with severity level (low, medium, high, critical)
  5. Note areas requiring interview clarification

  Be thorough and evidence-based. Output MUST be valid JSON format only, no additional text."
- **Expected Output**: "A structured JSON object with this exact schema:
```json
{
  "overall_fit_score": 78,
  "category_scores": {
    "technical_skills": 85,
    "experience_level": 70,
    "soft_skills": 80,
    "education": 90,
    "leadership": 75
  },
  "strong_matches": [
    {
      "requirement": "5+ years Python experience",
      "status": "MEETS",
      "evidence": "7 years Python across 3 companies, led Python migration at TechCorp"
    }
  ],
  "gaps": [
    {
      "requirement": "Kubernetes experience",
      "status": "DOES_NOT_MEET",
      "severity": "medium",
      "impact": "May need training for infrastructure management",
      "interview_focus": "Assess willingness to learn and related containerization experience"
    }
  ],
  "partial_matches": [
    {
      "requirement": "Team leadership experience",
      "status": "PARTIALLY_MEETS",
      "evidence": "Led team of 3 engineers for 1 year (requirement asks for 5+ team)",
      "gap": "Smaller team size than required"
    }
  ],
  "clarification_needed": [
    "Resume mentions 'microservices' but no details on scale or architecture decisions",
    "Gap between jobs (Jan-June 2020) - reason unclear"
  ],
  "growth_potential": {
    "assessment": "High - strong technical foundation, demonstrated learning ability",
    "evidence": ["Self-taught 3 new frameworks in past 2 years", "Promoted twice in 3 years"],
    "areas_for_growth": ["Scaling infrastructure", "Larger team management"]
  }
}
```"
- **Context Dependencies**: Requires Task 2 and Task 4 outputs

#### Task 6: Generate Strategic Questions
- **Agent**: Agent 6 (Strategic Question Generator)
- **Description**: "Based on the alignment analysis from Agent 5, generate strategic interview questions organized by priority:
  1. **CRITICAL QUESTIONS**: Address major gaps, verify essential requirements, probe red flags
  2. **IMPORTANT QUESTIONS**: Assess depth of claimed skills, behavioral/soft skills evaluation
  3. **OPTIONAL QUESTIONS**: Culture fit, growth potential, nice-to-have skills

  Each question must include:
  - Clear, open-ended question text
  - Category (technical, behavioral, scenario-based, clarification)
  - Rationale explaining why this question matters
  - Suggested follow-up questions
  - What to listen for in the answer

  Output MUST be valid JSON format only, no additional text."
- **Expected Output**: "A structured JSON object with this exact schema:
```json
{
  "critical_questions": [
    {
      "question": "You mentioned microservices experience, but the resume lacks details. Can you walk me through the largest microservices architecture you've designed? What were the challenges and how did you address them?",
      "category": "technical_depth",
      "rationale": "Job requires microservices expertise; resume claims it but lacks evidence",
      "what_to_listen_for": ["Specific technical decisions", "Scale (number of services, requests/sec)", "Challenges like data consistency, service discovery"],
      "follow_ups": [
        "How did you handle inter-service communication?",
        "What was your approach to monitoring and debugging distributed systems?"
      ],
      "relates_to_gap": "Microservices architecture details unclear"
    }
  ],
  "important_questions": [
    {
      "question": "Tell me about a time you had to mentor a struggling junior engineer. What was your approach and what was the outcome?",
      "category": "behavioral_leadership",
      "rationale": "Role requires mentoring 3-5 engineers; need to assess mentoring style and effectiveness",
      "what_to_listen_for": ["Empathy and patience", "Structured approach", "Measurable improvement in mentee"],
      "follow_ups": [
        "How do you balance mentoring with your own deliverables?",
        "How do you tailor your mentoring style to different personalities?"
      ],
      "relates_to_requirement": "Team leadership and mentoring"
    }
  ],
  "optional_questions": [
    {
      "question": "Our team works in a remote-first, async environment. How do you approach collaboration in distributed teams?",
      "category": "culture_fit",
      "rationale": "Assessing alignment with company's working style",
      "what_to_listen_for": ["Communication preferences", "Experience with async tools", "Self-motivation"],
      "follow_ups": ["What's been your biggest challenge in remote work?"],
      "relates_to_requirement": "Remote-first culture"
    }
  ],
  "question_summary": {
    "total_questions": 15,
    "critical_count": 5,
    "important_count": 7,
    "optional_count": 3,
    "estimated_time_minutes": 45
  }
}
```"
- **Context Dependencies**: Requires Task 5 output

#### Task 7: Synthesize Final Briefing
- **Agent**: Agent 7 (Final Briefing Synthesizer)
- **Description**: "Compile all validated analyses and strategic recommendations into a comprehensive, well-formatted interview briefing. Structure the briefing for easy consumption: executive summary with key takeaways, candidate profile, role requirements, alignment analysis with visual scoring, strategic question bank, interview strategy with focus areas and red flags, and decision framework. Ensure the briefing is actionable and enables the interviewer to conduct an effective, targeted interview."
- **Expected Output**: "A complete interview briefing document in markdown format, structured with: Executive Summary, Candidate Profile, Role Requirements, Alignment Analysis, Strategic Questions (prioritized), Interview Strategy, Decision Criteria. The briefing should be 3-5 pages when rendered and include clear sections, bullet points, and emphasis on critical elements."
- **Context Dependencies**: Requires outputs from Tasks 2, 4, 5, and 6

### Real-Time Progress Tracking Architecture

#### Status Update Mechanism

The expanded system will provide **real-time progress updates** to the UI during briefing generation. This is critical for user experience since the 7-agent workflow will take significantly longer than the current 2-agent system.

**CrewAI Event System Support**: ✅ **CONFIRMED**

CrewAI supports comprehensive event tracking through:
1. **Task-level callbacks**: Each task can have a `callback` function that executes upon completion
2. **Step-level callbacks**: The `Crew` object supports `step_callback` for monitoring each agent step
3. **Custom Event Listeners**: `BaseEventListener` class allows listening to granular events including:
   - Task start/completion events
   - Agent step events
   - LLM stream chunk events
   - Custom crew events

**Recommended Approach**: Custom Event Listener with Database Updates

```python
from crewai.events import BaseEventListener
from app.database import update_briefing_status

class BriefingProgressListener(BaseEventListener):
    def __init__(self, interview_id: str):
        self.interview_id = interview_id
        super().__init__()

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            # Update database with current task status
            update_briefing_status(
                self.interview_id,
                status=f"processing_{event.task.agent.role.lower().replace(' ', '_')}",
                message=f"Starting: {event.task.description[:100]}..."
            )

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            # Update database when task completes
            update_briefing_status(
                self.interview_id,
                status=f"completed_{event.task.agent.role.lower().replace(' ', '_')}",
                message=f"Completed: {event.task.agent.role}"
            )
```

#### Database Schema Changes

**New Table: `briefing_status`**

```sql
CREATE TABLE briefing_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    message TEXT,
    stage TEXT,
    progress_percentage INTEGER CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    current_agent TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_briefing_status_interview ON briefing_status(interview_id);
CREATE INDEX idx_briefing_status_updated ON briefing_status(updated_at DESC);
```

**Status Values & User-Facing Messages**:

| Status (Database) | Message (UI Display) | Progress % |
|-------------------|---------------------|------------|
| `initializing` | "Starting..." | 0% |
| `processing_resume_analyzer` | "Reviewing resume" | 0% |
| `completed_resume_analyzer` | "Reviewing resume" | 14% |
| `processing_resume_quality_checker` | "Checking resume analysis" | 14% |
| `completed_resume_quality_checker` | "Checking resume analysis" | 29% |
| `processing_job_description_analyzer` | "Reviewing job description" | 29% |
| `completed_job_description_analyzer` | "Reviewing job description" | 43% |
| `processing_job_description_quality_checker` | "Checking job analysis" | 43% |
| `completed_job_description_quality_checker` | "Checking job analysis" | 57% |
| `processing_cross_reference_matcher` | "Matching requirements" | 57% |
| `completed_cross_reference_matcher` | "Matching requirements" | 71% |
| `processing_strategic_question_generator` | "Generating questions" | 71% |
| `completed_strategic_question_generator` | "Generating questions" | 86% |
| `processing_final_briefing_synthesizer` | "Creating briefing" | 86% |
| `completed_final_briefing_synthesizer` | "Creating briefing" | 100% |
| `completed` | "Briefing ready" | 100% |
| `failed` | "Failed to generate" | - |

**Notes**:
- Status messages are concise (≤5 words) as specified
- Progress percentage updates at task completion
- UI displays: `{message} ({progress}%)` e.g., "Reviewing resume (14%)"

**Progress Percentage Calculation**:
- Total tasks: 7
- Each task completion: +14.3% (100/7)
- Finer granularity: Track task start (e.g., Agent 1 start = 0%, Agent 1 complete = 14.3%)

#### Frontend Status Polling/SSE

**Option 1: Server-Sent Events (SSE)** - Recommended

```typescript
// In SvelteKit load function or client-side
function subscribeToBriefingStatus(interviewId: string) {
    const eventSource = new EventSource(`/api/briefing/status/${interviewId}/stream`);

    eventSource.onmessage = (event) => {
        const statusUpdate = JSON.parse(event.data);
        // Update UI with: statusUpdate.status, statusUpdate.message, statusUpdate.progress_percentage
    };

    eventSource.onerror = () => {
        eventSource.close();
    };

    return eventSource;
}
```

**Option 2: Polling** - Simpler fallback

```typescript
async function pollBriefingStatus(interviewId: string) {
    const interval = setInterval(async () => {
        const response = await fetch(`/api/briefing/status/${interviewId}`);
        const status = await response.json();

        if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
        }

        // Update UI with status
    }, 1000); // Poll every second
}
```

**Recommended**: Use **SSE** for real-time updates with **polling** as a fallback for browsers that don't support SSE.

#### API Endpoint Changes

**New Endpoint: `GET /api/briefing/status/{interview_id}`**

```python
@router.get("/status/{interview_id}")
async def get_briefing_status(interview_id: UUID):
    """Get current status of briefing generation."""
    status = await get_latest_briefing_status(interview_id)
    return {
        "interview_id": interview_id,
        "status": status.status,
        "message": status.message,
        "progress_percentage": status.progress_percentage,
        "current_agent": status.current_agent,
        "updated_at": status.updated_at
    }
```

**New Endpoint: `GET /api/briefing/status/{interview_id}/stream` (SSE)**

```python
from fastapi.responses import StreamingResponse

@router.get("/status/{interview_id}/stream")
async def stream_briefing_status(interview_id: UUID):
    """Stream briefing status updates via SSE."""
    async def event_generator():
        last_update = None
        while True:
            status = await get_latest_briefing_status(interview_id)

            if status.updated_at != last_update:
                yield f"data: {json.dumps(status.dict())}\n\n"
                last_update = status.updated_at

            if status.status in ['completed', 'failed']:
                break

            await asyncio.sleep(0.5)  # Poll database every 500ms

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Modified Endpoint: `POST /api/interviews`**

The interview creation endpoint will now:
1. Create the interview record immediately
2. Return the interview ID
3. **Trigger briefing generation asynchronously** (background task)
4. Client can then connect to status stream

```python
from fastapi import BackgroundTasks

@router.post("/interviews")
async def create_interview(
    request: InterviewCreate,
    background_tasks: BackgroundTasks
):
    """Create interview and trigger async briefing generation."""
    # 1. Create interview record
    interview = await db.create_interview(request)

    # 2. Create initial briefing status
    await db.create_briefing_status(
        interview_id=interview.id,
        status="initializing",
        message="Starting...",
        progress_percentage=0
    )

    # 3. Trigger async briefing generation
    background_tasks.add_task(
        generate_briefing_async,
        interview_id=interview.id,
        job_description=request.job_description,
        resume_text=request.resume_text
    )

    # 4. Return immediately
    return {
        "interview_id": interview.id,
        "host_token": interview.host_token,
        "candidate_token": interview.candidate_token,
        "status": "initializing"
    }
```

**New Endpoint: `POST /api/briefing/generate/{interview_id}` (Retry)**

```python
@router.post("/generate/{interview_id}")
async def retry_briefing_generation(
    interview_id: UUID,
    background_tasks: BackgroundTasks
):
    """Retry briefing generation for a failed attempt."""
    # 1. Get interview details
    interview = await db.get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # 2. Reset briefing status
    await db.create_briefing_status(
        interview_id=interview_id,
        status="initializing",
        message="Retrying...",
        progress_percentage=0
    )

    # 3. Trigger async briefing generation
    background_tasks.add_task(
        generate_briefing_async,
        interview_id=interview_id,
        job_description=interview.job_description,
        resume_text=interview.resume_text
    )

    return {
        "interview_id": interview_id,
        "status": "initializing",
        "message": "Retry initiated"
    }
```

#### UI Changes

**Interview Creation Flow**:

1. User submits job description + resume
2. API creates interview and returns immediately with `interview_id`
3. UI shows success page with host/candidate links
4. Briefing generation starts automatically in background
5. No visible progress indicator on creation page

**Host Interview Room Flow**:

1. Host clicks host link to access interview room
2. **On page load**, check briefing status via API
3. **Replace "Generate Brief" button** with status label based on state:
   - **Generating**: Show progress label (e.g., "Reviewing resume (14%)")
   - **Completed**: Show full briefing (button hidden)
   - **Failed**: Show error message + "Retry Briefing Generation" button
4. **Real-time updates** via SSE/polling while briefing generates
5. When generation completes, automatically display full briefing

**Status Display States**:

```
State 1: Briefing Generating
┌─────────────────────────────────────┐
│  Briefing Section                   │
│  ⏳ Reviewing resume (14%)          │
└─────────────────────────────────────┘

State 2: Briefing Complete
┌─────────────────────────────────────┐
│  Briefing Section                   │
│  [Full briefing content displayed]  │
└─────────────────────────────────────┘

State 3: Briefing Failed
┌─────────────────────────────────────┐
│  Briefing Section                   │
│  ❌ Failed to generate briefing     │
│  [Retry Briefing Generation] button │
└─────────────────────────────────────┘
```

**Progress Status Component (Svelte)**:

This component replaces the "Generate Brief" button in the host view:

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  export let interviewId: string;

  let status = 'initializing';
  let message = '';
  let progress = 0;
  let eventSource: EventSource | null = null;

  onMount(() => {
    // Check initial status
    checkStatus();

    // Connect to SSE stream for real-time updates
    eventSource = new EventSource(`/api/briefing/status/${interviewId}/stream`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      status = data.status;
      message = data.message;
      progress = data.progress_percentage;

      // Close stream when complete or failed
      if (status === 'completed' || status === 'failed') {
        eventSource?.close();
      }
    };
  });

  onDestroy(() => {
    eventSource?.close();
  });

  async function checkStatus() {
    const response = await fetch(`/api/briefing/status/${interviewId}`);
    const data = await response.json();
    status = data.status;
    message = data.message;
    progress = data.progress_percentage;
  }

  async function retryGeneration() {
    // Trigger retry
    await fetch(`/api/briefing/generate/${interviewId}`, { method: 'POST' });
    status = 'initializing';
    message = 'Retrying...';
    progress = 0;

    // Reconnect to SSE stream
    eventSource = new EventSource(`/api/briefing/status/${interviewId}/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      status = data.status;
      message = data.message;
      progress = data.progress_percentage;
    };
  }
</script>

{#if status === 'completed'}
  <!-- Show full briefing content -->
  <div class="briefing-content">
    <!-- Briefing markdown rendered here -->
  </div>
{:else if status === 'failed'}
  <!-- Show error + retry button -->
  <div class="briefing-error">
    <p class="error-message">❌ Failed to generate briefing</p>
    <button on:click={retryGeneration} class="retry-button">
      Retry Briefing Generation
    </button>
  </div>
{:else}
  <!-- Show progress label (replaces "Generate Brief" button) -->
  <p class="briefing-status">
    ⏳ {message} ({progress}%)
  </p>
{/if}
```

### Implementation Phases

#### Phase 0: Real-Time Status Infrastructure (NEW)
**Objective**: Build infrastructure for real-time progress tracking and async briefing generation

**Tasks**:
1. Create `briefing_status` table migration
2. Implement database functions for status updates
3. Create Custom Event Listener (`BriefingProgressListener`)
4. Implement SSE endpoint (`/api/briefing/status/{interview_id}/stream`)
5. Implement polling endpoint (`/api/briefing/status/{interview_id}`)
6. Modify `POST /api/interviews` to trigger async generation
7. Create async briefing generation function with event listener integration
8. Build frontend progress component with SSE/polling support
9. Update interview creation UI to show real-time progress

**Success Criteria**:
- Briefing generation runs asynchronously
- Database updates in real-time as agents progress
- Frontend receives status updates via SSE or polling
- Progress percentage accurately reflects completion
- UI displays current agent and status message
- Interview creation returns immediately (non-blocking)

**Technical Notes**:
- Use FastAPI `BackgroundTasks` for async execution
- Event listener updates database on each task start/completion
- SSE connection automatically closes when status = completed/failed
- Polling fallback with exponential backoff for resilience

#### Phase 1: Core Agent Implementation
**Objective**: Implement the 7 agents with proper role definitions, goals, and backstories

**Tasks**:
1. Define each agent in `backend/app/crew/briefing.py`
2. Configure LLM settings for each agent (temperature, model selection)
3. Set verbose flags appropriately for debugging
4. Document agent personalities and strengths

**Success Criteria**:
- All 7 agents instantiated correctly
- Agent roles are distinct and non-overlapping
- LLM configurations optimized for each agent's purpose

#### Phase 2: Task and Workflow Implementation
**Objective**: Implement the 7 tasks with proper dependencies and context sharing

**Tasks**:
1. Create Task definitions for each agent
2. Implement parallel processing for Stages 1 and 2
3. Configure sequential processing for Stage 3
4. Set up context passing between dependent tasks
5. Define expected output formats for each task

**Success Criteria**:
- Parallel tasks execute simultaneously (performance gain)
- Sequential tasks receive correct context from prior tasks
- Task dependencies are properly configured

#### Phase 3: Quality Gate Implementation
**Objective**: Implement validation logic in quality checker agents

**Tasks**:
1. Define quality thresholds for Agents 2 and 4
2. Implement pass/fail logic
3. Create feedback mechanisms for failed validations
4. Add retry logic for failed quality gates
5. Implement logging for quality metrics

**Success Criteria**:
- Quality checkers can reject low-quality analysis
- Feedback is specific and actionable
- Metrics are tracked for monitoring

#### Phase 4: Output Formatting and Integration
**Objective**: Ensure final briefing output is well-structured and usable

**Tasks**:
1. Design briefing markdown template
2. Implement formatting logic in Agent 7
3. Add scoring visualizations (text-based or emoji-based)
4. Ensure briefing is interviewer-friendly
5. Test briefing rendering in frontend

**Success Criteria**:
- Briefing is consistently formatted
- All sections present and complete
- Easy to scan and consume during interview prep

#### Phase 5: Testing and Validation
**Objective**: Comprehensive testing of expanded agent system

**Tasks**:
1. Update unit tests in `backend/tests/test_crew.py`
2. Create integration tests with sample resumes and job descriptions
3. Test parallel processing performance
4. Test quality gate rejection scenarios
5. Test end-to-end briefing generation
6. Performance testing (execution time, token usage)

**Success Criteria**:
- All tests pass
- Quality gates work as expected
- Performance is acceptable (< 60 seconds end-to-end)
- Token usage is within budget

#### Phase 6: Monitoring and Optimization
**Objective**: Add observability and optimize performance

**Tasks**:
1. Add execution time logging for each stage
2. Track token usage per agent
3. Implement quality metric dashboards
4. Optimize prompts for efficiency
5. Add circuit breakers for failed agents

**Success Criteria**:
- Execution metrics visible
- Optimization opportunities identified
- System is resilient to individual agent failures

### Technical Considerations

#### Structured Output Strategy

**All analysis agents (1, 3, 5, 6) use explicit JSON schemas** to ensure consistent, parseable output:

- **Agent 1 (Resume Analyzer)**: 4-section schema (Skills, Experience, Education, Red Flags)
- **Agent 3 (Job Description Analyzer)**: 7-section schema (Required/Preferred Skills, Technical Requirements, etc.)
- **Agent 5 (Cross-Reference Matcher)**: Alignment matrix with scores, matches, gaps
- **Agent 6 (Question Generator)**: Prioritized question bank with rationales

**Benefits**:
- Eliminates ambiguity in agent outputs
- Enables reliable parsing by downstream agents
- Reduces hallucination by providing clear structure
- Makes quality checking more objective (Agent 2 & 4 can validate against schema)
- Simplifies debugging (invalid JSON = immediate failure)

**Implementation**:
- Task descriptions explicitly state: "Output MUST be valid JSON format only, no additional text"
- Each task includes the full expected JSON schema in the prompt
- Quality checkers validate both content AND schema compliance

#### CrewAI Process Types
- **Parallel Processing**: Use `Process.hierarchical` or custom task orchestration for Stages 1 and 2
- **Sequential Processing**: Use `Process.sequential` for Stage 3
- **Context Sharing**: Ensure task outputs are properly passed as context to dependent tasks

#### LLM Configuration
- **Analysis Agents (1, 3)**: `temperature=0.3` (more deterministic, structured extraction)
- **Quality Agents (2, 4)**: `temperature=0.1` (highly deterministic validation)
- **Synthesis Agents (5, 6, 7)**: `temperature=0.5` (balance creativity and structure)
- **Model Selection**: Consider using GPT-4 for quality agents, GPT-4o-mini for others (cost optimization)
- **JSON Mode**: Use OpenAI's JSON mode or equivalent for Agents 1, 3, 5, 6 to enforce valid JSON output

#### Error Handling
- Implement try-catch blocks for each stage
- Add fallback logic for quality gate failures
- Log all failures for debugging
- Provide partial results if final synthesis fails

#### Performance Optimization
- Run Agents 1 & 3 in parallel (save ~30-40% time)
- Run Agents 2 & 4 in parallel (save ~30-40% time)
- Cache LLM responses for testing
- Implement token usage monitoring

### Expected Benefits

#### Quality Improvements
- **Higher Accuracy**: Quality checkers catch mistakes and incomplete analysis
- **Comprehensive Coverage**: Specialized agents ensure no details missed
- **Better Questions**: Strategic question generation based on thorough analysis
- **Consistency**: Validation ensures consistent output quality

#### Process Improvements
- **Parallel Processing**: ~40-50% faster execution than pure sequential
- **Transparency**: Clear stages and checkpoints for debugging
- **Maintainability**: Modular agents easier to update and improve
- **Scalability**: Easy to add new agents or modify existing ones

#### User Experience Improvements
- **Better Briefings**: More thorough, actionable interview preparation
- **Confidence**: Interviewers trust quality-validated analysis
- **Efficiency**: Strategic questions save time in interviews
- **Insight**: Cross-reference analysis reveals subtle fit issues

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Increased latency from 7 agents | High | Parallel processing, use faster models for some agents |
| Higher token costs | Medium | Optimize prompts, use GPT-4o-mini where appropriate |
| Quality gates too strict (frequent rejections) | Medium | Tune thresholds based on real-world testing, implement graduated quality levels |
| Complex debugging with 7 agents | Medium | Comprehensive logging, verbose mode, stage-by-stage testing |
| Context loss between stages | High | Explicit context passing, validate context completeness |
| Agent hallucination in synthesis | High | Ground Agent 7 in validated inputs, add final sanity check |

### Success Metrics

#### Quality Metrics
- Quality gate pass rate: > 85% first pass
- Briefing completeness score: > 90%
- User satisfaction (interviewer feedback): > 4/5

#### Performance Metrics
- End-to-end execution time: < 60 seconds
- Token usage per briefing: < 15,000 tokens
- Parallel stage speedup: > 40% vs sequential

#### Adoption Metrics
- Interviewer briefing usage rate: > 80%
- Questions used from briefing: > 60%
- Return usage rate: > 70%

### Future Enhancements

1. **Feedback Loop**: Allow interviewers to rate briefing quality, feed back into agent improvement
2. **Learning Agents**: Implement memory/learning capabilities to improve over time
3. **Custom Agents**: Allow users to configure custom quality thresholds or question types
4. **Multi-Candidate Comparison**: Expand system to compare multiple candidates
5. **Interview Outcome Analysis**: Post-interview agent to analyze how interview went vs briefing
6. **Real-Time Adjustment**: Dynamic question generation during interview based on responses

### Appendix A: Sample Inputs and Outputs

#### Sample Resume (Input)
```
John Doe
Senior Software Engineer

EXPERIENCE
- Tech Corp (2020-Present): Led team of 5 engineers building microservices...
- StartupCo (2018-2020): Full-stack development using React and Node.js...

SKILLS
- Languages: Python, JavaScript, TypeScript, Go
- Frameworks: React, Node.js, FastAPI, Django
- Cloud: AWS, Docker, Kubernetes

EDUCATION
- BS Computer Science, State University (2018)
```

#### Sample Job Description (Input)
```
Staff Software Engineer

REQUIREMENTS
- 7+ years software engineering experience
- Expert in Python and distributed systems
- Experience leading engineering teams
- Strong system design skills

NICE TO HAVE
- Kubernetes experience
- Open source contributions
```

#### Expected Agent 1 Output (Resume Analysis)
```json
{
  "skills": {
    "languages": ["Python", "JavaScript", "TypeScript", "Go"],
    "frameworks": ["React", "Node.js", "FastAPI", "Django"],
    "cloud": ["AWS", "Docker", "Kubernetes"]
  },
  "experience": [
    {
      "company": "Tech Corp",
      "duration": "2020-Present (4 years)",
      "role": "Senior Software Engineer",
      "highlights": ["Led team of 5", "Microservices architecture"],
      "leadership": true
    }
  ],
  "experience_years": 6,
  "education": "BS Computer Science (2018)",
  "red_flags": ["Only 6 years experience (role requires 7+)", "No explicit distributed systems mention"]
}
```

#### Expected Agent 5 Output (Cross-Reference)
```json
{
  "overall_fit_score": 78,
  "category_scores": {
    "technical_skills": 85,
    "experience_level": 70,
    "leadership": 90
  },
  "strong_matches": [
    "Python expertise - confirmed",
    "Team leadership - demonstrated at Tech Corp",
    "Kubernetes - explicitly listed"
  ],
  "gaps": [
    {
      "requirement": "7+ years experience",
      "candidate_status": "6 years",
      "severity": "medium",
      "interview_focus": "Clarify depth of experience, assess rapid growth"
    },
    {
      "requirement": "Distributed systems expert",
      "candidate_status": "Not explicitly mentioned",
      "severity": "high",
      "interview_focus": "Probe microservices work for distributed systems knowledge"
    }
  ]
}
```

### Appendix B: Agent Prompt Templates

#### Agent 2 (Resume Quality Checker) - Prompt Template
```
You are a meticulous quality assurance specialist reviewing resume analysis.

You have been given:
1. Original Resume: {resume_text}
2. Resume Analysis: {agent_1_output}

Your task is to validate the analysis for:
- COMPLETENESS: Are all resume sections analyzed? (Skills, Experience, Education)
- ACCURACY: Are dates, companies, and skills correctly extracted?
- CATEGORIZATION: Are skills properly categorized (technical vs soft)?
- TIMELINE: Does the career progression make sense chronologically?
- RED FLAGS: Are legitimate concerns identified and false positives avoided?

Quality Gates:
✓ All major sections covered: YES/NO
✓ Skills extraction completeness: ≥ 80%
✓ Chronological validation: PASS/FAIL
✓ Education extracted: YES/NO

Provide:
1. quality_score (0-100)
2. missing_elements (list any overlooked sections)
3. accuracy_issues (list any errors or misinterpretations)
4. pass_fail (PASS or FAIL with reason)
5. approved_analysis (corrected version if PASS, null if FAIL)

Be strict but fair. If quality gates are not met, FAIL and provide specific feedback for re-analysis.
```

### Appendix C: File Structure Changes

```
backend/
├── app/
│   ├── crew/
│   │   ├── __init__.py
│   │   ├── briefing.py           # MODIFIED: Expanded from 2 to 7 agents
│   │   ├── agents/               # NEW: Agent definitions
│   │   │   ├── __init__.py
│   │   │   ├── resume_analyzer.py
│   │   │   ├── resume_quality_checker.py
│   │   │   ├── job_description_analyzer.py
│   │   │   ├── job_description_quality_checker.py
│   │   │   ├── cross_reference_matcher.py
│   │   │   ├── question_generator.py
│   │   │   └── briefing_synthesizer.py
│   │   ├── tasks/                # NEW: Task definitions
│   │   │   ├── __init__.py
│   │   │   ├── resume_tasks.py
│   │   │   ├── job_description_tasks.py
│   │   │   └── synthesis_tasks.py
│   │   └── templates/            # NEW: Output templates
│   │       ├── briefing_template.md
│   │       └── quality_report_template.md
│   └── api/
│       └── briefing.py           # MODIFIED: Update to use expanded crew
├── tests/
│   ├── test_crew.py              # MODIFIED: Expanded tests for 7 agents
│   ├── test_agents/              # NEW: Individual agent tests
│   │   ├── test_resume_analyzer.py
│   │   ├── test_resume_quality_checker.py
│   │   ├── test_job_description_analyzer.py
│   │   ├── test_job_description_quality_checker.py
│   │   ├── test_cross_reference_matcher.py
│   │   ├── test_question_generator.py
│   │   └── test_briefing_synthesizer.py
│   └── fixtures/                 # NEW: Test data
│       ├── sample_resumes.py
│       └── sample_job_descriptions.py
```

## Outstanding Questions & Clarifications

Before implementation begins, the following questions should be addressed:

### 1. **UI/UX Decisions**

**Q1.1**: Where should the progress indicator be displayed?
- **Option A**: On the interview creation success page (after form submission)
- **Option B**: Redirect to a dedicated "Generating Briefing" page
- **Option C**: Show progress inline on the same form page

**Recommendation**: Option A - Show progress on the success page where links are displayed, with a clear indicator that briefing is being generated.

**Q1.2**: Should users be able to access the interview room before the briefing is ready?
- **Option A**: Block access until briefing is complete (show "Preparing..." page)
- **Option B**: Allow access but show "Briefing still generating..." in the host view
- **Option C**: Pre-populate with basic info, then update when briefing is ready

**Recommendation**: Option B - Allow access but clearly indicate briefing status in the host view.

**Q1.3**: What should happen if briefing generation fails?
- **Option A**: Show error, allow retry with same interview
- **Option B**: Show error, require creating new interview
- **Option C**: Fall back to basic briefing (no CrewAI) and log error

**Recommendation**: Option A with Option C fallback - Allow retry, but if that fails, generate a basic manual briefing.

### 2. **Real-Time Updates - Implementation Details**

**Q2.1**: Should we use SSE, WebSockets, or Polling?
- **SSE (Server-Sent Events)**: One-way server→client, simpler, HTTP-based
- **WebSockets**: Two-way communication, more complex, requires WS server
- **Polling**: Simplest, higher latency, more server load

**Recommendation**: **SSE primary, polling fallback** - Best balance of real-time updates and simplicity. No need for WebSockets since communication is one-way (server → client).

**Q2.2**: What granularity of status updates do we want?
- **Option A**: Only task-level (7 updates total - one per agent)
- **Option B**: Task start + completion (14 updates - start/complete for each agent)
- **Option C**: Include agent step-level updates (50+ updates - every LLM call)

**Recommendation**: **Option B** - Task start + completion provides good balance. Too granular (Option C) may be noisy; too coarse (Option A) feels unresponsive.

**Q2.3**: Should status updates include estimated time remaining?
- **Yes**: Calculate based on average task duration (requires historical data)
- **No**: Just show progress percentage and current step

**Recommendation**: **No** initially - ETAs are notoriously inaccurate with LLM calls. Can add later if we collect sufficient historical data.

### 3. **Database & Performance**

**Q3.1**: Should we store all status updates or just the latest?
- **Option A**: Store all updates (full audit trail) in `briefing_status` table
- **Option B**: Update single record per interview (overwrite latest status)
- **Option C**: Store all, but only query latest for status endpoint

**Recommendation**: **Option C** - Store all for debugging/analytics, but optimize queries for latest status. Add retention policy to clean up old statuses after 30 days.

**Q3.2**: How should we handle concurrent briefing generations?
- **Current**: Single-threaded (one at a time)
- **Proposed**: Multiple concurrent (need worker pool/queue)

**Recommendation**: Start with **FastAPI BackgroundTasks** (simple, built-in). If we need better concurrency control, migrate to **Celery** or **ARQ** later.

**Q3.3**: Should briefing generation have a timeout?
- **Yes, what timeout?** (e.g., 5 minutes, 10 minutes)
- **No timeout** - let it run until completion or error

**Recommendation**: **Yes, 10-minute timeout** - LLM calls can hang. If timeout occurs, set status to `failed` and allow retry.

### 4. **Host View Integration**

**Q4.1**: Where should the briefing be displayed in the host view?
- **Option A**: Dedicated "Briefing" tab/section
- **Option B**: Sidebar panel always visible
- **Option C**: Modal/overlay that can be toggled

**Recommendation**: **Option A** - Dedicated section keeps interview UI clean, allows host to review briefing before/during interview.

**Q4.2**: Should the briefing auto-update if regenerated?
- **Yes**: Poll for briefing updates and refresh
- **No**: Require manual refresh

**Recommendation**: **No** - Once briefing is generated, it should be stable during the interview. Manual refresh option available if needed.

### 5. **Error Handling & Retry Logic**

**Q5.1**: If a quality gate fails (Agent 2 or 4 rejects analysis), should we:
- **Option A**: Retry automatically (up to N times)
- **Option B**: Fail entire briefing and notify user
- **Option C**: Continue with flagged but incomplete analysis

**Recommendation**: **Option A** - Retry up to 2 times, then fail with detailed error message. Quality gates are important but shouldn't block completely.

**Q5.2**: Should we implement circuit breakers for external LLM API failures?
- **Yes**: Stop trying after N consecutive failures
- **No**: Keep retrying indefinitely

**Recommendation**: **Yes** - Circuit breaker with exponential backoff. After 3 consecutive failures, wait 1 min, 5 min, 15 min before retry.

### 6. **Monitoring & Observability**

**Q6.1**: What metrics should we track?
- Briefing generation time (overall and per-agent)
- Token usage per agent
- Quality gate pass/fail rates
- Error rates by type
- User abandonment rate (users who create interview but never access it)

**Recommendation**: Track all of the above. Send to logging service (e.g., Sentry, LogRocket) and create dashboard.

**Q6.2**: Should we log full LLM responses for debugging?
- **Yes**: Store in database or log files
- **No**: Only log metadata (token count, latency, errors)

**Recommendation**: **Yes initially** - Store full responses for first 100 briefings to debug and tune agents. After stable, switch to metadata-only logging for privacy/cost.

## User Decisions - FINAL

All questions have been answered. Implementation can proceed with these specifications:

1. ✅ **Trigger mechanism**: Briefing generation starts automatically when interview is created (no manual trigger on creation page)

2. ✅ **Real-time updates**: UI displays live progress updates as each agent step starts/completes

3. ✅ **UI placement**: Progress indicator shows **in the host interview room page** where the "Generate Brief" button currently exists
   - Replace "Generate Brief" button with progress label during generation
   - Show concise text label with optional percentage: "Reviewing resume (14%)"

4. ✅ **Error handling**: On failure, show error message + "Retry Briefing Generation" button
   - Replace progress label with error message
   - Show retry button to trigger generation again

5. ✅ **Host view access**: Users CAN access interview room before briefing is ready
   - Show progress status in briefing section (where button currently is)
   - Once complete, show full briefing

6. ✅ **Status messages**: Short, concise labels (≤5 words):
   - "Reviewing resume"
   - "Checking resume analysis"
   - "Reviewing job description"
   - "Checking job analysis"
   - "Matching requirements"
   - "Generating questions"
   - "Creating briefing"

7. ✅ **Progress display format**: Simple text label with percentage
   - Example: "Reviewing resume (14%)"
   - Example: "Creating briefing (86%)"
   - No progress bar needed

## Conclusion

This expansion plan transforms the current simple 2-agent briefing system into a robust, quality-assured 7-agent architecture with **real-time progress tracking** and **asynchronous generation**. The parallel processing approach maintains acceptable performance while the quality validation layers ensure high-quality, reliable interview briefings.

The **automatic trigger on interview creation** ensures briefings are generated proactively, and the **real-time status updates** (via SSE or polling) provide excellent UX during the longer 7-agent workflow.

The modular design allows for incremental implementation and future enhancements, while the comprehensive testing strategy ensures reliability and maintainability.

---

## Implementation Ready - Final Summary

### ✅ All User Decisions Finalized

All outstanding questions have been answered. The plan is **ready for implementation**.

### Key Implementation Details

**UI Behavior**:
- ✅ Progress shows in **host interview room** (replaces "Generate Brief" button)
- ✅ Format: Simple text label with percentage → `"Reviewing resume (14%)"`
- ✅ Error handling: Show error message + "Retry Briefing Generation" button
- ✅ Host can access interview room **before** briefing is ready

**Status Messages** (≤5 words each):
1. "Reviewing resume"
2. "Checking resume analysis"
3. "Reviewing job description"
4. "Checking job analysis"
5. "Matching requirements"
6. "Generating questions"
7. "Creating briefing"

**Technical Architecture**:
- ✅ CrewAI Event System confirmed to support real-time tracking
- ✅ Custom `BaseEventListener` updates database on each task
- ✅ SSE primary, polling fallback for status updates
- ✅ FastAPI BackgroundTasks for async execution
- ✅ New `briefing_status` table tracks progress
- ✅ 10-minute timeout with retry capability

**API Endpoints**:
- `POST /api/interviews` - Creates interview + triggers async briefing
- `GET /api/briefing/status/{interview_id}` - Poll current status
- `GET /api/briefing/status/{interview_id}/stream` - SSE stream
- `POST /api/briefing/generate/{interview_id}` - Retry failed generation

### Recommended Implementation Order

**Phase 0: Real-Time Status Infrastructure** (Start Here)
1. Create `briefing_status` database table
2. Implement status update functions
3. Build Custom Event Listener (`BriefingProgressListener`)
4. Create SSE and polling API endpoints
5. Modify interview creation to trigger async generation
6. Build Svelte progress component for host view
7. Test end-to-end flow

**Phase 1-6**: Follow existing phase plan for 7-agent expansion

### Ready to Proceed

The plan is **fully specified** and **ready for implementation**. No further clarifications needed.
