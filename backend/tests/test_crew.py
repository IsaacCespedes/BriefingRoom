"""Tests for the briefing crew."""

import os
from unittest.mock import MagicMock, patch

import pytest
from langchain_openai import ChatOpenAI

from app.crew.briefing import create_briefing_crew


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    return MagicMock(spec=ChatOpenAI)


@pytest.fixture(autouse=True)
def set_openai_key():
    """Set a dummy OpenAI API key for testing."""
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    yield
    os.environ.pop("OPENAI_API_KEY", None)


@pytest.mark.unit
def test_create_briefing_crew_returns_crew(mock_llm):
    """Test that create_briefing_crew returns a Crew instance."""
    crew = create_briefing_crew(llm=mock_llm)
    assert crew is not None
    assert hasattr(crew, "kickoff")
    assert hasattr(crew, "agents")
    assert hasattr(crew, "tasks")


@pytest.mark.unit
def test_create_briefing_crew_has_agents(mock_llm):
    """Test that the crew has the expected agents."""
    crew = create_briefing_crew(llm=mock_llm)
    assert len(crew.agents) > 0
    agent_roles = [agent.role for agent in crew.agents]
    assert any("resume" in role.lower() or "analyst" in role.lower() for role in agent_roles)


@pytest.mark.unit
def test_create_briefing_crew_has_tasks(mock_llm):
    """Test that the crew has tasks defined."""
    crew = create_briefing_crew(llm=mock_llm)
    assert len(crew.tasks) > 0

