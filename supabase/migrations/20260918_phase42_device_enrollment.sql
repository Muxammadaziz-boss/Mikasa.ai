-- ==============================================================================
-- Mikasa AI v8.0.0 — Phase 42: Secure PC Agent Enrollment & Pairing Migration
-- Features:
--   1. device_pairing_sessions (short-lived 5-min pairing code sessions)
--   2. device_credentials (device Ed25519 public keys & cryptographic credentials)
--   3. device_auth_challenges (single-use nonces for replay-protected challenge-response)
--   4. Row Level Security (RLS) enabled on all user-owned tables
--   5. Multi-tenant isolation enforced via auth.uid()
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. PUBLIC.DEVICE_PAIRING_SESSIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.device_pairing_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    pairing_code_hash TEXT NOT NULL,
    pairing_code_salt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    device_id TEXT,
    request_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_pairing_sessions_user_id ON public.device_pairing_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_pairing_sessions_status ON public.device_pairing_sessions (status);

-- ------------------------------------------------------------------------------
-- 2. PUBLIC.DEVICE_CREDENTIALS (CRYPTOGRAPHIC PUBLIC KEYS)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.device_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    public_key TEXT NOT NULL,
    algorithm TEXT NOT NULL DEFAULT 'ed25519',
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    enrolled_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    revoked_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT uq_user_device_credential UNIQUE (user_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_device_credentials_user_id ON public.device_credentials (user_id);
CREATE INDEX IF NOT EXISTS idx_device_credentials_device_id ON public.device_credentials (device_id);

-- ------------------------------------------------------------------------------
-- 3. PUBLIC.DEVICE_AUTH_CHALLENGES (SINGLE-USE NONCES & REPLAY PROTECTION)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.device_auth_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id TEXT NOT NULL,
    nonce TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_device_challenges_device_id ON public.device_auth_challenges (device_id);
CREATE INDEX IF NOT EXISTS idx_device_challenges_nonce ON public.device_auth_challenges (nonce);


-- ==============================================================================
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- A. DEVICE PAIRING SESSIONS RLS
ALTER TABLE public.device_pairing_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "device_pairing_sessions_select_own" ON public.device_pairing_sessions;
CREATE POLICY "device_pairing_sessions_select_own"
    ON public.device_pairing_sessions
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "device_pairing_sessions_insert_own" ON public.device_pairing_sessions;
CREATE POLICY "device_pairing_sessions_insert_own"
    ON public.device_pairing_sessions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "device_pairing_sessions_update_own" ON public.device_pairing_sessions;
CREATE POLICY "device_pairing_sessions_update_own"
    ON public.device_pairing_sessions
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "device_pairing_sessions_delete_own" ON public.device_pairing_sessions;
CREATE POLICY "device_pairing_sessions_delete_own"
    ON public.device_pairing_sessions
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- B. DEVICE CREDENTIALS RLS
ALTER TABLE public.device_credentials ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "device_credentials_select_own" ON public.device_credentials;
CREATE POLICY "device_credentials_select_own"
    ON public.device_credentials
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "device_credentials_insert_own" ON public.device_credentials;
CREATE POLICY "device_credentials_insert_own"
    ON public.device_credentials
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "device_credentials_update_own" ON public.device_credentials;
CREATE POLICY "device_credentials_update_own"
    ON public.device_credentials
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "device_credentials_delete_own" ON public.device_credentials;
CREATE POLICY "device_credentials_delete_own"
    ON public.device_credentials
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- C. DEVICE AUTH CHALLENGES RLS (SINGLE-USE NONCES)
ALTER TABLE public.device_auth_challenges ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "device_auth_challenges_select" ON public.device_auth_challenges;
CREATE POLICY "device_auth_challenges_select"
    ON public.device_auth_challenges
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.devices
            WHERE public.devices.device_id = public.device_auth_challenges.device_id
              AND public.devices.user_id = auth.uid()
        )
    );
