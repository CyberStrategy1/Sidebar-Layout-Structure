import reflex as rx
from typing import TypedDict, Any
from app.states.framework_state import FrameworkState
from app.states.risk_scoring_state import RiskScoringState
from app.state import AppState
import asyncio
import random
from datetime import datetime, timedelta


class CveRiskData(TypedDict):
    cve_id: str
    description: str
    universal_risk_score: float
    cvss_score: float
    epss_score: float
    is_kev: bool
    ssvc_decision: str
    lev_score: float
    agreement: float
    conflicts: list[str]
    published_date: str


class RiskIntelligenceState(rx.State):
    """State for the Risk Intelligence dashboard."""

    all_cves: list[CveRiskData] = []
    filtered_cves: list[CveRiskData] = []
    is_loading: bool = True
    sort_by: tuple[str, str] = ("universal_risk_score", "desc")
    selected_cve: CveRiskData | None = None
    show_detail_modal: bool = False

    @rx.event(background=True)
    async def load_all_cve_data(self):
        async with self:
            self.is_loading = True
        await asyncio.sleep(2)
        cves = []
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        ssvc_decisions = ["Act", "Attend", "Track*", "Track"]
        for i in range(200):
            conflicts = []
            cvss = round(random.uniform(3, 10), 1)
            epss = round(random.uniform(0, 1), 4)
            if cvss > 7 and epss < 0.02:
                conflicts.append("High CVSS, Low EPSS")
            cves.append(
                {
                    "cve_id": f"CVE-2024-2{i:04}",
                    "description": f"This is a sample description for CVE-2024-2{i:04}.",
                    "universal_risk_score": round(random.uniform(20, 100), 1),
                    "cvss_score": cvss,
                    "epss_score": epss,
                    "is_kev": i % 10 == 0,
                    "ssvc_decision": ssvc_decisions[i % len(ssvc_decisions)],
                    "lev_score": round(min(1.0, epss * 1.25), 4),
                    "agreement": round(random.uniform(0.6, 1.0), 2),
                    "conflicts": conflicts,
                    "published_date": (datetime.now() - timedelta(days=i)).isoformat(),
                }
            )
        async with self:
            self.all_cves = cves
            self.filtered_cves = cves
            self.is_loading = False
            self._apply_sorting()

    def _apply_sorting(self):
        key, order = self.sort_by
        reverse = order == "desc"
        self.filtered_cves = sorted(
            self.filtered_cves, key=lambda cve: cve.get(key, 0) or 0, reverse=reverse
        )

    @rx.event
    def set_sort(self, key: str):
        if self.sort_by[0] == key:
            self.sort_by = (key, "asc" if self.sort_by[1] == "desc" else "desc")
        else:
            self.sort_by = (key, "desc")
        self._apply_sorting()

    @rx.event
    def show_cve_details(self, cve: CveRiskData):
        self.selected_cve = cve
        self.show_detail_modal = True

    @rx.event
    def close_detail_modal(self):
        self.show_detail_modal = False
        self.selected_cve = None

    @rx.var
    def score_distribution(self) -> list[dict]:
        dist = {i * 10: 0 for i in range(11)}
        for cve in self.all_cves:
            bucket = int(cve["universal_risk_score"] // 10) * 10
            dist[bucket] += 1
        return [{"range": f"{k}-{k + 9}", "count": v} for k, v in dist.items()]

    @rx.var
    def selected_cve_breakdown(self) -> list[dict]:
        if not self.selected_cve:
            return []
        score = self.selected_cve["universal_risk_score"]
        return [
            {"name": "CVSS", "value": score * 0.4},
            {"name": "EPSS", "value": score * 0.3},
            {"name": "SSVC", "value": score * 0.1},
            {
                "name": "KEV Bonus",
                "value": score * 0.2 if self.selected_cve["is_kev"] else 0,
            },
        ]