import reflex as rx
from typing import TypedDict


class Cve(TypedDict):
    cve_id: str
    vendor: str
    product: str
    version: str


class TechStackState(rx.State):
    """State for managing the technology stack and related data."""

    is_loading: bool = False
    unenriched_cves: list[dict] = []
    tech_stack: list[str] = ["PostgreSQL", "Windows Server"]
    new_tech_stack_item: str = ""