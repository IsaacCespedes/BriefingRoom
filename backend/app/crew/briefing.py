"""CrewAI briefing crew for analyzing resumes and generating interview briefings."""

from typing import Optional

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI


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
        goal="Create comprehensive interview briefings with candidate summaries and strategic questions",
        backstory="You are a senior recruiter who prepares detailed briefings for interview hosts, highlighting key candidate information and suggesting strategic questions to ask during interviews.",
        verbose=True,
        llm=llm,
    )

    # Define tasks
    analyze_resume_task = Task(
        description="Analyze the candidate's resume and extract key information including: skills, work experience, education, achievements, and potential red flags or areas of concern.",
        agent=resume_analyst,
        expected_output="A detailed analysis of the candidate's resume with structured information about their qualifications.",
    )

    generate_briefing_task = Task(
        description="Based on the resume analysis and job description, create a comprehensive briefing that includes: a candidate summary, key strengths, potential concerns, and strategic interview questions tailored to the role.",
        agent=briefing_generator,
        expected_output="A complete interview briefing document with candidate summary and strategic questions.",
    )

    # Create crew
    crew = Crew(
        agents=[resume_analyst, briefing_generator],
        tasks=[analyze_resume_task, generate_briefing_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew

