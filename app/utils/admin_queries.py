"""
This script contains the necessary SQL commands to set up the multi-tenant database schema
for the Aperture Enterprise Admin Console. Run these commands in your Supabase SQL Editor.
"""

SQL_MIGRATION_SCRIPT = """
-- === Phase 1: Create Core Tables ===

-- Create the api_health_log table for monitoring external API calls
CREATE TABLE IF NOT EXISTS public.api_health_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    api_name TEXT NOT NULL,
    endpoint TEXT,
    status TEXT NOT NULL CHECK (status IN ('success', 'failure')),
    status_code INTEGER,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT,
    records_fetched INTEGER
);
COMMENT ON TABLE public.api_health_log IS 'Logs health and performance of external API calls.';


-- Create the organizations table to hold customer data
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    status TEXT DEFAULT 'active' NOT NULL CHECK (status IN ('active', 'inactive', 'trialing')),
    tech_stack_count INTEGER DEFAULT 0 NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'canceled', 'past_due'))
);
COMMENT ON TABLE public.organizations IS 'Stores information about customer organizations.';

-- Create the users table to link Supabase auth users to organizations and roles
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'analyst' NOT NULL CHECK (role IN ('admin', 'analyst')),
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
COMMENT ON TABLE public.users IS 'Stores application-specific user data, including roles and organization linkage.';

-- Create a table for tracked CVEs per organization
CREATE TABLE IF NOT EXISTS public.tracked_cves (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    tracked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(cve_id, organization_id)
);
COMMENT ON TABLE public.tracked_cves IS 'Tracks unique CVEs monitored by each organization.';


-- === Phase 2: Create Functions and Triggers ===

-- Function to create a user profile upon new user sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Default new users to an 'analyst' role. Organization can be assigned later.
    INSERT INTO public.users (id, email, role)
    VALUES (new.id, new.email, 'analyst');
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to execute the function after a new user is created in auth.users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RPC function to get average tech stack size
CREATE OR REPLACE FUNCTION public.get_average_tech_stack_size()
RETURNS NUMERIC AS $$
BEGIN
    RETURN (
        SELECT COALESCE(AVG(tech_stack_count), 0)
        FROM public.organizations
        WHERE status = 'active'
    );
END;
$$ LANGUAGE plpgsql;


-- === Phase 3: Enable Row-Level Security (RLS) ===

-- Enable RLS on all relevant tables
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tracked_cves ENABLE ROW LEVEL SECURITY;

-- Policies for 'organizations' table
CREATE POLICY "Allow admin full access to organizations" ON public.organizations
    FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Allow users to see their own organization" ON public.organizations
    FOR SELECT USING ( id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- Policies for 'users' table
CREATE POLICY "Allow admin full access to users" ON public.users
    FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Allow users to see themselves" ON public.users
    FOR SELECT USING ( id = auth.uid() );


-- Policies for 'tracked_cves' table
CREATE POLICY "Allow admin full access to tracked_cves" ON public.tracked_cves
    FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Allow users to see their own tracked CVEs" ON public.tracked_cves
    FOR SELECT USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- Create vulnerabilities table for storing identified gaps
CREATE TABLE IF NOT EXISTS public.vulnerabilities (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    description TEXT,
    published_date TIMESTAMPTZ,
    last_modified TIMESTAMPTZ,
    missing_cvss BOOLEAN DEFAULT FALSE,
    missing_cpe BOOLEAN DEFAULT FALSE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    discovered_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    time_gap_days INTEGER,
    cvss_gap_score NUMERIC(4, 2),
    cpe_gap_score NUMERIC(4, 2),
    reference_quality_score NUMERIC(4, 2),
    overall_gap_severity NUMERIC(4, 2),
    affects_org_stack BOOLEAN DEFAULT FALSE,
    stack_match_confidence INTEGER,
    enrichment_velocity NUMERIC(6, 2),
    estimated_enrichment_date TIMESTAMPTZ,
    vuln_status TEXT,
    source_identifier TEXT,
    cisa_exploit_add DATE,
    cisa_action_due DATE,
    cisa_required_action TEXT,
    cisa_vuln_name TEXT,
    cve_tags TEXT[],
    weaknesses TEXT[],
    evaluator_comment TEXT,
    evaluator_solution TEXT,
    evaluator_impact TEXT,
    days_awaiting_analysis INTEGER,
    UNIQUE(cve_id, organization_id)
);
COMMENT ON TABLE public.vulnerabilities IS 'Stores vulnerabilities identified as gaps (missing CPE/CVSS).';

-- Enable RLS for vulnerabilities table
ALTER TABLE public.vulnerabilities ENABLE ROW LEVEL SECURITY;

-- Policies for 'vulnerabilities' table
CREATE POLICY "Allow admin full access to vulnerabilities" ON public.vulnerabilities
    FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Allow users to manage their own vulnerabilities" ON public.vulnerabilities
    FOR ALL USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Final Grant Statements ===

-- Grant usage on the public schema to the authenticated role
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant specific permissions for anon role (for login and health logging)
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT ON public.users TO anon;
GRANT INSERT ON public.api_health_log TO anon;
GRANT USAGE ON SEQUENCE api_health_log_id_seq TO anon;


-- === Phase 4: Engine Monitoring ===

-- Create table to track engine runs
CREATE TABLE IF NOT EXISTS public.engine_runs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    run_started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    run_completed_at TIMESTAMPTZ,
    records_found INTEGER,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE
);
COMMENT ON TABLE public.engine_runs IS 'Tracks the execution history of the gap analysis engine.';

-- Enable RLS for engine_runs table
ALTER TABLE public.engine_runs ENABLE ROW LEVEL SECURITY;

-- Policies for 'engine_runs' table
CREATE POLICY "Allow admin full access to engine_runs" ON public.engine_runs
    FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

CREATE POLICY "Allow users to see their own engine runs" ON public.engine_runs
    FOR ALL USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- Grant authenticated users access to the new table
GRANT ALL ON public.engine_runs TO authenticated;
GRANT ALL ON SEQUENCE engine_runs_id_seq TO authenticated;


-- === Phase 5: LLM & AI Analysis Tables ===

-- Create ai_provider_keys to store encrypted API keys per organization
CREATE TABLE IF NOT EXISTS public.ai_provider_keys (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('openai', 'groq', 'gemini', 'anthropic')),
    encrypted_api_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    UNIQUE(organization_id, provider)
);
COMMENT ON TABLE public.ai_provider_keys IS 'Stores encrypted API keys for third-party AI providers, scoped to organizations.';

-- Add ai_credits column to organizations table
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS ai_credits INTEGER DEFAULT 0 NOT NULL;

-- Create llm_analysis_cache for storing recent analysis results
CREATE TABLE IF NOT EXISTS public.llm_analysis_cache (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    analysis_result JSONB NOT NULL,
    tokens_used INTEGER,
    cost_credits INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(cve_id, organization_id)
);
COMMENT ON TABLE public.llm_analysis_cache IS 'Caches LLM analysis results to reduce cost and latency.';

-- Create llm_usage_log for tracking AI analysis usage and cost
CREATE TABLE IF NOT EXISTS public.llm_usage_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    cve_id TEXT,
    provider TEXT,
    model TEXT,
    tokens_used INTEGER,
    credits_charged INTEGER,
    analysis_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
COMMENT ON TABLE public.llm_usage_log IS 'Logs all LLM analysis events for billing and auditing purposes.';

-- Enable RLS for new AI tables
ALTER TABLE public.ai_provider_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_analysis_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_usage_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage their own org API keys" ON public.ai_provider_keys FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage their own org cache" ON public.llm_analysis_cache FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view their own org usage logs" ON public.llm_usage_log FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Admins have full access to AI tables" ON public.ai_provider_keys FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Admins have full access to AI cache" ON public.llm_analysis_cache FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Admins have full access to AI usage logs" ON public.llm_usage_log FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );


-- Grant permissions for new tables
GRANT ALL ON public.ai_provider_keys TO authenticated;
GRANT ALL ON SEQUENCE ai_provider_keys_id_seq TO authenticated;

GRANT ALL ON public.llm_analysis_cache TO authenticated;
GRANT ALL ON SEQUENCE llm_analysis_cache_id_seq TO authenticated;

GRANT ALL ON public.llm_usage_log TO authenticated;
GRANT ALL ON SEQUENCE llm_usage_log_id_seq TO authenticated;


SELECT 'SUCCESS: Aperture multi-tenant schema has been applied.';

"""


def get_migration_script() -> str:
    return SQL_MIGRATION_SCRIPT