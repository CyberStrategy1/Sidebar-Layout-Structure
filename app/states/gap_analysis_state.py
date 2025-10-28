import reflex as rx
from typing import TypedDict, Any
from datetime import datetime, timedelta
import asyncio
import random
from app.utils import supabase_client


class GapData(TypedDict):
    cve_id: str
    description: str
    published_date: str
    time_gap_days: int
    cvss_gap_score: float
    cpe_gap_score: float
    overall_gap_severity: float
    affects_org_stack: bool
    vendor: str


class FilterOptions(TypedDict):
    search_term: str
    time_gap_ranges: list[str]
    is_kev: bool
    affects_stack: bool
    cvss_score_range: tuple[int, int]
    cpe_score_range: tuple[int, int]


GAP_SEVERITY_COLORS = {"High": "#ef4444", "Medium": "#f97316", "Low": "#facc15"}


class GapAnalysisState(rx.State):
    """State for the Gap Intelligence Dashboard."""

    all_gaps: list[GapData] = []
    filtered_gaps: list[GapData] = []
    is_loading: bool = True
    is_filter_panel_open: bool = False
    filters: FilterOptions = {
        "search_term": "",
        "time_gap_ranges": [],
        "is_kev": False,
        "affects_stack": False,
        "cvss_score_range": (0, 10),
        "cpe_score_range": (0, 10),
    }
    sort_by: tuple[str, str] = ("overall_gap_severity", "desc")
    expanded_rows: set[str] = set()

    @rx.event(background=True)
    async def load_initial_data(self):
        """Load initial gap data from the database or mock."""
        async with self:
            self.is_loading = True
        await asyncio.sleep(1.5)
        gaps = []
        vendors = ["microsoft", "apple", "google", "cisco", "oracle", "adobe"]
        for i in range(500):
            published_date = datetime.now() - timedelta(days=random.randint(1, 365))
            time_gap = (datetime.now() - published_date).days
            gaps.append(
                {
                    "cve_id": f"CVE-2023-{40000 + i}",
                    "description": f"A mock description for a vulnerability in a product.",
                    "published_date": published_date.isoformat(),
                    "time_gap_days": time_gap,
                    "cvss_gap_score": round(random.uniform(0, 10), 1),
                    "cpe_gap_score": round(random.uniform(0, 10), 1),
                    "overall_gap_severity": round(random.uniform(0, 10), 1),
                    "affects_org_stack": random.choice([True, False]),
                    "vendor": random.choice(vendors),
                }
            )
        async with self:
            self.all_gaps = gaps
            self.is_loading = False
            yield GapAnalysisState.apply_filters

    def _apply_all_filters(self):
        """Helper to apply all active filters and sorting to the gap list."""
        gaps = self.all_gaps
        if self.filters["search_term"]:
            term = self.filters["search_term"].lower()
            gaps = [
                gap
                for gap in gaps
                if term in gap["cve_id"].lower() or term in gap["vendor"].lower()
            ]
        if self.filters["affects_stack"]:
            gaps = [gap for gap in gaps if gap["affects_org_stack"]]
        if self.filters["time_gap_ranges"]:
            filtered_by_gap = []
            for gap_range in self.filters["time_gap_ranges"]:
                min_g, max_g = map(int, gap_range.split("-"))
                filtered_by_gap.extend(
                    [g for g in gaps if min_g <= g["time_gap_days"] < max_g]
                )
            gaps = filtered_by_gap
        min_cvss, max_cvss = self.filters["cvss_score_range"]
        gaps = [g for g in gaps if min_cvss <= g["cvss_gap_score"] <= max_cvss]
        min_cpe, max_cpe = self.filters["cpe_score_range"]
        gaps = [g for g in gaps if min_cpe <= g["cpe_gap_score"] <= max_cpe]
        key, order = self.sort_by
        reverse = order == "desc"
        gaps = sorted(gaps, key=lambda g: g.get(key, 0), reverse=reverse)
        self.filtered_gaps = gaps

    @rx.event
    def apply_filters(self):
        self._apply_all_filters()
        return

    @rx.event
    def toggle_filter_panel(self):
        self.is_filter_panel_open = not self.is_filter_panel_open

    @rx.event
    def set_search_term(self, term: str):
        self.filters["search_term"] = term
        self._apply_all_filters()

    @rx.event
    def toggle_time_gap_filter(self, selected_range: str):
        if selected_range in self.filters["time_gap_ranges"]:
            self.filters["time_gap_ranges"].remove(selected_range)
        else:
            self.filters["time_gap_ranges"].append(selected_range)
        self._apply_all_filters()

    @rx.event
    def toggle_affects_stack_filter(self, checked: bool):
        self.filters["affects_stack"] = checked
        self._apply_all_filters()

    @rx.event
    def set_sort(self, key: str):
        if self.sort_by[0] == key:
            self.sort_by = (key, "asc" if self.sort_by[1] == "desc" else "desc")
        else:
            self.sort_by = (key, "desc")
        self._apply_all_filters()

    @rx.event
    def clear_all_filters(self):
        self.filters = {
            "search_term": "",
            "time_gap_ranges": [],
            "is_kev": False,
            "affects_stack": False,
            "cvss_score_range": (0, 10),
            "cpe_score_range": (0, 10),
        }
        self._apply_all_filters()
        return rx.toast.info("Filters cleared.")

    @rx.var
    def total_gaps_count(self) -> int:
        return len(self.filtered_gaps)

    @rx.var
    def avg_enrichment_time(self) -> int:
        if not self.filtered_gaps:
            return 0
        total_days = sum((g["time_gap_days"] for g in self.filtered_gaps))
        return round(total_days / len(self.filtered_gaps))

    @rx.var
    def worst_offenders(self) -> list[GapData]:
        return sorted(self.all_gaps, key=lambda g: g["time_gap_days"], reverse=True)[:5]

    @rx.var
    def cvss_gap_distribution(self) -> list[dict]:
        dist = {i: 0 for i in range(11)}
        for gap in self.filtered_gaps:
            score = int(gap["cvss_gap_score"])
            dist[score] += 1
        return [{"score": k, "count": v} for k, v in dist.items()]

    @rx.var
    def cpe_gap_distribution(self) -> list[dict]:
        dist = {i: 0 for i in range(11)}
        for gap in self.filtered_gaps:
            score = int(gap["cpe_gap_score"])
            dist[score] += 1
        return [{"score": k, "count": v} for k, v in dist.items()]

    @rx.var
    def monthly_backlog_growth(self) -> list[dict]:
        monthly_counts = {}
        for gap in self.all_gaps:
            month = datetime.fromisoformat(gap["published_date"]).strftime("%Y-%m")
            monthly_counts[month] = monthly_counts.get(month, 0) + 1
        sorted_months = sorted(monthly_counts.keys())
        return [{"month": m, "count": monthly_counts[m]} for m in sorted_months][-12:]