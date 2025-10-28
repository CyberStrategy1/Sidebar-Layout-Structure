import reflex as rx

REMEDIATION_MIGRATION_SCRIPT = """
-- === Phase 5A: Event Bus & Trigger Infrastructure ===

CREATE TABLE IF NOT EXISTS public.remediation_events (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    source TEXT NOT NULL, -- 'siem', 'exploit_validation', 'compliance_scan'
    trigger_payload JSONB NOT NULL,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'retry')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0
);
COMMENT ON TABLE public.remediation_events IS 'Stores events that trigger remediation workflows.';

ALTER TABLE public.remediation_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage remediation events in their org" ON public.remediation_events FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 5B: Remediation Engine & Decision Logic ===

CREATE TABLE IF NOT EXISTS public.remediation_playbooks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    trigger_conditions JSONB NOT NULL,
    action_sequence JSONB NOT NULL,
    requires_approval BOOLEAN DEFAULT FALSE,
    blast_radius_limit INTEGER DEFAULT 10,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, name, version)
);
COMMENT ON TABLE public.remediation_playbooks IS 'Stores versioned, user-defined remediation playbooks.';

ALTER TABLE public.remediation_playbooks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage playbooks in their org" ON public.remediation_playbooks FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE IF NOT EXISTS public.remediation_actions (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id BIGINT REFERENCES public.remediation_events(id) ON DELETE CASCADE,
    playbook_id BIGINT REFERENCES public.remediation_playbooks(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL,
    target_assets TEXT[], -- Hostnames, IPs, CVE IDs
    pre_state_snapshot JSONB,
    action_payload JSONB NOT NULL,
    execution_status TEXT DEFAULT 'pending' CHECK (execution_status IN ('pending', 'approved', 'executing', 'completed', 'failed', 'rolled_back')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    executed_by_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    execution_logs TEXT,
    error_message TEXT
);
COMMENT ON TABLE public.remediation_actions IS 'Tracks individual remediation actions executed by playbooks.';

ALTER TABLE public.remediation_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage actions in their org" ON public.remediation_actions FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 5C: Verification Engine & Continuous Validation ===

CREATE TABLE public.verification_results (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    remediation_action_id BIGINT NOT NULL REFERENCES public.remediation_actions(id) ON DELETE CASCADE,
    verification_method TEXT NOT NULL,
    verification_status TEXT NOT NULL CHECK (verification_status IN ('pending', 'in_progress', 'passed', 'failed', 'inconclusive')),
    confidence_score NUMERIC(3,2),
    evidence_artifacts JSONB,
    before_state JSONB,
    after_state JSONB,
    verification_logs TEXT,
    verified_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.verification_results IS 'Stores the outcome of post-remediation verification checks.';

ALTER TABLE public.verification_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage verification results in their org" ON public.verification_results FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE public.verification_evidence (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    verification_result_id BIGINT NOT NULL REFERENCES public.verification_results(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    artifact_url TEXT,
    artifact_data JSONB,
    checksum TEXT,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    is_immutable BOOLEAN DEFAULT TRUE
);
COMMENT ON TABLE public.verification_evidence IS 'Stores immutable evidence artifacts for compliance and auditing.';

ALTER TABLE public.verification_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage verification evidence in their org" ON public.verification_evidence FOR ALL
    USING ( (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- === Phase 5E: AI Optimization & Adaptive Learning ===

CREATE TABLE public.remediation_outcomes (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    playbook_id BIGINT REFERENCES public.remediation_playbooks(id) ON DELETE SET NULL,
    remediation_action_id BIGINT REFERENCES public.remediation_actions(id) ON DELETE CASCADE,
    was_successful BOOLEAN NOT NULL,
    verification_confidence NUMERIC(3,2),
    execution_time_seconds INTEGER,
    failure_reason TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.remediation_outcomes IS 'Tracks the historical success or failure of remediation actions to feed the optimization engine.';

ALTER TABLE public.remediation_outcomes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage remediation outcomes in their org" ON public.remediation_outcomes FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE public.playbook_optimization_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    playbook_id BIGINT NOT NULL REFERENCES public.remediation_playbooks(id) ON DELETE CASCADE,
    optimization_type TEXT NOT NULL, -- e.g., 'adjust_blast_radius', 'add_condition'
    previous_config JSONB,
    new_config JSONB,
    reasoning TEXT, -- AI-generated reason for the change
    applied_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.playbook_optimization_log IS 'Logs all automated adjustments made to playbooks by the AI optimization engine.';

ALTER TABLE public.playbook_optimization_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view playbook optimization logs in their org" ON public.playbook_optimization_log FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Indexes for Performance ===
CREATE INDEX IF NOT EXISTS idx_rem_events_org_status ON public.remediation_events(organization_id, processing_status);
CREATE INDEX IF NOT EXISTS idx_rem_actions_correlation ON public.remediation_actions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_ver_results_action ON public.verification_results(remediation_action_id);
CREATE INDEX IF NOT EXISTS idx_rem_outcomes_playbook ON public.remediation_outcomes(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_opt_log_playbook ON public.playbook_optimization_log(playbook_id);


-- === Final Grant Statements ===
GRANT ALL ON public.remediation_events TO authenticated;
GRANT ALL ON SEQUENCE remediation_events_id_seq TO authenticated;
GRANT ALL ON public.remediation_playbooks TO authenticated;
GRANT ALL ON SEQUENCE remediation_playbooks_id_seq TO authenticated;
GRANT ALL ON public.remediation_actions TO authenticated;
GRANT ALL ON SEQUENCE remediation_actions_id_seq TO authenticated;
GRANT ALL ON public.verification_results TO authenticated;
GRANT ALL ON SEQUENCE verification_results_id_seq TO authenticated;
GRANT ALL ON public.verification_evidence TO authenticated;
GRANT ALL ON SEQUENCE verification_evidence_id_seq TO authenticated;
GRANT ALL ON public.remediation_outcomes TO authenticated;
GRANT ALL ON SEQUENCE remediation_outcomes_id_seq TO authenticated;
GRANT ALL ON public.playbook_optimization_log TO authenticated;
GRANT ALL ON SEQUENCE playbook_optimization_log_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 5 Automated Remediation schema has been applied.';
"""


