import reflex as rx

REPORTING_MIGRATION_SCRIPT = """
-- === Phase 1: Reporting Core Tables ===

-- Create the 'reports' table to store report metadata
CREATE TABLE IF NOT EXISTS public.reports (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    creator_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    report_type TEXT NOT NULL CHECK (report_type IN ('vulnerability', 'trend', 'compliance', 'executive')),
    filters JSONB,
    shared_with JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    last_accessed_at TIMESTAMPTZ
);
COMMENT ON TABLE public.reports IS 'Stores metadata for all generated reports, with organization-level isolation.';

-- Create 'report_cves' junction table
CREATE TABLE IF NOT EXISTS public.report_cves (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    report_id BIGINT NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    cve_id TEXT NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    added_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    notes TEXT,
    priority_override TEXT CHECK (priority_override IN ('critical', 'high', 'medium', 'low')),
    status TEXT DEFAULT 'new' NOT NULL CHECK (status IN ('new', 'reviewing', 'resolved', 'ignored')),
    UNIQUE(report_id, cve_id)
);
COMMENT ON TABLE public.report_cves IS 'Links reports to specific CVEs, with additional context.';

-- Create 'report_exports' table for tracking export history
CREATE TABLE IF NOT EXISTS public.report_exports (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    report_id BIGINT NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    exported_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    format TEXT NOT NULL CHECK (format IN ('csv', 'json', 'excel', 'pdf', 'jira', 'servicenow', 'slack')),
    exported_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    file_size_bytes INTEGER,
    download_count INTEGER DEFAULT 0 NOT NULL,
    download_url TEXT,
    url_expires_at TIMESTAMPTZ,
    export_parameters JSONB
);
COMMENT ON TABLE public.report_exports IS 'Tracks history and analytics of report exports.';

-- Create 'report_shares' table for collaboration
CREATE TABLE IF NOT EXISTS public.report_shares (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    report_id BIGINT NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    shared_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    shared_with_user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    shared_with_email TEXT,
    share_type TEXT NOT NULL CHECK (share_type IN ('view', 'edit', 'comment')),
    shared_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    access_token TEXT UNIQUE,
    access_count INTEGER DEFAULT 0 NOT NULL,
    last_accessed_at TIMESTAMPTZ
);
COMMENT ON TABLE public.report_shares IS 'Manages sharing permissions and access for reports.';

-- Create 'report_audit_log' for a comprehensive audit trail
CREATE TABLE IF NOT EXISTS public.report_audit_log (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    report_id BIGINT REFERENCES public.reports(id) ON DELETE SET NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL CHECK (action IN ('created', 'updated', 'deleted', 'exported', 'shared', 'accessed')),
    action_details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
COMMENT ON TABLE public.report_audit_log IS 'Logs all significant actions performed on reports for auditing purposes.';


-- === Phase 2: RLS Policies for Multi-Tenancy ===

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_cves ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies for 'reports'
CREATE POLICY "Admins have full access to reports" ON public.reports FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage reports in their own organization" ON public.reports FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );
CREATE POLICY "Users can view reports shared with them" ON public.reports FOR SELECT
    USING ( id IN (SELECT report_id FROM public.report_shares WHERE shared_with_user_id = auth.uid()) );

-- RLS Policies for 'report_cves'
CREATE POLICY "Admins have full access to report_cves" ON public.report_cves FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage report_cves in their organization" ON public.report_cves FOR ALL
    USING ( report_id IN (SELECT id FROM public.reports WHERE organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid())) );

-- RLS Policies for the rest of the tables follow a similar pattern...
CREATE POLICY "Admins have full access to report_exports" ON public.report_exports FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage report_exports in their organization" ON public.report_exports FOR ALL USING ( report_id IN (SELECT id FROM public.reports WHERE organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid())) );

CREATE POLICY "Admins have full access to report_shares" ON public.report_shares FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can manage report_shares in their organization" ON public.report_shares FOR ALL USING ( report_id IN (SELECT id FROM public.reports WHERE organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid())) );

CREATE POLICY "Admins have full access to report_audit_log" ON public.report_audit_log FOR ALL USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );
CREATE POLICY "Users can see audit logs for their organization" ON public.report_audit_log FOR SELECT USING ( report_id IN (SELECT id FROM public.reports WHERE organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid())) );


-- === Phase 3: Indexes for Performance ===

CREATE INDEX IF NOT EXISTS idx_reports_organization_id_created_at ON public.reports(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_creator_id ON public.reports(creator_id);
CREATE INDEX IF NOT EXISTS idx_reports_report_type ON public.reports(report_type);

CREATE INDEX IF NOT EXISTS idx_report_cves_report_id ON public.report_cves(report_id);
CREATE INDEX IF NOT EXISTS idx_report_cves_cve_id ON public.report_cves(cve_id);
CREATE INDEX IF NOT EXISTS idx_report_cves_status ON public.report_cves(status);

CREATE INDEX IF NOT EXISTS idx_report_exports_report_id_exported_at ON public.report_exports(report_id, exported_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_exports_exported_by ON public.report_exports(exported_by);

CREATE INDEX IF NOT EXISTS idx_report_shares_report_id ON public.report_shares(report_id);
CREATE INDEX IF NOT EXISTS idx_report_shares_shared_with_user_id ON public.report_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_report_shares_access_token ON public.report_shares(access_token);

CREATE INDEX IF NOT EXISTS idx_report_audit_log_report_id_timestamp ON public.report_audit_log(report_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_report_audit_log_user_id ON public.report_audit_log(user_id);


-- === Phase 4: Triggers for Automation ===

-- Trigger to automatically update 'updated_at' timestamp on reports table
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_report_update
    BEFORE UPDATE ON public.reports
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger to create audit log entries
CREATE OR REPLACE FUNCTION public.log_report_changes()
RETURNS TRIGGER AS $$
DECLARE
    audit_details JSONB;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        audit_details = jsonb_build_object('new_data', to_jsonb(NEW));
        INSERT INTO public.report_audit_log (report_id, user_id, action, action_details)
        VALUES (NEW.id, NEW.creator_id, 'created', audit_details);
    ELSIF (TG_OP = 'UPDATE') THEN
        audit_details = jsonb_build_object('old_data', to_jsonb(OLD), 'new_data', to_jsonb(NEW));
        INSERT INTO public.report_audit_log (report_id, user_id, action, action_details)
        VALUES (NEW.id, auth.uid(), 'updated', audit_details);
    ELSIF (TG_OP = 'DELETE') THEN
        audit_details = jsonb_build_object('old_data', to_jsonb(OLD));
        INSERT INTO public.report_audit_log (report_id, user_id, action, action_details)
        VALUES (OLD.id, auth.uid(), 'deleted', audit_details);
    END IF;
    RETURN NULL; -- result is ignored since this is an AFTER trigger
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER report_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.reports
    FOR EACH ROW
    EXECUTE FUNCTION public.log_report_changes();


-- === Final Grant Statements ===
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

SELECT 'SUCCESS: Enterprise Reporting schema has been applied.';

"""


def get_reporting_migration_script() -> str:
    return REPORTING_MIGRATION_SCRIPT