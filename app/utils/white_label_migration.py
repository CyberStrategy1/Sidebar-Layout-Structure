import reflex as rx

WHITE_LABEL_MIGRATION_SCRIPT = """
-- === Phase 1: White-Label Configuration Table ===

CREATE TABLE IF NOT EXISTS public.white_label_configs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Branding
    company_name TEXT,
    dashboard_title TEXT,
    logo_url TEXT,
    favicon_url TEXT,

    -- Theming
    primary_color TEXT,
    secondary_color TEXT,
    accent_color TEXT,

    -- Customization
    custom_domain TEXT,
    footer_text TEXT,
    custom_css TEXT,

    -- Links & Support
    support_url TEXT,
    support_email TEXT,
    terms_url TEXT,
    privacy_url TEXT,

    -- Email Branding
    email_from_name TEXT,
    email_logo_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.white_label_configs IS 'Stores white-label branding and theming configurations for enterprise organizations.';

-- === Phase 2: RLS Policy ===

ALTER TABLE public.white_label_configs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage white-label config in their org" ON public.white_label_configs FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Admins have full access to white-label configs" ON public.white_label_configs FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

-- === Phase 3: Index for Performance ===

CREATE INDEX IF NOT EXISTS idx_white_label_configs_organization_id ON public.white_label_configs(organization_id);

-- === Phase 4: Trigger for 'updated_at' timestamp ===

CREATE OR REPLACE FUNCTION public.update_white_label_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_white_label_config_update
    BEFORE UPDATE ON public.white_label_configs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_white_label_updated_at();

-- === Final Grant Statements ===

GRANT ALL ON public.white_label_configs TO authenticated;
GRANT ALL ON SEQUENCE white_label_configs_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 2I White-Label schema has been applied.';

"""


def get_white_label_migration_script() -> str:
    """Returns the SQL migration script for the white-label schema."""
    return WHITE_LABEL_MIGRATION_SCRIPT