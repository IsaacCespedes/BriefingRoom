"""CrewAI briefing crew for analyzing resumes and generating interview briefings."""

import logging
from typing import Optional

from crewai import Agent, Crew, Process, Task
from crewai_tools import DOCXSearchTool, PDFSearchTool, ScrapeWebsiteTool
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

    # Set up tools for document processing
    tools = []
    
    # Add PDF search tool
    pdf_search_tool = PDFSearchTool()
    tools.append(pdf_search_tool)
    
    # Add DOCX search tool
    docx_search_tool = DOCXSearchTool()
    tools.append(docx_search_tool)
    
    # Add web scraping tool for URLs
    scrape_tool = ScrapeWebsiteTool()
    tools.append(scrape_tool)

    # Define agents with tools and teammate tone
    resume_analyst = Agent(
        role="Resume Analyst",
        goal="Analyze candidate resumes thoroughly and extract key information about skills, experience, and qualifications. If the resume is provided as a file path or URL, use the available tools to extract the text first.",
        backstory="You're a trusted teammate who's reviewed hundreds of resumes. You have a sharp eye for detail and can quickly identify what matters. You communicate your findings directly and honestly, like you're prepping a colleague for an important meeting.",
        verbose=True,
        llm=llm,
        tools=tools,
    )

    briefing_generator = Agent(
        role="Briefing Generator",
        goal="Create comprehensive interview briefings with candidate summaries and strategic questions. If the job description is provided as a file path or URL, use the available tools to extract the text first.",
        backstory="You're a senior teammate who's great at preparing interview briefings. You write like you're sharing insights with a colleague - direct, actionable, and focused on what really matters. You highlight key candidate information and suggest strategic questions that will help your teammate conduct an effective interview.",
        verbose=True,
        llm=llm,
        tools=tools,
    )

    # Define tasks
    analyze_resume_task = Task(
        description="""Analyze the candidate's resume and extract key information including: skills, work experience, education, achievements, and potential red flags or areas of concern.
        
        Resume content: {resume_text}
        
        IMPORTANT: The input is prefixed with a type indicator. You MUST use the appropriate tool based on the prefix:
        
        - If it starts with "PDF_FILE:" → Remove the prefix and use PDFSearchTool on the URL/path that follows
        - If it starts with "DOCX_FILE:" → Remove the prefix and use DOCXSearchTool on the URL/path that follows
        - If it starts with "FILE:" → Remove the prefix and try to determine file type from the extension, then use PDFSearchTool or DOCXSearchTool
        - If it starts with "WEBSITE_URL:" → Remove the prefix and use ScrapeWebsiteTool on the URL that follows
        - If it's plain text (no prefix): Analyze directly without using tools
        
        Examples:
        - "PDF_FILE:https://example.com/storage/file.pdf?token=abc" → Use PDFSearchTool on "https://example.com/storage/file.pdf?token=abc"
        - "WEBSITE_URL:https://example.com/job-posting" → Use ScrapeWebsiteTool on "https://example.com/job-posting"
        - "John Doe, Software Engineer..." → Analyze directly (plain text)
        
        After extracting the text (if needed), provide a detailed analysis with structured information about their qualifications.""",
        agent=resume_analyst,
        expected_output="A concise, bullet-point summary of the candidate's qualifications, highlighting key skills and experience. Keep it brief and to the point, like you're sharing quick notes with a teammate.",
    )

    generate_briefing_task = Task(
        description="""Based on the resume analysis from the previous task and the job description below, create a comprehensive briefing that includes: a candidate summary, key strengths, potential concerns, and strategic interview questions tailored to the role.
        
        Job description content: {job_description}
        
        IMPORTANT: The input is prefixed with a type indicator. You MUST use the appropriate tool based on the prefix:
        
        - If it starts with "PDF_FILE:" → Remove the prefix and use PDFSearchTool on the URL/path that follows
        - If it starts with "DOCX_FILE:" → Remove the prefix and use DOCXSearchTool on the URL/path that follows
        - If it starts with "FILE:" → Remove the prefix and try to determine file type from the extension, then use PDFSearchTool or DOCXSearchTool
        - If it starts with "WEBSITE_URL:" → Remove the prefix and use ScrapeWebsiteTool on the URL that follows
        - If it's plain text (no prefix): Use directly without using tools
        
        Examples:
        - "PDF_FILE:https://example.com/storage/file.pdf?token=abc" → Use PDFSearchTool on "https://example.com/storage/file.pdf?token=abc"
        - "WEBSITE_URL:https://example.com/job-posting" → Use ScrapeWebsiteTool on "https://example.com/job-posting"
        - "Software Engineer position..." → Use directly (plain text)
        
        After extracting the job description text (if needed), create the briefing based on both the resume analysis and job description.""",
        agent=briefing_generator,
        expected_output="A short and informal interview briefing. Include a brief candidate summary and a few key strategic questions. Write it like you're sending a quick prep message to a teammate.",
        context=[analyze_resume_task],
    )

    # Create crew
    crew = Crew(
        agents=[resume_analyst, briefing_generator],
        tasks=[analyze_resume_task, generate_briefing_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew

