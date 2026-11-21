// Public settings of the Supabase project (dashboard -> Project Settings -> API Keys).
// The publishable key is meant to be public: row level security in the database decides what each user can see.
// Never put the secret key here.
export const SUPABASE_URL = "https://nivzkojlyzbtytqdxqze.supabase.co";
export const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_nxxFVTRURO7B4uLN31d1qg_DCURdEVL";

// Must match LOGIN_EMAIL_DOMAIN in src/xmas_wichtel/repository.py.
export const LOGIN_EMAIL_DOMAIN = "wichtel.local";
