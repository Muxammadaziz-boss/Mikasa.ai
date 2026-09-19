-- ==============================================================================
-- Mikasa AI v8.0.0 — Phase 41: Supabase Auth & PostgreSQL Schema Migration
-- Features:
--   1. auth.users 1:1 public.profiles
--   2. User-owned tables: devices, telegram_links, permissions
--   3. Row Level Security (RLS) enabled on all user tables
--   4. Automatic profile generation on auth.users insert (Trigger)
--   5. Multi-tenant isolation enforced via auth.uid()
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. PUBLIC.PROFILES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for username lookups
CREATE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles (lower(username));
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles (lower(email));

-- Automatic profile creation on auth.users registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    base_username TEXT;
    candidate_username TEXT;
    user_display_name TEXT;
    user_avatar TEXT;
    counter INT := 0;
BEGIN
    -- Determine display name (support Google OAuth 'full_name' or 'name')
    user_display_name := COALESCE(
        NULLIF(NEW.raw_user_meta_data->>'display_name', ''),
        NULLIF(NEW.raw_user_meta_data->>'full_name', ''),
        NULLIF(NEW.raw_user_meta_data->>'name', ''),
        split_part(NEW.email, '@', 1),
        'User'
    );

    -- Determine avatar (support Google OAuth 'avatar_url' or 'picture')
    user_avatar := COALESCE(
        NULLIF(NEW.raw_user_meta_data->>'avatar_url', ''),
        NULLIF(NEW.raw_user_meta_data->>'picture', '')
    );

    -- Base username from metadata, email, or uuid prefix
    base_username := lower(regexp_replace(
        COALESCE(
            NULLIF(NEW.raw_user_meta_data->>'username', ''),
            NULLIF(NEW.raw_user_meta_data->>'preferred_username', ''),
            split_part(NEW.email, '@', 1),
            'user'
        ),
        '[^a-zA-Z0-9_]', '', 'g'
    ));
    IF base_username = '' THEN
        base_username := 'user_' || substr(NEW.id::text, 1, 8);
    END IF;

    candidate_username := base_username;

    -- Ensure uniqueness by appending hash/counter if collision occurs
    WHILE EXISTS (SELECT 1 FROM public.profiles WHERE lower(username) = lower(candidate_username) AND id <> NEW.id) LOOP
        counter := counter + 1;
        candidate_username := base_username || '_' || substr(md5(NEW.id::text || counter::text), 1, 4);
    END LOOP;

    INSERT INTO public.profiles (id, username, email, display_name, avatar_url, is_verified)
    VALUES (
        NEW.id,
        candidate_username,
        NEW.email,
        user_display_name,
        user_avatar,
        COALESCE((NEW.email_confirmed_at IS NOT NULL), false)
    )
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        display_name = COALESCE(EXCLUDED.display_name, public.profiles.display_name),
        avatar_url = COALESCE(EXCLUDED.avatar_url, public.profiles.avatar_url),
        is_verified = EXCLUDED.is_verified,
        updated_at = timezone('utc'::text, now());

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE OF email, email_confirmed_at ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ------------------------------------------------------------------------------
-- 2. PUBLIC.DEVICES (HOST / AGENT DEVICES)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hostname TEXT DEFAULT '',
    mac_address TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    os TEXT DEFAULT '',
    agent_version TEXT DEFAULT '',
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_user_device UNIQUE (user_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_devices_user_id ON public.devices (user_id);
CREATE INDEX IF NOT EXISTS idx_devices_device_id ON public.devices (device_id);


-- ------------------------------------------------------------------------------
-- 3. PUBLIC.TELEGRAM_LINKS (TELEGRAM IDENTITY INTEGRATION)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.telegram_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    telegram_username TEXT,
    first_name TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_links_user_id ON public.telegram_links (user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_links_tg_id ON public.telegram_links (telegram_user_id);


-- ------------------------------------------------------------------------------
-- 4. PUBLIC.PERMISSIONS (DEVICE PERMISSION PROFILES)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    allowed_categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    require_confirmation_categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocked_commands JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_user_device_permission UNIQUE (user_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_permissions_user_device ON public.permissions (user_id, device_id);


-- ==============================================================================
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- A. PROFILES RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own"
    ON public.profiles
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
CREATE POLICY "profiles_update_own"
    ON public.profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- B. DEVICES RLS
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "devices_select_own" ON public.devices;
CREATE POLICY "devices_select_own"
    ON public.devices
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "devices_insert_own" ON public.devices;
CREATE POLICY "devices_insert_own"
    ON public.devices
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "devices_update_own" ON public.devices;
CREATE POLICY "devices_update_own"
    ON public.devices
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "devices_delete_own" ON public.devices;
CREATE POLICY "devices_delete_own"
    ON public.devices
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- C. TELEGRAM_LINKS RLS
ALTER TABLE public.telegram_links ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "telegram_links_select_own" ON public.telegram_links;
CREATE POLICY "telegram_links_select_own"
    ON public.telegram_links
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "telegram_links_insert_own" ON public.telegram_links;
CREATE POLICY "telegram_links_insert_own"
    ON public.telegram_links
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "telegram_links_update_own" ON public.telegram_links;
CREATE POLICY "telegram_links_update_own"
    ON public.telegram_links
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "telegram_links_delete_own" ON public.telegram_links;
CREATE POLICY "telegram_links_delete_own"
    ON public.telegram_links
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- D. PERMISSIONS RLS
ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "permissions_select_own" ON public.permissions;
CREATE POLICY "permissions_select_own"
    ON public.permissions
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "permissions_insert_own" ON public.permissions;
CREATE POLICY "permissions_insert_own"
    ON public.permissions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "permissions_update_own" ON public.permissions;
CREATE POLICY "permissions_update_own"
    ON public.permissions
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "permissions_delete_own" ON public.permissions;
CREATE POLICY "permissions_delete_own"
    ON public.permissions
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());
