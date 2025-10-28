import reflex as rx

FEEDBACK_MIGRATION_SCRIPT = """
-- === Phase 1: Human-in-the-Loop (HITL) Feedback Tables ===

-- Create 'feedback_labels' to store user-provided ground truth
CREATE TABLE IF NOT EXISTS public.feedback_labels (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    finding_id BIGINT NOT NULL REFERENCES public.inference_findings(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    label TEXT NOT NULL CHECK (label IN ('exploitable', 'false_positive', 'uncertain')),
    confidence INTEGER CHECK (confidence BETWEEN 1 AND 5), -- 1-5 confidence scale
    notes TEXT, -- Optional detailed notes from the user
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(finding_id, user_id) -- A user can only label a finding once
);
COMMENT ON TABLE public.feedback_labels IS 'Stores user-provided ground truth labels for model findings to enable active learning.';

-- Create 'model_retraining_queue' to trigger retraining jobs
CREATE TABLE IF NOT EXISTS public.model_retraining_queue (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE UNIQUE,
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'queued', 'running', 'completed', 'failed')),
    feedback_count_at_trigger INTEGER,
    triggered_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    precision_at_50 NUMERIC(5,4) -- Track model performance
);
COMMENT ON TABLE public.model_retraining_queue IS 'Tracks the status of model retraining jobs triggered by feedback thresholds.';

-- === Phase 2: RLS Policies ===

ALTER TABLE public.feedback_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_retraining_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own feedback labels" ON public.feedback_labels FOR ALL
    USING ( user_id = auth.uid() );

CREATE POLICY "Org owners can view all feedback in their org" ON public.feedback_labels FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.members WHERE user_id = auth.uid() AND role = 'owner') );

CREATE POLICY "Users can view retraining status for their org" ON public.model_retraining_queue FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

-- === Phase 3: Indexes ===

CREATE INDEX IF NOT EXISTS idx_feedback_finding_id ON public.feedback_labels(finding_id);
CREATE INDEX IF NOT EXISTS idx_feedback_org_id ON public.feedback_labels(organization_id);

-- === Phase 4: Triggers and Functions ===

-- Trigger to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION public.update_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_feedback_update
    BEFORE UPDATE ON public.feedback_labels
    FOR EACH ROW
    EXECUTE FUNCTION public.update_feedback_updated_at();

-- Function to check feedback count and queue retraining
CREATE OR REPLACE FUNCTION public.check_and_queue_retraining()
RETURNS TRIGGER AS $$
DECLARE
    feedback_count INTEGER;
    retraining_threshold INTEGER := 100; -- Set the threshold here
BEGIN
    -- Count feedback for the organization
    SELECT count(*) INTO feedback_count
    FROM public.feedback_labels
    WHERE organization_id = NEW.organization_id;

    -- Check if threshold is met
    IF feedback_count >= retraining_threshold THEN
        -- Upsert into the retraining queue
        INSERT INTO public.model_retraining_queue (organization_id, status, feedback_count_at_trigger, triggered_at)
        VALUES (NEW.organization_id, 'queued', feedback_count, NOW())
        ON CONFLICT (organization_id)
        DO UPDATE SET
            status = 'queued',
            feedback_count_at_trigger = EXCLUDED.feedback_count_at_trigger,
            triggered_at = EXCLUDED.triggered_at
        WHERE public.model_retraining_queue.status = 'idle'; -- Only queue if not already queued/running
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to run the check after each new feedback submission
CREATE TRIGGER on_new_feedback
    AFTER INSERT ON public.feedback_labels
    FOR EACH ROW
    EXECUTE FUNCTION public.check_and_queue_retraining();


-- === Final Grant Statements ===

GRANT ALL ON public.feedback_labels TO authenticated;
GRANT ALL ON SEQUENCE feedback_labels_id_seq TO authenticated;
GRANT ALL ON public.model_retraining_queue TO authenticated;
GRANT ALL ON SEQUENCE model_retraining_queue_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 3B Human-in-the-Loop schema has been applied.';
"""


def get_feedback_migration_script() -> str:
    return FEEDBACK_MIGRATION_SCRIPT