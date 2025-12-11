"""CrewAI review crew for analyzing interview transcripts and generating candidate assessments."""

import logging
from typing import Optional

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_review_crew(llm: Optional[ChatOpenAI] = None) -> Crew:
    """Create a CrewAI crew for generating interview reviews.

    Args:
        llm: Optional LLM instance. If not provided, creates a new ChatOpenAI instance.

    Returns:
        Crew: A configured CrewAI crew with agents and tasks for review generation.
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # Define agents with teammate tone
    transcript_analyst = Agent(
        role="Interview Transcript Analyst",
        goal="Thoroughly analyze interview transcripts to extract key insights about the candidate's performance, responses, and communication style. Identify specific examples and evidence from the conversation.",
        backstory="You're a trusted teammate who's been through hundreds of interviews. You have a sharp eye for detail and can spot both strengths and areas for improvement. You communicate your findings directly and honestly, like you're debriefing with a colleague after a meeting.",
        verbose=True,
        llm=llm,
    )

    assessment_generator = Agent(
        role="Interview Assessment Generator",
        goal="Create comprehensive interview assessments that summarize the call, evaluate candidate performance, and provide evidence-based recommendations. Write in a clear, direct style as if you're sharing insights with a teammate.",
        backstory="You're a senior teammate who's great at synthesizing information and making clear recommendations. You always back up your assessments with specific evidence from the interview. You write like you're preparing a brief for your team - direct, actionable, and honest.",
        verbose=True,
        llm=llm,
    )

    # Define tasks
    analyze_transcript_task = Task(
        description="""Analyze the interview transcript thoroughly and extract key insights including:
        
        - Candidate's responses to questions (quality, depth, relevance)
        - Communication style and clarity
        - Technical knowledge and expertise demonstrated
        - Problem-solving approach and examples provided
        - Cultural fit indicators
        - Areas of concern or red flags
        - Specific quotes or examples that illustrate points
        
        Transcript content: {transcript_text}
        
        Focus on finding concrete evidence from the conversation. Note specific examples, quotes, or moments that demonstrate strengths or weaknesses. Be thorough but objective.""",
        agent=transcript_analyst,
        expected_output="A brief, bullet-point analysis of the transcript. Focus on key moments and direct quotes. Keep it concise, like quick notes for a debrief.",
    )

    generate_assessment_task = Task(
        description="""Based on the transcript analysis from the previous task, create a comprehensive interview review that includes:
        
        1. **Overall Assessment**: A high-level summary of the candidate's performance and fit
        2. **Call Summary**: A concise summary of what was discussed during the interview
        3. **Candidate Strengths**: Specific strengths demonstrated during the interview, backed by evidence from the transcript
        4. **Candidate Weaknesses or Concerns**: Areas of concern or gaps identified, with specific examples
        5. **Interview Quality**: Assessment of how well the interview flowed and what was covered
        6. **Evidence-Based Recommendations**: Clear recommendations (e.g., proceed to next round, not a fit, needs more evaluation) with specific reasons based on the transcript
        
        Write this as if you're debriefing with a teammate - be direct, honest, and actionable. Every assessment point should be backed by specific evidence from the transcript. Use a professional but conversational tone.
        
        Format the review clearly with sections for easy reading.""",
        agent=assessment_generator,
        expected_output="A short, informal interview review. Summarize the candidate's performance, list a few key strengths and weaknesses with evidence, and give a clear recommendation. Write it like a quick follow-up message to your teammate.",
        context=[analyze_transcript_task],
    )

    # Create crew
    crew = Crew(
        agents=[transcript_analyst, assessment_generator],
        tasks=[analyze_transcript_task, generate_assessment_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew
