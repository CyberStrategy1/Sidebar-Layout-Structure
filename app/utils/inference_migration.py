import reflex as rx

INFERENCE_MIGRATION_SCRIPT = """
-- === Phase 3A: AI Inference Engine Tables ===

-- Create 'inference_findings' to store detailed ML predictions and extracted features
CREATE TABLE IF NOT EXISTS public.inference_findings (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    cve_id TEXT NOT NULL,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,

    -- Raw Input Data Captured at Time of Inference
    raw_description TEXT NOT NULL,
    raw_references TEXT[],
    raw_cwe_ids TEXT[],
    inferred_cpes JSONB DEFAULT '[]'::jsonb,

    -- AI Inference Engine Outputs from Feature Extraction
    extracted_products JSONB,           -- NER: Product names, versions, vendors
    extracted_attack_vectors JSONB,     -- NER: Attack techniques, exploit methods
    technical_keywords TEXT[],          -- Feature engineering: Key technical terms
    semantic_embedding FLOAT[],         -- SBERT: 384-dim vector for similarity search

    -- ML Model Predictions
    predicted_severity TEXT CHECK (predicted_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    severity_confidence NUMERIC(5,4),   -- Confidence of the severity prediction (0.0 to 1.0)
    predicted_epss NUMERIC(5,4),        -- Model's prediction of EPSS
    predicted_impact_score NUMERIC(5,2),-- Model's prediction of overall impact (0-100)
    exploitation_likelihood TEXT CHECK (exploitation_likelihood IN ('Very High', 'High', 'Medium', 'Low')),

    -- Risk Classification Predictions
    risk_category TEXT,                 -- e.g., 'RCE', 'Privilege Escalation', 'DoS', 'Info Disclosure'
    attack_complexity TEXT CHECK (attack_complexity IN ('Low', 'High')),
    requires_user_interaction BOOLEAN,

    -- Enrichment Metadata
    inference_timestamp TIMESTAMPTZ DEFAULT NOW(),
    model_version TEXT,
    confidence_score NUMERIC(5,4),      -- Overall confidence in the enrichment quality
    prediction_probability NUMERIC(5,4), -- model confidence 0-1
    processing_time_ms INTEGER,

    UNIQUE(cve_id, organization_id)
);
COMMENT ON TABLE public.inference_findings IS 'Stores enriched data and predictions from the AI inference engine for each CVE.';

-- RLS Policy for 'inference_findings'
ALTER TABLE public.inference_findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view inference findings in their own organization" ON public.inference_findings FOR SELECT
    USING ( organization_id = (SELECT organization_id FROM public.users WHERE id = auth.uid()) );

CREATE POLICY "Admins have full access to all inference findings" ON public.inference_findings FOR ALL
    USING ( (SELECT role FROM public.users WHERE id = auth.uid()) = 'admin' );

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_inference_findings_org_cve ON public.inference_findings(organization_id, cve_id);
CREATE INDEX IF NOT EXISTS idx_inference_findings_risk_category ON public.inference_findings(risk_category);

-- Grant Permissions
GRANT ALL ON public.inference_findings TO authenticated;
GRANT ALL ON SEQUENCE inference_findings_id_seq TO authenticated;

SELECT 'SUCCESS: Phase 3A AI Inference Engine schema has been applied.';
"""


def get_inference_migration_script() -> str:
    """Returns the SQL migration script for the inference engine schema."""
    return INFERENCE_MIGRATION_SCRIPT