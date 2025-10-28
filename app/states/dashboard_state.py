import reflex as rx
from typing import TypedDict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
import random


class CveData(TypedDict):
    id: str
    description: str
    published_date: str
    severity: str
    time_gap: int
    tech_match: int
    is_kev: bool
    vendor: str
    product: str
    version: str
    universal_risk_score: float


class View(TypedDict):
    name: str
    filters: dict


class FilterOptions(TypedDict):
    tech_stack: list[str]
    severity: list[str]
    date_range: str
    is_kev: bool
    search_term: str


SEVERITY_COLORS = {
    "CRITICAL": "#ef4444",
    "HIGH": "#f97316",
    "MEDIUM": "#facc15",
    "LOW": "#84cc16",
    "UNKNOWN": "#9ca3af",
}


class DashboardState(rx.State):
    """State for the interactive main dashboard."""

    all_cves: list[CveData] = []
    filtered_cves: list[CveData] = []
    is_loading: bool = True
    is_filter_panel_open: bool = False
    filters: FilterOptions = {
        "tech_stack": [],
        "severity": [],
        "date_range": "90",
        "is_kev": False,
        "search_term": "",
    }
    sort_by: tuple[str, str] = ("time_gap", "desc")
    expanded_rows: set[str] = set()
    selected_rows: set[str] = set()
    views: list[View] = [
        {"name": "Default View", "filters": {}},
        {
            "name": "Critical KEVs (Last 30 Days)",
            "filters": {
                "severity": ["CRITICAL"],
                "is_kev": True,
                "date_range": "30",
                "tech_stack": [],
                "search_term": "",
            },
        },
    ]
    active_view: str = "Default View"
    new_view_name: str = ""
    scanner_view_cves: list[dict] = [
        {
            "CVE ID": "CVE-2024-0001",
            "Vendor": "apache",
            "Product": "Apache HTTP Server",
            "Version": "2.4.58",
        },
        {
            "CVE ID": "CVE-2024-0002",
            "Vendor": "microsoft",
            "Product": "Windows Server",
            "Version": "2019",
        },
    ]

    @rx.event(background=True)
    async def load_initial_data(self):
        """Load initial CVE data."""
        async with self:
            self.is_loading = True
        await asyncio.sleep(2)
        cves = []
        tech = ["PostgreSQL", "React", "AWS", "Nginx", "Docker", "Kubernetes"]
        vendors = ["postgresql", "facebook", "amazon", "nginx", "docker", "google"]
        products = tech
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for i in range(200):
            cves.append(
                {
                    "id": f"CVE-2024-10{i:03}",
                    "description": f"A vulnerability in {products[i % len(products)]} allows for remote code execution.",
                    "published_date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "severity": severities[i % len(severities)],
                    "time_gap": 90 - i,
                    "tech_match": 95 - i % 40,
                    "is_kev": i % 10 == 0,
                    "vendor": vendors[i % len(vendors)],
                    "product": products[i % len(products)],
                    "version": f"1.{i % 9}.{i % 20}",
                    "universal_risk_score": round(random.uniform(20, 100), 1),
                }
            )
        async with self:
            self.all_cves = cves
            self.is_loading = False
            self._apply_all_filters()

    def _apply_all_filters(self):
        """Helper to apply all active filters and sorting to the CVE list."""
        cves = self.all_cves
        if self.filters["search_term"]:
            term = self.filters["search_term"].lower()
            cves = [
                cve
                for cve in cves
                if term in cve["id"].lower() or term in cve["description"].lower()
            ]
        if self.filters["is_kev"]:
            cves = [cve for cve in cves if cve["is_kev"]]
        if self.filters["severity"]:
            cves = [cve for cve in cves if cve["severity"] in self.filters["severity"]]
        if self.filters["tech_stack"]:
            tech_filters = [t.lower() for t in self.filters["tech_stack"]]
            cves = [
                cve
                for cve in cves
                if any((t in cve["product"].lower() for t in tech_filters))
            ]
        if self.filters["date_range"] and self.filters["date_range"].isdigit():
            days = int(self.filters["date_range"])
            cutoff_date = datetime.now() - timedelta(days=days)
            cves = [
                cve
                for cve in cves
                if datetime.fromisoformat(cve["published_date"]) > cutoff_date
            ]
        key, order = self.sort_by
        reverse = order == "desc"
        cves = sorted(cves, key=lambda cve: cve.get(key, 0), reverse=reverse)
        self.filtered_cves = cves

    @rx.event
    def apply_all_filters(self):
        """Apply all active filters and sorting to the CVE list."""
        self._apply_all_filters()

    @rx.event
    def toggle_filter_panel(self):
        self.is_filter_panel_open = not self.is_filter_panel_open

    @rx.event
    def set_search_term(self, term: str):
        self.filters["search_term"] = term
        self.apply_all_filters()

    @rx.event
    def clear_search_term(self):
        self.filters["search_term"] = ""
        self.apply_all_filters()

    @rx.event
    def toggle_kev_filter(self, is_checked: bool):
        self.filters["is_kev"] = is_checked
        self.apply_all_filters()

    @rx.event
    def set_date_range(self, range_val: str):
        self.filters["date_range"] = range_val
        self.apply_all_filters()

    @rx.event
    def toggle_severity_filter(self, severity: str):
        if severity in self.filters["severity"]:
            self.filters["severity"].remove(severity)
        else:
            self.filters["severity"].append(severity)
        self.apply_all_filters()

    @rx.event
    def set_sort(self, key: str):
        if self.sort_by[0] == key:
            self.sort_by = (key, "asc" if self.sort_by[1] == "desc" else "desc")
        else:
            self.sort_by = (key, "desc")
        self.apply_all_filters()

    @rx.event
    def toggle_row_expansion(self, cve_id: str):
        if cve_id in self.expanded_rows:
            self.expanded_rows.remove(cve_id)
        else:
            self.expanded_rows.add(cve_id)

    @rx.event
    def toggle_row_selection(self, cve_id: str):
        if cve_id in self.selected_rows:
            self.selected_rows.remove(cve_id)
        else:
            self.selected_rows.add(cve_id)

    @rx.event
    def toggle_select_all(self, is_checked: bool):
        if is_checked:
            self.selected_rows = {cve["id"] for cve in self.filtered_cves}
        else:
            self.selected_rows = set()

    @rx.event
    def save_current_view(self):
        if not self.new_view_name.strip():
            return rx.toast.error("View name cannot be empty.")
        self.views.append(
            {
                "name": self.new_view_name,
                "filters": json.loads(json.dumps(self.filters)),
            }
        )
        self.new_view_name = ""
        return rx.toast.success("View saved successfully!")

    @rx.event
    def load_view(self, view_name: str):
        for view in self.views:
            if view["name"] == view_name:
                self.filters = view["filters"]
                self.active_view = view_name
                self.apply_all_filters()
                return rx.toast.info(f"Loaded view: {view_name}")

    @rx.var
    def awaiting_enrichment_count(self) -> int:
        return len(self.filtered_cves)

    @rx.var
    def average_enrichment_lag(self) -> int:
        if not self.filtered_cves:
            return 0
        total_lag = sum((cve["time_gap"] for cve in self.filtered_cves))
        return round(total_lag / len(self.filtered_cves))

    @rx.var
    def critical_kev_count(self) -> int:
        return len(
            [
                cve
                for cve in self.filtered_cves
                if cve["severity"] == "CRITICAL" and cve["is_kev"]
            ]
        )

    @rx.var
    def severity_distribution(self) -> list[dict[str, str | int]]:
        dist = {s: 0 for s in SEVERITY_COLORS}
        for cve in self.filtered_cves:
            dist[cve["severity"]] += 1
        return [
            {"name": k, "value": v, "fill": SEVERITY_COLORS[k]} for k, v in dist.items()
        ]

    @rx.var
    def cves_over_time(self) -> list[dict[str, str | int]]:
        data = {}
        for cve in self.all_cves:
            date = datetime.fromisoformat(cve["published_date"]).strftime("%Y-%m-%d")
            if date not in data:
                data[date] = 0
            data[date] += 1
        sorted_data = sorted(data.items())[-90:]
        return [{"date": date, "count": count} for date, count in sorted_data]

    @rx.var
    async def tech_stack_distribution(self) -> list[dict[str, str | int]]:
        from app.state import AppState

        app_state = await self.get_state(AppState)
        tech_stack = app_state.tech_stack
        dist = {tech: 0 for tech in tech_stack}
        for cve in self.filtered_cves:
            for tech in tech_stack:
                if tech.lower() in cve["product"].lower():
                    dist[tech] += 1
        return [{"name": k, "count": v} for k, v in dist.items()]

    @rx.var
    def blind_spot_cves(self) -> list[dict]:
        scanner_cve_ids = {cve["CVE ID"] for cve in self.scanner_view_cves}
        return [cve for cve in self.all_cves if cve["id"] not in scanner_cve_ids][:5]