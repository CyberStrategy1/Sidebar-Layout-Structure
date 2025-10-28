import reflex as rx

RISK_FRAMEWORK_MIGRATION_SCRIPT = """
-- === Phase 1: Risk Framework Core Tables ===

-- Create the 'framework_scores' table to store multi-framework scoring data
CREATE TABLE IF NOT EXISTS public.framework_scores (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    cvss_v3_score NUMERIC(3,1),
    cvss_v3_vector TEXT,
    epss_score NUMERIC(5,4),
    epss_percentile NUMERIC(5,4),
    is_kev BOOLEAN DEFAULT FALSE,
    kev_date_added DATE,
    kev_due_date DATE,
    ssvc_decision TEXT CHECK (ssvc_decision IN ('Track', 'Track*', 'Attend', 'Act')),
    lev_score NUMERIC(5,4),
    universal_risk_score NUMERIC(5,2),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    -- Phase 2 Enhancements
    vpr_score NUMERIC(3,1),                 -- Tenable VPR (0-10)
    pxs_score NUMERIC(3,1),                 -- Picus PXS (0-10)
    vex_status TEXT,                        -- Fixed/Affected/NotAffected/Investigating
    vex_source TEXT,
    microsoft_ei INTEGER,                   -- MS Exploitability Index (0-3)
    microsoft_ei_category TEXT,             -- Detected/MoreLikely/etc.
    rvss_score NUMERIC(3,1),                -- RVSS for robotics/IoT
    ml_exploitability NUMERIC(3,1),         -- ML-based prediction
    ssvc_rationale JSONB,                   -- Full decision tree path
    framework_agreement NUMERIC(3,2),         -- Cohen's Kappa (0-1)
    scoring_confidence NUMERIC(3,2),          -- Overall confidence (0-1)
    conflict_flags TEXT[],                  -- Array of detected conflicts
    recommended_action TEXT,
    action_rationale TEXT,
    UNIQUE(cve_id, organization_id)
);
COMMENT ON TABLE public.framework_scores IS 'Stores multi-framework vulnerability scores for each organization.';

-- Create 'api_keys' table for encrypted, per-organization API credentials
CREATE TABLE IF NOT EXISTS public.api_keys (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_type TEXT CHECK (key_type IN ('nvd', 'epss', 'kev', 'ssvc', 'vpr', 'pxs', 'openai', 'anthropic', 'groq', 'gemini')),
    is_active BOOLEAN DEFAULT TRUE,
    last_rotated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, key_name)
);
COMMENT ON TABLE public.api_keys IS 'Stores encrypted API keys for external services, scoped to organizations.';

-- Create 'scoring_configs' to allow per-org customization of the scoring engine
CREATE TABLE IF NOT EXISTS public.scoring_configs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE UNIQUE,
    weights JSONB DEFAULT '{{"cvss": 0.4, "epss": 0.3, "kev": 0.2, "ssvc": 0.1}}'::jsonb,
    enabled_frameworks TEXT[] DEFAULT ARRAY['cvss', 'epss', 'kev'],
    custom_rules JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.scoring_configs IS 'Configurable settings for the risk scoring engine for each organization.';

-- Create 'framework_recommendations' table to store engine-generated advice
CREATE TABLE IF NOT EXISTS public.framework_recommendations (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    recommendation_type TEXT CHECK (recommendation_type IN ('add_framework', 'adjust_weights', 'remove_framework')),
    framework_name TEXT,
    reasoning TEXT,
    confidence NUMERIC(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_dismissed BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE public.framework_recommendations IS 'Stores AI-generated recommendations for optimizing framework usage.';


-- === Phase 2: RLS Policies for Multi-Tenancy ===

ALTER TABLE public.framework_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scoring_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.framework_recommendations ENABLE ROW LEVEL SECURITY;

-- Policies for 'framework_scores'
CREATE POLICY "Admins have full access to framework_scores" ON public.framework_scores FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage framework_scores in their own organization" ON public.framework_scores FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- Policies for 'api_keys'
CREATE POLICY "Admins have full access to api_keys" ON public.api_keys FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage api_keys in their own organization" ON public.api_keys FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- Policies for 'scoring_configs'
CREATE POLICY "Admins have full access to scoring_configs" ON public.scoring_configs FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage scoring_configs in their own organization" ON public.scoring_configs FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- Policies for 'framework_recommendations'
CREATE POLICY "Admins have full access to framework_recommendations" ON public.framework_recommendations FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage framework_recommendations in their own organization" ON public.framework_recommendations FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 3: Indexes for Performance ===

CREATE INDEX IF NOT EXISTS idx_framework_scores_org_cve ON public.framework_scores(organization_id, cve_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org_type ON public.api_keys(organization_id, key_type);
CREATE INDEX IF NOT EXISTS idx_scoring_configs_org ON public.scoring_configs(organization_id);
CREATE INDEX IF NOT EXISTS idx_framework_recommendations_org_created ON public.framework_recommendations(organization_id, created_at DESC);

-- === Phase 4: Triggers and Functions ===

-- Trigger to auto-update 'updated_at' on scoring_configs
CREATE OR REPLACE FUNCTION public.update_scoring_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_scoring_configs_update
    BEFORE UPDATE ON public.scoring_configs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_scoring_configs_updated_at();

-- === Final Grant Statements ===
GRANT ALL ON public.framework_scores TO authenticated;
GRANT ALL ON SEQUENCE framework_scores_id_seq TO authenticated;

GRANT ALL ON public.api_keys TO authenticated;
GRANT ALL ON SEQUENCE api_keys_id_seq TO authenticated;

GRANT ALL ON public.scoring_configs TO authenticated;
GRANT ALL ON SEQUENCE scoring_configs_id_seq TO authenticated;

GRANT ALL ON public.framework_recommendations TO authenticated;
GRANT ALL ON SEQUENCE framework_recommendations_id_seq TO authenticated;

SELECT 'SUCCESS: Risk Intelligence Framework schema has been applied.';

"""


def get_risk_framework_migration_script() -> str:
    return RISK_FRAMEWORK_MIGRATION_SCRIPT