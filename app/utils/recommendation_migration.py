import reflex as rx

RECOMMENDATION_MIGRATION_SCRIPT = """
-- === Phase 1: Recommendation Engine Tables ===

-- AI-Generated Recommendations
CREATE TABLE IF NOT EXISTS public.framework_recommendations (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN ('adjust_weights', 'enable_framework', 'disable_framework', 'change_provider')),
    details JSONB NOT NULL,
    reasoning TEXT NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL,
    impact_preview JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'applied', 'dismissed', 'ab_testing')),
    applied_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    feedback TEXT
);
COMMENT ON TABLE public.framework_recommendations IS 'Stores AI-generated recommendations for optimizing framework usage.';

-- Weight Change Audit Trail
CREATE TABLE IF NOT EXISTS public.weight_history (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    weights JSONB NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    change_reason TEXT NOT NULL CHECK (change_reason IN ('manual_update', 'recommendation_applied', 'ab_test_start', 'rollback')),
    recommendation_id BIGINT REFERENCES public.framework_recommendations(id) ON DELETE SET NULL,
    ab_test_id BIGINT
);
COMMENT ON TABLE public.weight_history IS 'Comprehensive audit trail for all scoring weight changes.';

-- A/B Testing Framework
CREATE TABLE IF NOT EXISTS public.ab_tests (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    recommendation_id BIGINT REFERENCES public.framework_recommendations(id) ON DELETE SET NULL,
    control_weights JSONB NOT NULL,
    variant_weights JSONB NOT NULL,
    start_date TIMESTAMPTZ DEFAULT NOW(),
    end_date TIMESTAMPTZ,
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'canceled')),
    results JSONB
);
COMMENT ON TABLE public.ab_tests IS 'Manages A/B tests for validating recommendation effectiveness.';

-- Framework Performance Metrics
CREATE TABLE IF NOT EXISTS public.framework_performance (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    framework TEXT NOT NULL,
    metric_date DATE NOT NULL,
    accuracy NUMERIC(5,4),
    precision NUMERIC(5,4),
    recall NUMERIC(5,4),
    true_positives INTEGER,
    false_positives INTEGER,
    true_negatives INTEGER,
    false_negatives INTEGER,
    UNIQUE(organization_id, framework, metric_date)
);
COMMENT ON TABLE public.framework_performance IS 'Tracks historical performance of each scoring framework for an organization.';


-- === Phase 2: RLS Policies ===

ALTER TABLE public.framework_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weight_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.framework_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own org recommendations" ON public.framework_recommendations FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view their own org weight history" ON public.weight_history FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage their own org A/B tests" ON public.ab_tests FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view their own org performance metrics" ON public.framework_performance FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 3: Indexes for Performance ===

CREATE INDEX IF NOT EXISTS idx_recs_org_status_created ON public.framework_recommendations(organization_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wh_org_changed_at ON public.weight_history(organization_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ab_org_status ON public.ab_tests(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_perf_org_framework_date ON public.framework_performance(organization_id, framework, metric_date DESC);


-- === Final Grant Statements ===

GRANT ALL ON public.framework_recommendations TO authenticated;
GRANT ALL ON SEQUENCE framework_recommendations_id_seq TO authenticated;
GRANT ALL ON public.weight_history TO authenticated;
GRANT ALL ON SEQUENCE weight_history_id_seq TO authenticated;
GRANT ALL ON public.ab_tests TO authenticated;
GRANT ALL ON SEQUENCE ab_tests_id_seq TO authenticated;
GRANT ALL ON public.framework_performance TO authenticated;
GRANT ALL ON SEQUENCE framework_performance_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 2G Framework Orchestration schema has been applied.';

"""


def get_recommendation_migration_script() -> str:
    """Returns the SQL migration script for the recommendation engine schema."""
    return RECOMMENDATION_MIGRATION_SCRIPT