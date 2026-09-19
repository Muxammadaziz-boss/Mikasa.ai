// ==============================================================================
// Mikasa AI — Supabase Client Service (Phase 41)
// Handles direct client-side authentication, session persistence and tokens.
// NOTE: Only VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are used here.
// NEVER expose SUPABASE_SERVICE_ROLE_KEY to the frontend!
// ==============================================================================

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const rawUrl = import.meta.env.VITE_SUPABASE_URL;
const rawAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const isSupabaseConfigured = Boolean(
  rawUrl &&
  rawAnonKey &&
  !rawUrl.includes('placeholder-project') &&
  rawAnonKey !== 'placeholder-anon-key'
);

const supabaseUrl = isSupabaseConfigured ? rawUrl : 'https://placeholder-project.supabase.co';
const supabaseAnonKey = isSupabaseConfigured ? rawAnonKey : 'placeholder-anon-key';

export const getSupabaseConfigStatus = () => ({
  configured: isSupabaseConfigured,
  hasUrl: Boolean(rawUrl && !rawUrl.includes('placeholder-project')),
  hasKey: Boolean(rawAnonKey && rawAnonKey !== 'placeholder-anon-key'),
});

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: window.localStorage
  }
});

