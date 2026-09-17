// ==============================================================================
// Mikasa AI — Supabase Client Service (Phase 41)
// Handles direct client-side authentication, session persistence and tokens.
// NOTE: Only VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are used here.
// NEVER expose SUPABASE_SERVICE_ROLE_KEY to the frontend!
// ==============================================================================

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder-project.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key';

export const isSupabaseConfigured = Boolean(
  import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY
);

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: window.localStorage
  }
});
