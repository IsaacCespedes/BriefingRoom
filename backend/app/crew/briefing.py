"""CrewAI briefing crew for analyzing resumes and generating interview briefings."""

import logging
from typing import Optional

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_briefing_crew(llm: Optional[ChatOpenAI] = None) -> Crew:
    """Create a CrewAI crew for generating interview briefings.

    Args:
        llm: Optional LLM instance. If not provided, creates a new ChatOpenAI instance.

    Returns:
        Crew: A configured CrewAI crew with agents and tasks for briefing generation.
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # Define agents
    resume_analyst = Agent(
        role="Resume Analyst",
        goal="Analyze candidate resumes thoroughly and extract key information about skills, experience, and qualifications",
        backstory="You are an experienced HR professional with expertise in analyzing resumes and identifying candidate strengths and potential fit for roles.",
        verbose=True,
        llm=llm,
    )

    briefing_generator = Agent(
        role="Briefing Generator",
        goal="Create concise interview briefings with candidate summaries and strategic questions",
        backstory="You are a senior recruiter who prepares brief briefings for interview hosts, highlighting key candidate information and suggesting strategic questions to ask during interviews. Keep briefings concise and focused.",
        verbose=True,
        llm=llm,
    )

    # Define tasks - IMPORTANT: Use {variable_name} syntax to pass inputs
    analyze_resume_task = Task(
        description="""Analyze the candidate's resume provided below and extract key information including: 
        - Skills (technical and soft skills)
        - Work experience (companies, roles, dates, key achievements)
        - Education
        - Notable achievements
        - Potential red flags or areas of concern
        
        Resume text:
        {resume_text}
        
        Provide a structured analysis focusing on the most relevant qualifications.""",
        agent=resume_analyst,
        expected_output="A concise analysis of the candidate's resume with structured information about their qualifications.",
    )

    generate_briefing_task = Task(
        description="""Based on the resume analysis from the previous task and the job description below, create a concise interview briefing (maximum 300 words) that includes:
        1. Brief candidate summary (2-3 sentences)
        2. Key strengths relevant to the role (3-4 bullet points)
        3. Potential concerns or questions to explore (2-3 bullet points)
        4. Strategic interview questions (3-5 questions tailored to the role)
        
        Job Description:
        {job_description}
        
        Use the resume analysis from the previous task to understand the candidate's background. Keep the briefing concise and focused. Reference specific skills and experiences from both the resume analysis and job description.""",
        agent=briefing_generator,
        expected_output="A concise interview briefing (max 300 words) with candidate summary, key strengths, concerns, and strategic questions.",
        context=[analyze_resume_task],  # Explicitly pass previous task output as context
    )

    # Create crew
    crew = Crew(
        agents=[resume_analyst, briefing_generator],
        tasks=[analyze_resume_task, generate_briefing_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew

