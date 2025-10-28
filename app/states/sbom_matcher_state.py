import reflex as rx
from typing import Optional
import logging
from app.services.sbom_matcher import sbom_matcher
from app.state import AppState

logger = logging.getLogger(__name__)


class SBOMMatcherState(rx.State):
    """State for SBOM → Vulnerability matching."""

    is_matching: bool = False
    matches: list[dict] = []
    sbom_components_count: int = 0
    matched_vulns_count: int = 0

    @rx.event(background=True)
    async def run_sbom_matching(self):
        """Run SBOM → vulnerability matching for the current organization."""
        async with self:
            self.is_matching = True
            self.matches = []
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
            sbom_components = app_state.tech_stack
        if not org_id or not sbom_components:
            async with self:
                self.is_matching = False
            yield rx.toast.error("No organization or SBOM data available.")
            return
        try:
            components = [{"name": comp, "version": "*"} for comp in sbom_components]
            async with self:
                self.sbom_components_count = len(components)
            matches = await sbom_matcher.match_sbom_to_vulnerabilities(
                org_id, components
            )
            async with self:
                self.matches = matches
                self.matched_vulns_count = len(matches)
                self.is_matching = False
            yield rx.toast.success(
                f"Matched {len(matches)} vulnerabilities to your SBOM!"
            )
        except Exception as e:
            logger.exception(f"SBOM matching failed: {e}")
            async with self:
                self.is_matching = False
            yield rx.toast.error("SBOM matching failed. Check logs.")