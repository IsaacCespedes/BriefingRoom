"""URL handler service for validating and processing job posting URLs."""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# LinkedIn domains (blocked for scraping)
LINKEDIN_DOMAINS = {"linkedin.com", "www.linkedin.com"}

# Common job board domains (for reference)
JOB_BOARD_DOMAINS = {
    "indeed.com",
    "www.indeed.com",
    "glassdoor.com",
    "www.glassdoor.com",
    "monster.com",
    "www.monster.com",
    "ziprecruiter.com",
    "www.ziprecruiter.com",
}


@dataclass
class URLResult:
    """Result of URL validation."""

    url: str
    metadata: dict  # domain, validation_status, etc.
    warnings: list  # blocked domains, etc.


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL format.
    
    Returns:
        (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    # Basic URL format validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    
    if not url_pattern.match(url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    # Ensure HTTPS (security best practice)
    if not url.startswith("https://"):
        return False, "Only HTTPS URLs are allowed for security"
    
    return True, None


def is_linkedin_url(url: str) -> bool:
    """Check if URL is a LinkedIn profile or job posting."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(linkedin_domain in domain for linkedin_domain in LINKEDIN_DOMAINS)
    except Exception:
        return False


def validate_and_store_url(
    url: str,
    interview_id: str,
    field_type: str,  # "job_description" or "resume"
) -> URLResult:
    """
    Validate URL and return for CrewAI processing.
    
    Note: CrewAI agents will use ScrapeWebsiteTool to extract content.
    
    Args:
        url: URL to validate
        interview_id: Interview ID (for reference)
        field_type: "job_description" or "resume"
    
    Returns:
        URLResult with url, metadata, and warnings
    
    Raises:
        ValueError: If URL validation fails
    """
    # Validate URL format
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        raise ValueError(error_msg or "URL validation failed")
    
    # Parse URL for metadata
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Check for LinkedIn (blocked)
    warnings = []
    if is_linkedin_url(url):
        warnings.append(
            "LinkedIn profiles cannot be automatically imported. "
            "Please copy/paste the content as plain text."
        )
    
    # Determine if it's a known job board
    is_job_board = any(job_domain in domain for job_domain in JOB_BOARD_DOMAINS)
    
    # Prepare metadata
    metadata = {
        "domain": domain,
        "validation_status": "valid",
        "is_job_board": is_job_board,
        "is_linkedin": is_linkedin_url(url),
        "path": parsed.path,
    }
    
    return URLResult(
        url=url,
        metadata=metadata,
        warnings=warnings,
    )
