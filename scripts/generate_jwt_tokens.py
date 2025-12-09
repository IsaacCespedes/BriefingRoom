#!/usr/bin/env python3
"""Generate JWT tokens for Supabase local development.

This script generates JWT tokens (anon and service_role) that are signed
with the JWT_SECRET used in docker-compose.yml.
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict

import jwt


def generate_jwt_token(role: str, secret: str, exp_days: int = 365) -> str:
    """Generate a JWT token for the given role."""
    now = datetime.utcnow()
    # Set iat to slightly in the past to avoid clock skew issues
    iat_time = now - timedelta(seconds=5)
    
    payload: Dict = {
        "iss": "supabase-demo",
        "ref": "default-project-ref",
        "role": role,
        "iat": int(iat_time.timestamp()),
        "exp": int((now + timedelta(days=exp_days)).timestamp()),
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def main():
    """Generate JWT tokens for anon and service_role."""
    # Default JWT_SECRET from docker-compose.yml
    jwt_secret = sys.argv[1] if len(sys.argv) > 1 else "super-secret-jwt-token-with-at-least-32-characters-long"
    
    print(f"Using JWT_SECRET: {jwt_secret[:20]}...")
    print()
    
    # Generate anon token
    anon_token = generate_jwt_token("anon", jwt_secret)
    print("SUPABASE_ANON_KEY:")
    print(anon_token)
    print()
    
    # Generate service_role token
    service_role_token = generate_jwt_token("service_role", jwt_secret)
    print("SUPABASE_SERVICE_ROLE_KEY:")
    print(service_role_token)
    print()
    
    # Verify tokens can be decoded (with leeway for clock skew)
    try:
        decoded_anon = jwt.decode(anon_token, jwt_secret, algorithms=["HS256"], leeway=60)
        decoded_service = jwt.decode(service_role_token, jwt_secret, algorithms=["HS256"], leeway=60)
        print("✓ Tokens verified successfully")
        print(f"  Anon role: {decoded_anon['role']}")
        print(f"  Service role: {decoded_service['role']}")
    except Exception as e:
        print(f"✗ Token verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

