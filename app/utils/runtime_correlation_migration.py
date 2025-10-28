import reflex as rx

RUNTIME_CORRELATION_MIGRATION_SCRIPT = """
-- === Phase 1: Integration & Runtime Evidence Tables ===

-- SIEM Integration Configurations
CREATE TABLE IF NOT EXISTS public.siem_integrations (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE UNIQUE,
    provider TEXT CHECK (provider IN ('splunk', 'sentinel', 'stellar_cyber', 'qradar', 'hunters_ai')),
    endpoint_url TEXT,
    encrypted_api_key TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    last_sync TIMESTAMPTZ,
    UNIQUE(organization_id, provider)
);
COMMENT ON TABLE public.siem_integrations IS 'Stores SIEM integration configurations for each organization.';

-- RMM Integration Configurations
CREATE TABLE IF NOT EXISTS public.rmm_integrations (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE UNIQUE,
    provider TEXT CHECK (provider IN ('ninjaone', 'datto', 'connectwise', 'manageengine', 'pulseway')),
    endpoint_url TEXT,
    encrypted_api_key TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    last_sync TIMESTAMPTZ,
    UNIQUE(organization_id, provider)
);
COMMENT ON TABLE public.rmm_integrations IS 'Stores RMM integration configurations for each organization.';

-- Runtime Evidence Table
CREATE TABLE IF NOT EXISTS public.runtime_evidence (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    finding_id BIGINT NOT NULL REFERENCES public.inference_findings(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    correlation_timestamp TIMESTAMPTZ DEFAULT NOW(),
    runtime_confirmed BOOLEAN NOT NULL,
    active_processes JSONB, -- [{'process_name', 'host', 'pid', 'start_time'}]
    affected_hosts TEXT[],
    siem_evidence JSONB, -- Raw SIEM query results
    rmm_evidence JSONB, -- Raw RMM telemetry
    true_risk_score NUMERIC(5,2),
    containment_priority TEXT CHECK (containment_priority IN ('immediate', 'high', 'medium', 'low')),
    containment_action_taken BOOLEAN DEFAULT FALSE,
    UNIQUE(finding_id)
);
COMMENT ON TABLE public.runtime_evidence IS 'Stores correlated runtime evidence for vulnerability findings.';

-- === Phase 2: RLS Policies ===

ALTER TABLE public.siem_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rmm_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.runtime_evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage SIEM integrations in their org" ON public.siem_integrations FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage RMM integrations in their org" ON public.rmm_integrations FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage runtime evidence in their org" ON public.runtime_evidence FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_runtime_evidence_finding_id ON public.runtime_evidence(finding_id);
CREATE INDEX IF NOT EXISTS idx_runtime_evidence_org_id ON public.runtime_evidence(organization_id);

-- === Final Grant Statements ===

GRANT ALL ON public.siem_integrations TO authenticated;
GRANT ALL ON SEQUENCE siem_integrations_id_seq TO authenticated;
GRANT ALL ON public.rmm_integrations TO authenticated;
GRANT ALL ON SEQUENCE rmm_integrations_id_seq TO authenticated;
GRANT ALL ON public.runtime_evidence TO authenticated;
GRANT ALL ON SEQUENCE runtime_evidence_id_seq TO authenticated;

SELECT 'SUCCESS: Runtime Correlation (SIEM/RMM) schema has been applied.';
"""


def get_runtime_correlation_migration_script() -> str:
    return RUNTIME_CORRELATION_MIGRATION_SCRIPT