"""Pytest configuration and fixtures for integration tests."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env file from project root if it exists
# This matches the .env file used by Docker Compose
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables if not already set."""
    # Check if Supabase credentials are set
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        pytest.skip(
            "Supabase credentials not set. "
            "Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables "
            "in a .env file or as environment variables. "
            "These tests require a real Supabase database connection."
        )