def get_remediation_migration_script() -> str:
    return REMEDIATION_MIGRATION_SCRIPT


import reflex as rx

REMEDIATION_MIGRATION_SCRIPT = """
-- === Phase 5A: Event Bus & Trigger Infrastructure ===

CREATE TABLE IF NOT EXISTS public.remediation_events (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    source TEXT NOT NULL, -- 'siem', 'exploit_validation', 'compliance_scan'
    trigger_payload JSONB NOT NULL,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'retry')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0
);
COMMENT ON TABLE public.remediation_events IS 'Stores events that trigger remediation workflows.';

ALTER TABLE public.remediation_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage remediation events in their org" ON public.remediation_events FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 5B: Remediation Engine & Decision Logic ===

CREATE TABLE IF NOT EXISTS public.remediation_playbooks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    trigger_conditions JSONB NOT NULL,
    action_sequence JSONB NOT NULL,
    requires_approval BOOLEAN DEFAULT FALSE,
    blast_radius_limit INTEGER DEFAULT 10,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, name, version)
);
COMMENT ON TABLE public.remediation_playbooks IS 'Stores versioned, user-defined remediation playbooks.';

ALTER TABLE public.remediation_playbooks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage playbooks in their org" ON public.remediation_playbooks FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE IF NOT EXISTS public.remediation_actions (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id BIGINT REFERENCES public.remediation_events(id) ON DELETE CASCADE,
    playbook_id BIGINT REFERENCES public.remediation_playbooks(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL,
    target_assets TEXT[], -- Hostnames, IPs, CVE IDs
    pre_state_snapshot JSONB,
    action_payload JSONB NOT NULL,
    execution_status TEXT DEFAULT 'pending' CHECK (execution_status IN ('pending', 'approved', 'executing', 'completed', 'failed', 'rolled_back')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    executed_by_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    execution_logs TEXT,
    error_message TEXT
);
COMMENT ON TABLE public.remediation_actions IS 'Tracks individual remediation actions executed by playbooks.';

ALTER TABLE public.remediation_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage actions in their org" ON public.remediation_actions FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 5C: Verification Engine & Continuous Validation ===

CREATE TABLE public.verification_results (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    correlation_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    remediation_action_id BIGINT NOT NULL REFERENCES public.remediation_actions(id) ON DELETE CASCADE,
    verification_method TEXT NOT NULL,
    verification_status TEXT NOT NULL CHECK (verification_status IN ('pending', 'in_progress', 'passed', 'failed', 'inconclusive')),
    confidence_score NUMERIC(3,2),
    evidence_artifacts JSONB,
    before_state JSONB,
    after_state JSONB,
    verification_logs TEXT,
    verified_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.verification_results IS 'Stores the outcome of post-remediation verification checks.';

ALTER TABLE public.verification_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage verification results in their org" ON public.verification_results FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE public.verification_evidence (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    verification_result_id BIGINT NOT NULL REFERENCES public.verification_results(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    artifact_url TEXT,
    artifact_data JSONB,
    checksum TEXT,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    is_immutable BOOLEAN DEFAULT TRUE
);
COMMENT ON TABLE public.verification_evidence IS 'Stores immutable evidence artifacts for compliance and auditing.';

ALTER TABLE public.verification_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage verification evidence in their org" ON public.verification_evidence FOR ALL
    USING ( (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- === Phase 5E: AI Optimization & Adaptive Learning ===

CREATE TABLE public.remediation_outcomes (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    playbook_id BIGINT REFERENCES public.remediation_playbooks(id) ON DELETE SET NULL,
    remediation_action_id BIGINT REFERENCES public.remediation_actions(id) ON DELETE CASCADE,
    was_successful BOOLEAN NOT NULL,
    verification_confidence NUMERIC(3,2),
    execution_time_seconds INTEGER,
    failure_reason TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.remediation_outcomes IS 'Tracks the historical success or failure of remediation actions to feed the optimization engine.';

ALTER TABLE public.remediation_outcomes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage remediation outcomes in their org" ON public.remediation_outcomes FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


CREATE TABLE public.playbook_optimization_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    playbook_id BIGINT NOT NULL REFERENCES public.remediation_playbooks(id) ON DELETE CASCADE,
    optimization_type TEXT NOT NULL, -- e.g., 'adjust_blast_radius', 'add_condition'
    previous_config JSONB,
    new_config JSONB,
    reasoning TEXT, -- AI-generated reason for the change
    applied_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.playbook_optimization_log IS 'Logs all automated adjustments made to playbooks by the AI optimization engine.';

ALTER TABLE public.playbook_optimization_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view playbook optimization logs in their org" ON public.playbook_optimization_log FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Indexes for Performance ===
CREATE INDEX IF NOT EXISTS idx_rem_events_org_status ON public.remediation_events(organization_id, processing_status);
CREATE INDEX IF NOT EXISTS idx_rem_actions_correlation ON public.remediation_actions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_ver_results_action ON public.verification_results(remediation_action_id);
CREATE INDEX IF NOT EXISTS idx_rem_outcomes_playbook ON public.remediation_outcomes(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_opt_log_playbook ON public.playbook_optimization_log(playbook_id);


-- === Final Grant Statements ===
GRANT ALL ON public.remediation_events TO authenticated;
GRANT ALL ON SEQUENCE remediation_events_id_seq TO authenticated;
GRANT ALL ON public.remediation_playbooks TO authenticated;
GRANT ALL ON SEQUENCE remediation_playbooks_id_seq TO authenticated;
GRANT ALL ON public.remediation_actions TO authenticated;
GRANT ALL ON SEQUENCE remediation_actions_id_seq TO authenticated;
GRANT ALL ON public.verification_results TO authenticated;
GRANT ALL ON SEQUENCE verification_results_id_seq TO authenticated;
GRANT ALL ON public.verification_evidence TO authenticated;
GRANT ALL ON SEQUENCE verification_evidence_id_seq TO authenticated;
GRANT ALL ON public.remediation_outcomes TO authenticated;
GRANT ALL ON SEQUENCE remediation_outcomes_id_seq TO authenticated;
GRANT ALL ON public.playbook_optimization_log TO authenticated;
GRANT ALL ON SEQUENCE playbook_optimization_log_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 5 Automated Remediation schema has been applied.';
"""


def get_remediation_migration_script() -> str:
    return REMEDIATION_MIGRATION_SCRIPT