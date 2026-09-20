-- ========== Phase 47: Full Agent Access & User Consent ==========
-- Supabase Migration: agent_access_grants table
-- Device-scoped full agent authority grants with RLS

-- Create agent_access_grants table
CREATE TABLE IF NOT EXISTS public.agent_access_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    access_level TEXT NOT NULL DEFAULT 'LIMITED' CHECK (access_level IN ('LIMITED', 'FULL', 'CUSTOM')),
    policy_version TEXT NOT NULL DEFAULT '1.0.0',
    warning_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    warning_acknowledged_at TIMESTAMPTZ,
    reauthenticated_at TIMESTAMPTZ,
    confirmation_id TEXT,
    enabled_at TIMESTAMPTZ,
    disabled_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    overrides JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, device_id)
);

-- Add comments
COMMENT ON TABLE public.agent_access_grants IS 'Phase 47: Device-scoped full agent access grants with consent tracking';
COMMENT ON COLUMN public.agent_access_grants.access_level IS 'Agent vakolat darajasi: LIMITED, FULL, yoki CUSTOM';
COMMENT ON COLUMN public.agent_access_grants.overrides IS 'Individual permission overrides as JSON map';

-- Enable RLS
ALTER TABLE public.agent_access_grants ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own grants
CREATE POLICY "Users can view own agent access grants"
    ON public.agent_access_grants
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own agent access grants"
    ON public.agent_access_grants
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own agent access grants"
    ON public.agent_access_grants
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own agent access grants"
    ON public.agent_access_grants
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role full access (for backend operations)
CREATE POLICY "Service role full access to agent access grants"
    ON public.agent_access_grants
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_access_grants_user_id ON public.agent_access_grants(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_access_grants_device ON public.agent_access_grants(user_id, device_id);
CREATE INDEX IF NOT EXISTS idx_agent_access_grants_level ON public.agent_access_grants(access_level) WHERE access_level != 'LIMITED';

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_agent_access_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_access_updated_at
    BEFORE UPDATE ON public.agent_access_grants
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_access_updated_at();
