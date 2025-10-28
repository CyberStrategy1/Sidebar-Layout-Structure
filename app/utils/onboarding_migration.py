import reflex as rx

ONBOARDING_MIGRATION_SCRIPT = """
-- Track onboarding completion status
CREATE TABLE IF NOT EXISTS public.onboarding_progress (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    current_step INTEGER DEFAULT 1,
    steps_completed INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    skipped BOOLEAN DEFAULT FALSE,
    temp_data JSONB,
    UNIQUE(user_id)
);

-- Track user profiles (extended from basic auth)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    job_title TEXT,
    department TEXT,
    phone TEXT,
    avatar_url TEXT,
    timezone TEXT DEFAULT 'UTC',
    notification_preferences JSONB DEFAULT '{"email": true, "slack": false}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create organizations_context table to store security context
CREATE TABLE IF NOT EXISTS public.organizations_context (
    organization_id UUID PRIMARY KEY REFERENCES public.organizations(id) ON DELETE CASCADE,
    cloud_provider TEXT,
    ip_ranges TEXT,
    sbom_file TEXT,
    deployment_environment TEXT,
    industry_vertical TEXT,
    compliance_requirements TEXT[],
    critical_assets TEXT,
    risk_appetite TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.organizations_context IS 'Stores security and asset context for each organization to enhance inference.';

ALTER TABLE public.organizations_context ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage context for their own org" ON public.organizations_context FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.members WHERE user_id = auth.uid() AND role = 'owner') );

GRANT ALL ON public.organizations_context TO authenticated;
GRANT ALL ON SEQUENCE organizations_context_organization_id_seq TO authenticated; 

-- Track organizations created during onboarding
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS domain TEXT;
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS company_size TEXT;
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS industry TEXT;
ALTER TABLE public.organizations ADD COLUMN IF NOT EXISTS tech_stack TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Members table to link users to organizations
CREATE TABLE IF NOT EXISTS public.members (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- RLS Policies
ALTER TABLE public.onboarding_progress ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own onboarding progress" ON public.onboarding_progress FOR ALL
    USING ( user_id = auth.uid() );

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own profile" ON public.user_profiles FOR ALL
    USING ( user_id = auth.uid() );

ALTER TABLE public.members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own memberships" ON public.members FOR SELECT
    USING ( user_id = auth.uid() );
CREATE POLICY "Organization owners can manage members" ON public.members FOR ALL
    USING ( organization_id IN (SELECT organization_id FROM public.members WHERE user_id = auth.uid() AND role = 'owner') );


-- Function to create a user profile upon new user sign-up
-- This replaces the old handle_new_user function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

CREATE OR REPLACE FUNCTION public.handle_new_user_with_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- Create a user profile
    INSERT INTO public.user_profiles (user_id, full_name)
    VALUES (new.id, new.raw_user_meta_data->>'full_name');

    -- Initialize onboarding progress
    INSERT INTO public.onboarding_progress(user_id)
    VALUES(new.id);

    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to execute the function after a new user is created in auth.users
CREATE TRIGGER on_auth_user_created_with_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_with_profile();

-- Grant permissions for new tables
GRANT ALL ON public.onboarding_progress TO authenticated;
GRANT ALL ON SEQUENCE onboarding_progress_id_seq TO authenticated;

GRANT ALL ON public.user_profiles TO authenticated;

GRANT ALL ON public.members TO authenticated;
GRANT ALL ON SEQUENCE members_id_seq TO authenticated;

"""


def get_onboarding_migration_script() -> str:
    return ONBOARDING_MIGRATION_SCRIPT