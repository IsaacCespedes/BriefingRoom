# Authentication & Authorization Design

## Overview

The Bionic Interviewer uses a simple, token-based authentication system designed for single-organization use. This approach eliminates the need for user accounts while providing secure, role-based access control.

## Token Model

### Token Structure

Each token is:
- **Interview-scoped**: Grants access to a specific interview
- **Role-based**: Assigned either "host" or "candidate" role
- **Secure**: Stored as a hash in the database (never plain text)
- **Time-limited**: Optional expiration for security
- **Revocable**: Can be deactivated without deleting the record

### Token Lifecycle

1. **Generation**: 
   - Triggered when an interview is created
   - Backend generates two tokens: one for host, one for candidate
   - Tokens are cryptographically secure random strings (UUID v4 or similar)
   - Tokens are hashed (SHA-256) before storage

2. **Distribution**:
   - Host token: Returned immediately to the host creating the interview
   - Candidate token: Generated but requires manual distribution (email, link, copy/paste)

3. **Validation**:
   - Frontend includes token in API requests (header or query param)
   - Backend hashes incoming token and looks up in database
   - Validates: hash match, active status, expiration, interview association

4. **Revocation**:
   - Tokens can be deactivated by setting `is_active = false`
   - Useful for security incidents or interview cancellation

## Database Schema

### tokens Table

```sql
CREATE TABLE tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('host', 'candidate')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_tokens_hash ON tokens(token_hash);
CREATE INDEX idx_tokens_interview ON tokens(interview_id);
```

## API Design

### Token Generation Endpoint

**POST** `/api/interviews`
- Creates new interview
- Generates host and candidate tokens
- Returns interview data with host token (candidate token separate endpoint)

**Response:**
```json
{
  "interview_id": "uuid",
  "host_token": "plain-token-string",
  "candidate_token": "plain-token-string",
  ...
}
```

### Token Validation (Middleware)

All protected endpoints use token validation middleware:

```python
async def validate_token(token: str) -> TokenInfo:
    """
    Validates token and returns interview_id and role.
    Raises HTTPException if invalid.
    """
    token_hash = hash_token(token)
    token_record = await db.get_token(token_hash)
    
    if not token_record or not token_record.is_active:
        raise HTTPException(401, "Invalid or inactive token")
    
    if token_record.expires_at and token_record.expires_at < now():
        raise HTTPException(401, "Token expired")
    
    return TokenInfo(
        interview_id=token_record.interview_id,
        role=token_record.role
    )
```

### Role-Based Access Control

**Host Permissions:**
- View and generate briefings
- Start/end video calls
- Add interview notes
- View all interview data
- Access Vapi voice interface

**Candidate Permissions:**
- Join video calls (via Daily.co link)
- View interview status (limited)
- Cannot access briefing or notes

## Frontend Integration

### Token Handling

1. **Initial Access**: Token passed via URL query parameter
   ```
   https://app.example.com/interview/abc123?token=xyz789
   ```

2. **Token Storage**: After initial load, token stored in:
   - Session storage (cleared on browser close) - recommended
   - Local storage (persists) - optional
   - Memory only (cleared on refresh) - most secure

3. **API Requests**: Token included in Authorization header
   ```
   Authorization: Bearer xyz789
   ```
   Or as query parameter for GET requests:
   ```
   GET /api/interviews/abc123?token=xyz789
   ```

### Role Detection

Frontend extracts role from token validation response:
```typescript
const { role, interview_id } = await validateToken(token);
// Route to appropriate UI based on role
```

## Security Best Practices

1. **Token Hashing**: Always hash tokens before storage (SHA-256)
2. **HTTPS Only**: Enforce HTTPS in production
3. **Token Expiration**: Set reasonable expiration times (e.g., 7 days default)
4. **Revocation**: Provide mechanism to revoke tokens
5. **Rate Limiting**: Limit token validation attempts to prevent brute force
6. **Secure Generation**: Use cryptographically secure random generators
7. **No Token Reuse**: Generate new tokens for each interview

## Implementation Notes

### Token Generation (Backend)

```python
import secrets
import hashlib

def generate_token() -> tuple[str, str]:
    """Generate token and its hash."""
    token = secrets.token_urlsafe(32)  # 256-bit token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash
```

### Token Validation (Backend)

```python
from fastapi import Depends, HTTPException, Header

async def get_current_token(
    authorization: str = Header(None),
    token: str = Query(None)
) -> TokenInfo:
    """Extract and validate token from header or query."""
    token_value = authorization.replace("Bearer ", "") if authorization else token
    if not token_value:
        raise HTTPException(401, "Token required")
    
    return await validate_token(token_value)
```

### Role-Based Dependency (Backend)

```python
def require_role(allowed_roles: list[str]):
    """Dependency factory for role-based access."""
    async def role_checker(token_info: TokenInfo = Depends(get_current_token)):
        if token_info.role not in allowed_roles:
            raise HTTPException(403, f"Role '{token_info.role}' not allowed")
        return token_info
    return role_checker

# Usage in routes
@router.post("/generate-briefing")
async def generate_briefing(
    token_info: TokenInfo = Depends(require_role(["host"]))
):
    # Only hosts can generate briefings
    ...
```

## Migration Path

When implementing:
1. Create `tokens` table via Supabase migration
2. Update interview creation to generate tokens
3. Add token validation middleware
4. Update all protected endpoints to use token validation
5. Update frontend to handle token-based auth

