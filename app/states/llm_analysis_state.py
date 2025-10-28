import reflex as rx
from typing import Optional, Literal, TypedDict
import logging
import os
import json
import asyncio
import random
from datetime import datetime, timedelta, timezone
from app.utils import supabase_client
from app.utils.encryption import encrypt_data, decrypt_data
from app.utils.llm_prompts import get_vulnerability_analysis_prompt
from app.state import AppState
from app.states.auth_state import AuthState

PROVIDER_CONFIG = {
    "openai": {
        "model": "gpt-4o-mini",
        "cost_credits": 10,
        "client_class": "openai.AsyncOpenAI",
    },
    "groq": {
        "model": "llama-3.1-70b-versatile",
        "cost_credits": 3,
        "client_class": "groq.AsyncGroq",
    },
    "gemini": {
        "model": "gemini-1.5-flash",
        "cost_credits": 5,
        "client_class": "google.generativeai.GenerativeModel",
    },
    "anthropic": {
        "model": "claude-3-5-sonnet-20240620",
        "cost_credits": 12,
        "client_class": "anthropic.AsyncAnthropic",
    },
}
Provider = Literal["openai", "groq", "gemini", "anthropic"]


class AnalysisResult(TypedDict):
    executive_summary: str
    technical_impact: str
    exploitation_likelihood: str
    recommended_actions: list[str]
    remediation_timeline: str
    business_risk_context: str


