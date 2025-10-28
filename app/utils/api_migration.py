import reflex as rx

API_MIGRATION_SCRIPT = """
-- === Phase 1: API Access Tables ===

-- Create the 'api_keys' table to store and manage client API keys
CREATE TABLE IF NOT EXISTS public.api_keys (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    key_prefix TEXT NOT NULL, -- e.g., 'apk'
    key_hash TEXT NOT NULL,   -- Securely hashed version of the key
    permissions JSONB DEFAULT '["*"]'::jsonb, -- Granular permissions
    rate_limit INTEGER DEFAULT 1000, -- Requests per hour
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(organization_id, key_name)
);
COMMENT ON TABLE public.api_keys IS 'Stores hashed API keys for programmatic access.';

-- Create 'api_usage_log' table to track all API requests
CREATE TABLE IF NOT EXISTS public.api_usage_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    api_key_id BIGINT REFERENCES public.api_keys(id) ON DELETE SET NULL,
    endpoint TEXT NOT NULL,
    http_method TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
COMMENT ON TABLE public.api_usage_log IS 'Logs all incoming requests made to the public API.';

-- === Phase 2: RLS Policies ===

ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage API keys in their own organization" ON public.api_keys FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view API usage logs for their own organization" ON public.api_usage_log FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- Admin access policies
CREATE POLICY "Admins have full access to api_keys" ON public.api_keys FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Admins have full access to api_usage_log" ON public.api_usage_log FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );


-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_api_keys_organization_id ON public.api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON public.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_usage_log_org_timestamp ON public.api_usage_log(organization_id, timestamp DESC);

-- === Final Grant Statements ===

GRANT ALL ON public.api_keys TO authenticated;
GRANT ALL ON SEQUENCE api_keys_id_seq TO authenticated;
GRANT ALL ON public.api_usage_log TO authenticated;
GRANT ALL ON SEQUENCE api_usage_log_id_seq TO authenticated;

SELECT 'SUCCESS: API Access Layer schema has been applied.';

"""


def get_api_migration_script() -> str:
    """Returns the SQL migration script for the API access layer."""
    return API_MIGRATION_SCRIPT