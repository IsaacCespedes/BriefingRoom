#!/usr/bin/env python3
"""Automate updating JWT tokens in docker-compose.yml.

This script:
1. Runs generate_jwt_tokens.py to get fresh tokens.
2. Parses the output to extract the new keys.
3. Reads the docker-compose.yml file.
4. Replaces the default SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY.
5. Writes the updated content back to the file.
"""

import re
import subprocess
import sys
from pathlib import Path


def run_generate_tokens() -> str:
    """Run the token generation script and return its output."""
    script_path = Path(__file__).parent / "generate_jwt_tokens.py"
    if not script_path.exists():
        print(f"Error: {script_path} not found.", file=sys.stderr)
        sys.exit(1)
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def extract_token_from_output(output: str, key_name: str) -> str:
    """Extract a token value from the script's output."""
    match = re.search(f"^{key_name}:\s*(\S+)", output, re.MULTILINE)
    if not match:
        print(f"Error: Could not find {key_name} in script output.", file=sys.stderr)
        sys.exit(1)
    return match.group(1)


def update_docker_compose(anon_key: str, service_role_key: str):
    """Update the docker-compose.yml file with the new keys."""
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_path.exists():
        print(f"Error: {compose_path} not found.", file=sys.stderr)
        sys.exit(1)
    
    content = compose_path.read_text()
    
    # Regex to find and replace the default token values
    content = re.sub(
        r"(SUPABASE_ANON_KEY: \${SUPABASE_ANON_KEY:-)(\S+)(})",
        f"\g<1>{anon_key}\g<3>",
        content,
    )
    
    content = re.sub(
        r"(SUPABASE_SERVICE_ROLE_KEY: \${SUPABASE_SERVICE_ROLE_KEY:-)(\S+)(})",
        f"\g<1>{service_role_key}\g<3>",
        content,
    )
    
    compose_path.write_text(content)


def main():
    """Main function to run the update process."""
    print("Generating new JWT tokens...")
    output = run_generate_tokens()
    
    anon_key = extract_token_from_output(output, "SUPABASE_ANON_KEY")
    service_role_key = extract_token_from_output(output, "SUPABASE_SERVICE_ROLE_KEY")
    
    print("Updating docker-compose.yml...")
    update_docker_compose(anon_key, service_role_key)
    
    print("✓ Successfully updated docker-compose.yml with new JWT tokens.")
    print("Please restart your services for the changes to take effect:")
    print("  docker-compose up -d --build")


if __name__ == "__main__":
    main()
