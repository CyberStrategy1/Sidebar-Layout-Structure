import reflex as rx
from fastapi import Depends, HTTPException
from typing import Optional
from app.api.auth import get_current_org_from_api_key
from app.utils import supabase_client


@rx.page(route="/api/v1/health")
def health_check():
    """API Health Check Endpoint."""
    return {"status": "ok", "timestamp": "2024-07-29T12:00:00Z"}


@rx.page(route="/api/v1/vulnerabilities")
async def list_vulnerabilities(
    organization_id: str = Depends(get_current_org_from_api_key),
    severity: Optional[str] = None,
    is_kev: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List vulnerabilities for the organization."""
    return {
        "data": [
            {
                "cve_id": "CVE-2024-1234",
                "severity": "CRITICAL",
                "universal_risk_score": 95.5,
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset,
    }


@rx.page(route="/api/v1/vulnerabilities/{cve_id}")
async def get_vulnerability(
    cve_id: str, organization_id: str = Depends(get_current_org_from_api_key)
):
    """Get details for a single CVE."""
    return {
        "cve_id": cve_id,
        "universal_risk_score": 95.5,
        "scores": {"cvss": 9.8, "epss": 0.95, "is_kev": True},
    }