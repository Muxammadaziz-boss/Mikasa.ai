// ==============================================================================
// Mikasa AI — Supabase Client Service (Phase 41+)
// Handles direct client-side authentication, session persistence and tokens.
// NOTE: Only VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY are used here.
// NEVER expose SUPABASE_SECRET_KEY or service_role to the frontend!
// ==============================================================================

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const rawUrl = import.meta.env.VITE_SUPABASE_URL;
const rawPublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(
  rawUrl &&
  rawPublishableKey &&
  !rawUrl.includes('placeholder-project') &&
  rawPublishableKey !== 'placeholder-anon-key' &&
  rawPublishableKey !== 'placeholder-publishable-key'
);

const supabaseUrl = isSupabaseConfigured ? rawUrl : 'https://placeholder-project.supabase.co';
const supabaseKey = isSupabaseConfigured ? rawPublishableKey : 'placeholder-publishable-key';

export const getSupabaseConfigStatus = () => ({
  configured: isSupabaseConfigured,
  hasUrl: Boolean(rawUrl && !rawUrl.includes('placeholder-project')),
  hasKey: Boolean(rawPublishableKey && rawPublishableKey !== 'placeholder-anon-key' && rawPublishableKey !== 'placeholder-publishable-key'),
});

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: window.localStorage
  }
});

