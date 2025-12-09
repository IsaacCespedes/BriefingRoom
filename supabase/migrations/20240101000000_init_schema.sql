-- Create required Supabase roles first
DO $$
BEGIN
    -- Create supabase_admin role (for postgres-meta)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_admin') THEN
        CREATE ROLE supabase_admin WITH LOGIN PASSWORD 'postgres' SUPERUSER;
    ELSE
        -- Ensure password is set even if role already exists
        ALTER ROLE supabase_admin WITH PASSWORD 'postgres' SUPERUSER;
    END IF;

    -- Create supabase_auth_admin role (for GoTrue)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_auth_admin') THEN
        CREATE ROLE supabase_auth_admin WITH LOGIN PASSWORD 'postgres' CREATEDB CREATEROLE;
    ELSE
        -- Ensure password is set even if role already exists
        ALTER ROLE supabase_auth_admin WITH PASSWORD 'postgres' CREATEDB CREATEROLE;
    END IF;

    -- Create authenticator role (for PostgREST)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator WITH LOGIN PASSWORD 'postgres' NOINHERIT;
    ELSE
        -- Ensure password is set even if role already exists
        ALTER ROLE authenticator WITH PASSWORD 'postgres' NOINHERIT;
    END IF;

    -- Create anon role (anonymous access for PostgREST)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;

    -- Create authenticated role (authenticated access for PostgREST)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;

    -- Create service_role (admin operations)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;

    -- Grant permissions
    GRANT anon TO authenticator;
    GRANT authenticated TO authenticator;
    GRANT service_role TO authenticator;
    GRANT supabase_auth_admin TO authenticator;
END
$$;

-- Create auth schema for GoTrue
CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION supabase_auth_admin;

-- Grant schema permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO supabase_admin, supabase_auth_admin;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
GRANT USAGE ON SCHEMA auth TO authenticated, service_role;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    job_description TEXT NOT NULL,
    resume_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
);

-- Create interview_notes table
CREATE TABLE IF NOT EXISTS interview_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    note TEXT NOT NULL,
    source TEXT NOT NULL
);

-- Create tokens table
CREATE TABLE IF NOT EXISTS tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('host', 'candidate')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tokens_hash ON tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_tokens_interview ON tokens(interview_id);
CREATE INDEX IF NOT EXISTS idx_interview_notes_interview ON interview_notes(interview_id);

-- Grant table permissions
GRANT ALL ON TABLE interviews TO anon, authenticated, service_role;
GRANT ALL ON TABLE interview_notes TO anon, authenticated, service_role;
GRANT ALL ON TABLE tokens TO anon, authenticated, service_role;

-- Set up Row Level Security (RLS)
-- service_role has BYPASSRLS, so it can access all rows regardless of policies
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tokens ENABLE ROW LEVEL SECURITY;

