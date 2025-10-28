import reflex as rx

ALERTING_MIGRATION_SCRIPT = """
-- === Phase 1: Alerting Core Tables ===

-- Create 'alert_channels' to store encrypted integration credentials
CREATE TABLE IF NOT EXISTS public.alert_channels (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('slack', 'teams', 'pagerduty', 'email', 'sms', 'webhook')),
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    encrypted_credentials TEXT NOT NULL, -- For webhook URLs, API keys, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, name)
);
COMMENT ON TABLE public.alert_channels IS 'Stores configuration and encrypted credentials for alert channels.';

-- Create 'escalation_policies' to define alert routing rules
CREATE TABLE IF NOT EXISTS public.escalation_policies (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    severity_level TEXT NOT NULL CHECK (severity_level IN ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY')),
    delay_minutes INTEGER NOT NULL DEFAULT 0,
    channels BIGINT[] NOT NULL, -- Array of alert_channel IDs
    UNIQUE(organization_id, name, severity_level, delay_minutes)
);
COMMENT ON TABLE public.escalation_policies IS 'Defines multi-step escalation rules for different alert severities.';

-- Create 'on_call_schedules' for recipient management
CREATE TABLE IF NOT EXISTS public.on_call_schedules (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    user_ids UUID[], -- Array of user IDs from user_profiles
    rotation_type TEXT CHECK (rotation_type IN ('daily', 'weekly', 'custom')),
    rotation_start_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, name)
);
COMMENT ON TABLE public.on_call_schedules IS 'Manages on-call rotations and schedules.';

-- Create 'alert_history' to log all alerts
CREATE TABLE IF NOT EXISTS public.alert_history (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    deduplication_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL,
    source TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'acknowledged', 'resolved', 'escalated')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    resolved_by UUID REFERENCES public.users(id) ON DELETE SET NULL
);
COMMENT ON TABLE public.alert_history IS 'Comprehensive log of all alerts, their status, and lifecycle.';

-- Create 'alert_suppressions' for maintenance windows
CREATE TABLE IF NOT EXISTS public.alert_suppressions (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    reason TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.alert_suppressions IS 'Defines maintenance windows or suppression rules to prevent alert fatigue.';

-- === Phase 2: RLS Policies ===

ALTER TABLE public.alert_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.escalation_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.on_call_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_suppressions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage alerting config in their org" ON public.alert_channels FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage escalation policies in their org" ON public.escalation_policies FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage on-call schedules in their org" ON public.on_call_schedules FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view and manage alerts in their org" ON public.alert_history FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage suppressions in their org" ON public.alert_suppressions FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_alert_history_org_status_created ON public.alert_history(organization_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_dedup_key ON public.alert_history(deduplication_key);


-- === Final Grant Statements ===

GRANT ALL ON public.alert_channels TO authenticated;
GRANT ALL ON SEQUENCE alert_channels_id_seq TO authenticated;

GRANT ALL ON public.escalation_policies TO authenticated;
GRANT ALL ON SEQUENCE escalation_policies_id_seq TO authenticated;

GRANT ALL ON public.on_call_schedules TO authenticated;
GRANT ALL ON SEQUENCE on_call_schedules_id_seq TO authenticated;

GRANT ALL ON public.alert_history TO authenticated;
GRANT ALL ON SEQUENCE alert_history_id_seq TO authenticated;

GRANT ALL ON public.alert_suppressions TO authenticated;
GRANT ALL ON SEQUENCE alert_suppressions_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 2I Advanced Alerting schema has been applied.';

"""


def get_alerting_migration_script() -> str:
    return ALERTING_MIGRATION_SCRIPT