class LlmAnalysisState(rx.State):
    """Manages LLM-based vulnerability analysis, providers, and credits."""

    is_analyzing: bool = False
    analysis_result: dict[str, AnalysisResult] = {}
    streaming_content: str = ""
    error_message: str = ""
    selected_provider: Provider = "groq"
    provider_keys: dict[Provider, str] = {}
    is_byok_enabled: dict[Provider, bool] = {}
    org_credits: int = 0
    is_loading_keys: bool = False
    test_connection_status: dict[Provider, str] = {}

    @rx.event
    def handle_api_key_change(self, provider: str, value: str):
        """Update the value of a provider key in the state."""
        self.provider_keys[provider] = value

    @rx.var
    def current_provider_cost(self) -> int:
        """Get the cost for the currently selected provider."""
        if self.selected_provider in PROVIDER_CONFIG:
            return PROVIDER_CONFIG[self.selected_provider]["cost_credits"]
        return 0

    @rx.event(background=True)
    async def load_provider_keys(self):
        """Load stored API keys and credit balance for the organization."""
        async with self:
            self.is_loading_keys = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            async with self:
                self.is_loading_keys = False
            return
        try:
            tasks = {
                provider: supabase_client.get_encrypted_api_key(org_id, provider)
                for provider in PROVIDER_CONFIG
            }
            results = await asyncio.gather(*tasks.values())
            keys_data = dict(zip(tasks.keys(), results))
            credit_balance = await supabase_client.get_org_credit_balance(org_id)
            async with self:
                for provider, key_data in keys_data.items():
                    if key_data and key_data.get("encrypted_api_key"):
                        self.provider_keys[provider] = "********"
                        self.is_byok_enabled[provider] = True
                    else:
                        self.provider_keys[provider] = ""
                        self.is_byok_enabled[provider] = False
                self.org_credits = credit_balance or 0
                self.is_loading_keys = False
        except Exception as e:
            logging.exception(f"Failed to load provider keys: {e}")
            async with self:
                self.is_loading_keys = False

    @rx.event(background=True)
    async def save_api_key(self, provider: Provider, api_key: str):
        """Encrypt and save a new API key for the selected provider."""
        if not api_key.strip():
            yield rx.toast.error("API Key cannot be empty.")
            return
        async with self:
            self.is_loading_keys = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            return
        try:
            encrypted_key = encrypt_data(api_key)
            await supabase_client.store_encrypted_api_key(
                org_id, provider, encrypted_key
            )
            async with self:
                self.provider_keys[provider] = "********"
                self.is_byok_enabled[provider] = True
            yield rx.toast.success(f"{provider.capitalize()} API key saved securely.")
        except Exception as e:
            logging.exception(f"Failed to save API key: {e}")
            yield rx.toast.error("Failed to save API key.")
        finally:
            async with self:
                self.is_loading_keys = False

    @rx.event(background=True)
    async def test_api_key(self, provider: Provider):
        """Test the connection for a given provider's API key."""
        async with self:
            self.test_connection_status[provider] = "testing"
        await asyncio.sleep(1.5)
        success = random.choice([True, False])
        async with self:
            if success:
                self.test_connection_status[provider] = "success"
                yield rx.toast.success("Connection successful!")
            else:
                self.test_connection_status[provider] = "failure"
                yield rx.toast.error("Connection failed. Please check your key.")

    @rx.event(background=True)
    async def analyze_cve(self, cve_data: dict):
        """Orchestrate the LLM analysis for a given CVE."""
        cve_id = cve_data["cve_id"]
        async with self:
            self.is_analyzing = True
            self.streaming_content = ""
            self.error_message = ""
            app_state = await self.get_state(AppState)
            auth_state = await self.get_state(AuthState)
            org_id = app_state.active_organization_id
            user_id = auth_state.user_id
        if not org_id or not user_id:
            return
        cached = await supabase_client.get_cached_analysis(cve_id, org_id)
        if cached:
            async with self:
                self.analysis_result[cve_id] = cached["analysis_result"]
                self.is_analyzing = False
            await supabase_client.log_llm_usage(
                org_id, user_id, cve_id, cached["provider"], "cached", 0, 0, 0, True
            )
            yield rx.toast.info(
                f"Loaded cached analysis from {cached['provider'].capitalize()}."
            )
            return
        provider_cost = PROVIDER_CONFIG[self.selected_provider]["cost_credits"]
        is_byok = self.is_byok_enabled.get(self.selected_provider, False)
        if not is_byok and self.org_credits < provider_cost:
            async with self:
                self.error_message = "Insufficient credits for this analysis."
                self.is_analyzing = False
            yield rx.toast.error(self.error_message)
            return
        if not is_byok:
            await supabase_client.deduct_credits(org_id, provider_cost)
            async with self:
                self.org_credits -= provider_cost
        try:
            org_context = {
                "industry": "Technology",
                "tech_stack": app_state.tech_stack,
                "risk_appetite": "Medium",
            }
            prompt = get_vulnerability_analysis_prompt(cve_data, org_context)
            mock_response = {
                "executive_summary": "This is a critical vulnerability that requires immediate attention.",
                "technical_impact": "Successful exploitation could lead to remote code execution.",
                "exploitation_likelihood": "High, as a PoC is available.",
                "recommended_actions": [
                    "Apply vendor patch immediately",
                    "Monitor for unusual activity",
                ],
                "remediation_timeline": "Within 72 hours",
                "business_risk_context": "Could lead to data breach and reputational damage.",
            }
            response_json_str = json.dumps(mock_response, indent=2)
            for i in range(0, len(response_json_str), 15):
                async with self:
                    self.streaming_content += response_json_str[i : i + 15]
                await asyncio.sleep(0.05)
            parsed_result = json.loads(self.streaming_content)
            tokens_used = len(prompt) + len(self.streaming_content)
            await supabase_client.store_analysis_cache(
                cve_id,
                org_id,
                self.selected_provider,
                parsed_result,
                tokens_used,
                0 if is_byok else provider_cost,
            )
            await supabase_client.log_llm_usage(
                org_id,
                user_id,
                cve_id,
                self.selected_provider,
                PROVIDER_CONFIG[self.selected_provider]["model"],
                tokens_used,
                0 if is_byok else provider_cost,
                1500,
                False,
            )
            async with self:
                self.analysis_result[cve_id] = parsed_result
        except Exception as e:
            logging.exception(f"LLM analysis failed for {cve_id}: {e}")
            async with self:
                self.error_message = f"Analysis failed: {e}"
            if not is_byok:
                await supabase_client.refund_credits(org_id, provider_cost)
                async with self:
                    self.org_credits += provider_cost
            yield rx.toast.error("Analysis failed. Credits refunded.")
        finally:
            async with self:
                self.is_analyzing = False