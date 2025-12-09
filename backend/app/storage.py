"""Shared in-memory storage for development.

This module provides in-memory storage for interviews and tokens.
In production, this should be replaced with database operations.
"""

# In-memory storage for development (replace with database in production)
interviews_store: dict[str, dict] = {}
tokens_store: dict[str, dict] = {}

