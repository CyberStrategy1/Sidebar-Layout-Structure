import reflex as rx

VALIDATION_MIGRATION_SCRIPT = """
-- === Phase 1: Validation & Performance Tables ===

-- Create the 'validation_results' table to store ground truth comparisons
CREATE TABLE IF NOT EXISTS public.validation_results (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    framework TEXT NOT NULL,
    predicted_score NUMERIC(5,2) NOT NULL,
    ground_truth_score NUMERIC(5,2) NOT NULL,
    is_correct BOOLEAN,
    error_margin NUMERIC(5,2),
    validated_at TIMESTAMPTZ DEFAULT NOW(),
    validated_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    source TEXT -- e.g., 'manual_review', 'threat_intel_feed'
);
COMMENT ON TABLE public.validation_results IS 'Stores results of prediction vs. ground truth validations.';

-- Create 'framework_performance_metrics' to track accuracy over time
CREATE TABLE IF NOT EXISTS public.framework_performance_metrics (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    framework TEXT NOT NULL,
    accuracy NUMERIC(5,4),
    precision NUMERIC(5,4),
    recall NUMERIC(5,4),
    f1_score NUMERIC(5,4),
    true_positives INTEGER,
    false_positives INTEGER,
    true_negatives INTEGER,
    false_negatives INTEGER,
    UNIQUE(organization_id, metric_date, framework)
);
COMMENT ON TABLE public.framework_performance_metrics IS 'Tracks daily performance metrics for each scoring framework.';

-- Create 'auto_tuning_history' to log all automated weight adjustments
CREATE TABLE IF NOT EXISTS public.auto_tuning_history (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    framework TEXT NOT NULL,
    previous_weight NUMERIC(4,3),
    new_weight NUMERIC(4,3),
    triggering_metric TEXT, -- e.g., 'accuracy', 'precision'
    triggering_value NUMERIC(5,4),
    reasoning TEXT
);
COMMENT ON TABLE public.auto_tuning_history IS 'Logs all automated adjustments made by the tuning engine.';


-- === Phase 2: RLS Policies ===

ALTER TABLE public.validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.framework_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auto_tuning_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage validation results in their org" ON public.validation_results FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage performance metrics in their org" ON public.framework_performance_metrics FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view auto-tuning history in their org" ON public.auto_tuning_history FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_validation_org_cve_framework ON public.validation_results(organization_id, cve_id, framework);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_org_date_framework ON public.framework_performance_metrics(organization_id, metric_date DESC, framework);
CREATE INDEX IF NOT EXISTS idx_tuning_history_org_timestamp ON public.auto_tuning_history(organization_id, event_timestamp DESC);


-- === Final Grant Statements ===

GRANT ALL ON public.validation_results TO authenticated;
GRANT ALL ON SEQUENCE validation_results_id_seq TO authenticated;
GRANT ALL ON public.framework_performance_metrics TO authenticated;
GRANT ALL ON SEQUENCE framework_performance_metrics_id_seq TO authenticated;
GRANT ALL ON public.auto_tuning_history TO authenticated;
GRANT ALL ON SEQUENCE auto_tuning_history_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 2H Evidence-Based Validation schema has been applied.';

"""


def get_validation_migration_script() -> str:
    return VALIDATION_MIGRATION_SCRIPT


import reflex as rx

VALIDATION_MIGRATION_SCRIPT = """
-- === Phase 1: Validation & Performance Tables ===

-- Create the 'validation_results' table to store ground truth comparisons
CREATE TABLE IF NOT EXISTS public.validation_results (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    framework TEXT NOT NULL,
    predicted_score NUMERIC(5,2) NOT NULL,
    ground_truth_score NUMERIC(5,2) NOT NULL,
    is_correct BOOLEAN,
    error_margin NUMERIC(5,2),
    validated_at TIMESTAMPTZ DEFAULT NOW(),
    validated_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    source TEXT -- e.g., 'manual_review', 'threat_intel_feed'
);
COMMENT ON TABLE public.validation_results IS 'Stores results of prediction vs. ground truth validations.';

-- Create 'framework_performance_metrics' to track accuracy over time
CREATE TABLE IF NOT EXISTS public.framework_performance_metrics (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    framework TEXT NOT NULL,
    accuracy NUMERIC(5,4),
    precision NUMERIC(5,4),
    recall NUMERIC(5,4),
    f1_score NUMERIC(5,4),
    true_positives INTEGER,
    false_positives INTEGER,
    true_negatives INTEGER,
    false_negatives INTEGER,
    UNIQUE(organization_id, metric_date, framework)
);
COMMENT ON TABLE public.framework_performance_metrics IS 'Tracks daily performance metrics for each scoring framework.';

-- Create 'auto_tuning_history' to log all automated weight adjustments
CREATE TABLE IF NOT EXISTS public.auto_tuning_history (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    framework TEXT NOT NULL,
    previous_weight NUMERIC(4,3),
    new_weight NUMERIC(4,3),
    triggering_metric TEXT, -- e.g., 'accuracy', 'precision'
    triggering_value NUMERIC(5,4),
    reasoning TEXT
);
COMMENT ON TABLE public.auto_tuning_history IS 'Logs all automated adjustments made by the tuning engine.';


-- === Phase 2: RLS Policies ===

ALTER TABLE public.validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.framework_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auto_tuning_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage validation results in their org" ON public.validation_results FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can manage performance metrics in their org" ON public.framework_performance_metrics FOR ALL
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Users can view auto-tuning history in their org" ON public.auto_tuning_history FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );


-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_validation_org_cve_framework ON public.validation_results(organization_id, cve_id, framework);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_org_date_framework ON public.framework_performance_metrics(organization_id, metric_date DESC, framework);
CREATE INDEX IF NOT EXISTS idx_tuning_history_org_timestamp ON public.auto_tuning_history(organization_id, event_timestamp DESC);


-- === Final Grant Statements ===

GRANT ALL ON public.validation_results TO authenticated;
GRANT ALL ON SEQUENCE validation_results_id_seq TO authenticated;
GRANT ALL ON public.framework_performance_metrics TO authenticated;
GRANT ALL ON SEQUENCE framework_performance_metrics_id_seq TO authenticated;
GRANT ALL ON public.auto_tuning_history TO authenticated;
GRANT ALL ON SEQUENCE auto_tuning_history_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 2H Evidence-Based Validation schema has been applied.';

"""


def get_validation_migration_script() -> str:
    return VALIDATION_MIGRATION_SCRIPT