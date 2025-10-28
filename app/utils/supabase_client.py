import os
import reflex as rx
import os
import reflex as rx
from supabase import create_client, Client, PostgrestAPIResponse
from typing import Optional
import logging
from datetime import datetime, timezone

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def sign_up(email: str, password: str) -> Optional[dict]:
    try:
        response = supabase_client.auth.sign_up({"email": email, "password": password})
        if response.user:
            return response.user.dict()
        return None
    except Exception as e:
        logging.exception(f"Sign up failed: {e}")
        return None


async def sign_in(email: str, password: str) -> Optional[dict]:
    try:
        response = supabase_client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if response.user:
            return response.user.dict()
        return None
    except Exception as e:
        logging.exception(f"Sign in failed: {e}")
        return None


async def sign_out() -> bool:
    try:
        supabase_client.auth.sign_out()
        return True
    except Exception as e:
        logging.exception(f"Sign out failed: {e}")
        return False


async def get_user(jwt: str) -> Optional[dict]:
    try:
        response = supabase_client.auth.get_user(jwt)
        if response:
            return response.dict()
        return None
    except Exception as e:
        logging.exception(f"Failed to get user: {e}")
        return None


async def reset_password_for_email(email: str) -> bool:
    try:
        supabase_client.auth.reset_password_for_email(
            email, redirect_to="http://localhost:3000/reset-password"
        )
        return True
    except Exception as e:
        logging.exception(f"Password reset request failed: {e}")
        return False


async def log_api_health(log_data: dict):
    from postgrest.exceptions import APIError

    try:
        supabase_client.table("api_health_log").insert(log_data).execute()
    except APIError as e:
        if hasattr(e, "code") and e.code == "PGRST002":
            logging.warning(
                "API health logging skipped: 'api_health_log' table not found. Please run the required SQL migration to enable API monitoring."
            )
        else:
            logging.exception(
                f"Failed to log API health due to unexpected Supabase error: {e}"
            )
    except Exception as e:
        logging.exception(
            f"An unexpected error occurred during API health logging: {e}"
        )


async def check_user_is_admin() -> bool:
    """Verify if the currently authenticated user has the 'admin' role."""
    from postgrest.exceptions import APIError

    try:
        user_session = supabase_client.auth.get_user()
        if not user_session or not user_session.user:
            return False
        user_id = user_session.user.id
        response = (
            supabase_client.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return response.data.get("role") == "admin"
    except APIError as e:
        if e.code == "PGRST116":
            logging.warning(
                f"Admin check failed: User with ID {user_id} not found in users table."
            )
        else:
            logging.exception(f"Supabase error while checking admin status: {e}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected error occurred during admin check: {e}")
        return False


async def get_total_active_customers() -> int:
    """Query the organizations table for the count of active customers."""
    from postgrest.exceptions import APIError

    try:
        response = (
            supabase_client.table("organizations")
            .select("id", count="exact")
            .eq("status", "active")
            .execute()
        )
        return response.count
    except APIError as e:
        if e.code == "42P01":
            logging.warning(
                "get_total_active_customers: 'organizations' table not found."
            )
        else:
            logging.exception(f"Supabase error fetching active customers: {e}")
        return 0
    except Exception as e:
        logging.exception(f"Unexpected error fetching active customers: {e}")
        return 0


async def get_average_tech_stack_size() -> float:
    """Calculate the average tech stack size across all active organizations."""
    from postgrest.exceptions import APIError

    try:
        response = supabase_client.rpc("get_average_tech_stack_size").execute()
        return round(float(response.data), 2) if response.data else 0.0
    except APIError as e:
        if "function public.get_average_tech_stack_size() does not exist" in str(
            e.message
        ):
            logging.warning("get_average_tech_stack_size: RPC function not found.")
        else:
            logging.exception(f"Supabase error fetching average tech stack size: {e}")
        return 0.0
    except Exception as e:
        logging.exception(f"Unexpected error fetching average tech stack size: {e}")
        return 0.0


async def get_total_tracked_cves() -> int:
    """Count the total number of unique CVEs tracked across all customers."""
    from postgrest.exceptions import APIError

    try:
        response = (
            supabase_client.table("tracked_cves")
            .select("cve_id", count="exact")
            .execute()
        )
        return response.count
    except APIError as e:
        if e.code == "42P01":
            logging.warning("get_total_tracked_cves: 'tracked_cves' table not found.")
        else:
            logging.exception(f"Supabase error fetching total CVEs: {e}")
        return 0
    except Exception as e:
        logging.exception(f"Unexpected error fetching total CVEs: {e}")
        return 0


async def get_all_active_organizations() -> list[dict]:
    """Fetches all organizations with an 'active' status."""
    from postgrest.exceptions import APIError

    try:
        response = (
            supabase_client.table("organizations")
            .select("id", "name")
            .eq("status", "active")
            .execute()
        )
        return response.data
    except APIError as e:
        if e.code == "42P01":
            logging.warning(
                "get_all_active_organizations: 'organizations' table not found."
            )
        else:
            logging.exception(f"Supabase error fetching active organizations: {e}")
        return []
    except Exception as e:
        logging.exception(f"Unexpected error fetching active organizations: {e}")
        return []


async def get_organization_details(organization_id: str) -> Optional[dict]:
    """Fetches details for a single organization."""
    try:
        response = (
            supabase_client.table("organizations")
            .select("*")
            .eq("id", organization_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(
            f"Error fetching organization details for {organization_id}: {e}"
        )
        return None


async def get_all_customers_list() -> list[dict]:
    """Fetch a list of all organizations with their metadata."""
    from postgrest.exceptions import APIError

    try:
        response = (
            supabase_client.table("organizations").select("*").order("name").execute()
        )
        return response.data
    except APIError as e:
        if e.code == "42P01":
            logging.warning("get_all_customers_list: 'organizations' table not found.")
        else:
            logging.exception(f"Supabase error fetching customer list: {e}")
        return []
    except Exception as e:
        logging.exception(f"Unexpected error fetching customer list: {e}")
        return []


async def get_user_memberships() -> Optional[PostgrestAPIResponse]:
    """Fetches the organizations a user is a member of."""
    try:
        user_session = supabase_client.auth.get_user()
        if not user_session or not user_session.user:
            return None
        user_id = user_session.user.id
        return (
            supabase_client.table("members")
            .select("*, organization:organizations(*)")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as e:
        logging.exception(f"Error fetching user memberships: {e}")
        return None


async def get_current_user_with_profile() -> Optional[PostgrestAPIResponse]:
    """Fetches the current user's data joined with their profile."""
    try:
        user_session = supabase_client.auth.get_user()
        if not user_session or not user_session.user:
            return None
        user_id = user_session.user.id
        return (
            supabase_client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as e:
        logging.exception(f"Error fetching user profile: {e}")
        return None


async def create_organization(name: str) -> Optional[str]:
    try:
        response = (
            supabase_client.table("organizations")
            .insert({"name": name})
            .select("id")
            .execute()
        )
        if response.data:
            return response.data[0]["id"]
        return None
    except Exception as e:
        logging.exception(f"Failed to create organization: {e}")
        return None


async def create_membership(user_id: str, org_id: str, role: str) -> bool:
    try:
        await (
            supabase_client.table("members")
            .insert({"user_id": user_id, "organization_id": org_id, "role": role})
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to create membership: {e}")
        return False


async def update_user_profile(user_id: str, full_name: str, job_title: str) -> bool:
    try:
        await (
            supabase_client.table("user_profiles")
            .update({"full_name": full_name, "job_title": job_title})
            .eq("user_id", user_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to update user profile: {e}")
        return False


async def upsert_organization_context(context_data: dict) -> bool:
    try:
        await (
            supabase_client.table("organizations_context")
            .upsert(context_data, on_conflict="organization_id")
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to upsert organization context: {e}")
        return False


async def update_organization_tech_stack(org_id: str, tech_stack: list[str]) -> bool:
    try:
        await (
            supabase_client.table("organizations")
            .update({"tech_stack": tech_stack})
            .eq("id", org_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(
            f"Failed to update validation status for proof {proof_id}: {e}"
        )
        return False


async def create_exploit_validation_record(
    proof_id: int, method: str, status: str
) -> Optional[int]:
    try:
        response = (
            supabase_client.table("exploit_validations")
            .insert(
                {
                    "exploit_proof_id": proof_id,
                    "validation_method": method,
                    "status": status,
                }
            )
            .select("id")
            .single()
            .execute()
        )
        return response.data.get("id")
    except Exception as e:
        logging.exception(
            f"Failed to create exploit validation record for proof {proof_id}: {e}"
        )
        return None


async def update_exploit_validation_record(
    proof_id: int, status: str, evidence: dict
) -> bool:
    try:
        await (
            supabase_client.table("exploit_validations")
            .update(
                {
                    "status": status,
                    "evidence_artifacts": evidence,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("exploit_proof_id", proof_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(
            f"Failed to update exploit validation record for proof {proof_id}: {e}"
        )
        return False


async def get_api_health_logs() -> list[dict]:
    """Fetch all logs from the api_health_log table."""
    from postgrest.exceptions import APIError

    try:
        response = (
            supabase_client.table("api_health_log")
            .select("*")
            .order("start_time", desc=True)
            .limit(100)
            .execute()
        )
        return response.data
    except APIError as e:
        if e.code == "42P01" or (hasattr(e, "code") and e.code == "PGRST002"):
            logging.warning(
                "get_api_health_logs: 'api_health_log' table not found. Please run the SQL migration script from app/utils/admin_queries.py in your Supabase SQL Editor to create it."
            )
            return []
        else:
            logging.exception(f"Supabase error fetching API health logs: {e}")
            return []
    except Exception as e:
        logging.exception(f"Unexpected error fetching API health logs: {e}")
        return []


async def insert_engine_run(organization_id: str) -> Optional[int]:
    try:
        response = (
            supabase_client.table("engine_runs")
            .insert({"organization_id": organization_id, "status": "running"})
            .select("id")
            .execute()
        )
        if response.data:
            return response.data[0]["id"]
        return None
    except Exception as e:
        logging.exception(f"Failed to insert engine run: {e}")
        return None


async def update_engine_run(
    run_id: int, status: str, records_found: Optional[int] = None
):
    try:
        update_data = {
            "status": status,
            "run_completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if records_found is not None:
            update_data["records_found"] = records_found
        supabase_client.table("engine_runs").update(update_data).eq(
            "id", run_id
        ).execute()
    except Exception as e:
        logging.exception(f"Failed to update engine run {run_id}: {e}")


async def get_last_completed_run(organization_id: str) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("engine_runs")
            .select("run_completed_at")
            .eq("organization_id", organization_id)
            .eq("status", "completed")
            .order("run_completed_at", desc=True)
            .limit(1)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get last completed run: {e}")
        return None


async def upsert_vulnerabilities(gaps: list[dict]):
    try:
        await (
            supabase_client.table("framework_scores")
            .upsert(gaps, on_conflict="cve_id, organization_id")
            .execute()
        )
    except Exception as e:
        logging.exception(f"Failed to upsert vulnerabilities: {e}")


async def insert_vulnerabilities(records: list[dict]):
    try:
        await supabase_client.table("framework_scores").insert(records).execute()
    except Exception as e:
        logging.exception(f"Failed to insert vulnerabilities: {e}")


async def create_report(
    org_id: str, creator_id: str, name: str, description: str, report_type: str
) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("reports")
            .insert(
                {
                    "organization_id": org_id,
                    "creator_id": creator_id,
                    "name": name,
                    "description": description,
                    "report_type": report_type,
                }
            )
            .select("*")
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to create report: {e}")
        return None


async def get_reports_for_organization(org_id: str) -> list[dict]:
    try:
        response = (
            supabase_client.table("reports")
            .select("*")
            .eq("organization_id", org_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get reports for org {org_id}: {e}")
        return []


async def add_cves_to_report(report_id: int, cve_ids: list[str], added_by: str) -> bool:
    try:
        records = [
            {"report_id": report_id, "cve_id": cve, "added_by": added_by}
            for cve in cve_ids
        ]
        await supabase_client.table("report_cves").insert(records).execute()
        return True
    except Exception as e:
        logging.exception(f"Failed to add CVEs to report {report_id}: {e}")
        return False


async def remove_cves_from_report(report_id: int, cve_ids: list[str]) -> bool:
    try:
        await (
            supabase_client.table("report_cves")
            .delete()
            .eq("report_id", report_id)
            .in_("cve_id", cve_ids)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to remove CVEs from report {report_id}: {e}")
        return False


async def export_report(
    report_id: int,
    user_id: str,
    export_format: str,
    file_size: int,
    download_url: str,
    expires_at: str,
) -> bool:
    try:
        await (
            supabase_client.table("report_exports")
            .insert(
                {
                    "report_id": report_id,
                    "exported_by": user_id,
                    "format": export_format,
                    "file_size_bytes": file_size,
                    "download_url": download_url,
                    "url_expires_at": expires_at,
                }
            )
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to log export for report {report_id}: {e}")
        return False


async def share_report(report_id: int, shared_by: str, share_details: dict) -> bool:
    try:
        share_record = {**share_details, "report_id": report_id, "shared_by": shared_by}
        await supabase_client.table("report_shares").insert(share_record).execute()
        return True
    except Exception as e:
        logging.exception(f"Failed to share report {report_id}: {e}")
        return False


async def get_export_history(report_id: int) -> list[dict]:
    try:
        response = (
            supabase_client.table("report_exports")
            .select("*")
            .eq("report_id", report_id)
            .order("exported_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get export history for report {report_id}: {e}")
        return []


async def log_report_audit(
    report_id: int, user_id: str, action: str, details: dict, ip: str, user_agent: str
) -> bool:
    try:
        await (
            supabase_client.table("report_audit_log")
            .insert(
                {
                    "report_id": report_id,
                    "user_id": user_id,
                    "action": action,
                    "action_details": details,
                    "ip_address": ip,
                    "user_agent": user_agent,
                }
            )
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to log audit for report {report_id}: {e}")
        return False


async def store_encrypted_api_key(
    org_id: str, provider: str, encrypted_key: str
) -> bool:
    try:
        await (
            supabase_client.table("ai_provider_keys")
            .upsert(
                {
                    "organization_id": org_id,
                    "provider": provider,
                    "encrypted_api_key": encrypted_key,
                },
                on_conflict="organization_id, provider",
            )
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to store API key for org {org_id}: {e}")
        return False


async def get_encrypted_api_key(org_id: str, provider: str) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("ai_provider_keys")
            .select("encrypted_api_key")
            .eq("organization_id", org_id)
            .eq("provider", provider)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get API key for org {org_id}: {e}")
        return None


async def get_org_credit_balance(org_id: str) -> Optional[int]:
    try:
        response = (
            supabase_client.table("organizations")
            .select("ai_credits")
            .eq("id", org_id)
            .single()
            .execute()
        )
        return response.data.get("ai_credits", 0)
    except Exception as e:
        logging.exception(f"Failed to get credit balance for org {org_id}: {e}")
        return None


async def get_white_label_config(org_id: str) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("white_label_configs")
            .select("*")
            .eq("organization_id", org_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get white label config for org {org_id}: {e}")
        return None


async def save_white_label_config(org_id: str, config: dict) -> bool:
    try:
        await (
            supabase_client.table("white_label_configs")
            .upsert(config, on_conflict="organization_id")
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to save white label config for org {org_id}: {e}")
        return False


async def deduct_credits(org_id: str, amount: int) -> bool:
    try:
        current_balance = await get_org_credit_balance(org_id)
        if current_balance is None or current_balance < amount:
            return False
        new_balance = current_balance - amount
        await (
            supabase_client.table("organizations")
            .update({"ai_credits": new_balance})
            .eq("id", org_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to deduct credits for org {org_id}: {e}")
        return False


async def refund_credits(org_id: str, amount: int) -> bool:
    try:
        current_balance = await get_org_credit_balance(org_id)
        if current_balance is None:
            return False
        new_balance = current_balance + amount
        await (
            supabase_client.table("organizations")
            .update({"ai_credits": new_balance})
            .eq("id", org_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to refund credits for org {org_id}: {e}")
        return False


async def store_analysis_cache(
    cve_id: str, org_id: str, provider: str, analysis: dict, tokens: int, cost: int
) -> bool:
    try:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        record = {
            "cve_id": cve_id,
            "organization_id": org_id,
            "provider": provider,
            "analysis_result": analysis,
            "tokens_used": tokens,
            "cost_credits": cost,
            "expires_at": expires_at,
        }
        await (
            supabase_client.table("llm_analysis_cache")
            .upsert(record, on_conflict="cve_id, organization_id")
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to store analysis cache for {cve_id}: {e}")
        return False


async def get_cached_analysis(cve_id: str, org_id: str) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("llm_analysis_cache")
            .select("*")
            .eq("cve_id", cve_id)
            .eq("organization_id", org_id)
            .gte("expires_at", datetime.now(timezone.utc).isoformat())
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get cached analysis for {cve_id}: {e}")
        return None


async def log_llm_usage(
    org_id: str,
    user_id: str,
    cve_id: str,
    provider: str,
    model: str,
    tokens: int,
    credits: int,
    duration: int,
    cached: bool,
) -> bool:
    try:
        record = {
            "organization_id": org_id,
            "user_id": user_id,
            "cve_id": cve_id,
            "provider": provider,
            "model": model,
            "tokens_used": tokens,
            "credits_charged": credits,
            "analysis_duration_ms": duration,
            "was_cached": cached,
        }
        await supabase_client.table("llm_usage_log").insert(record).execute()
        return True
    except Exception as e:
        logging.exception(f"Failed to log LLM usage for org {org_id}: {e}")
        return False


async def get_org_id_from_api_key(api_key: str) -> Optional[str]:
    try:
        key_prefix, key_hash = api_key.split("_", 1)
        response = (
            supabase_client.table("api_keys")
            .select("organization_id")
            .eq("key_prefix", key_prefix)
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .single()
            .execute()
        )
        if response.data:
            return response.data["organization_id"]
        return None
    except Exception as e:
        logging.exception(f"API key validation failed: {e}")
        return None


async def get_api_keys_for_org(org_id: str) -> list[dict]:
    try:
        response = (
            supabase_client.table("api_keys")
            .select("id, key_name, key_prefix, key_hash, created_at")
            .eq("organization_id", org_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to fetch api keys for org {org_id}: {e}")
        return []


async def create_api_key(
    org_id: str, key_name: str, key_prefix: str, key_hash: str
) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("api_keys")
            .insert(
                {
                    "organization_id": org_id,
                    "key_name": key_name,
                    "key_prefix": key_prefix,
                    "key_hash": key_hash,
                }
            )
            .select("*")
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to create api key for org {org_id}: {e}")
        return None


async def revoke_api_key(key_id: str) -> bool:
    try:
        await (
            supabase_client.table("api_keys")
            .update({"is_active": False})
            .eq("id", key_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to revoke api key {key_id}: {e}")
        return False


async def submit_feedback_label(
    finding_id: int, org_id: str, user_id: str, label: str, confidence: int, notes: str
) -> Optional[int]:
    try:
        record = {
            "finding_id": finding_id,
            "organization_id": org_id,
            "user_id": user_id,
            "label": label,
            "confidence": confidence,
            "notes": notes,
        }
        response = (
            supabase_client.table("feedback_labels")
            .insert(record)
            .select("id")
            .single()
            .execute()
        )
        return response.data.get("id")
    except Exception as e:
        logging.exception(f"Failed to submit feedback label: {e}")
        return None


async def get_user_feedback_for_finding(
    finding_id: int, user_id: str
) -> Optional[dict]:
    try:
        response = (
            supabase_client.table("feedback_labels")
            .select("*")
            .eq("finding_id", finding_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get feedback for finding {finding_id}: {e}")
        return None


async def delete_feedback(feedback_id: int, user_id: str) -> bool:
    try:
        await (
            supabase_client.table("feedback_labels")
            .delete()
            .eq("id", feedback_id)
            .eq("user_id", user_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to delete feedback {feedback_id}: {e}")
        return False


async def get_remediation_outcomes_for_playbook(playbook_id: int) -> list[dict]:
    try:
        response = (
            await supabase_client.table("remediation_outcomes")
            .select("*")
            .eq("playbook_id", playbook_id)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(
            f"Failed to get remediation outcomes for playbook {playbook_id}: {e}"
        )
        return []


async def get_playbook_details(playbook_id: int) -> Optional[dict]:
    try:
        response = (
            await supabase_client.table("remediation_playbooks")
            .select("*")
            .eq("id", playbook_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get playbook details for {playbook_id}: {e}")
        return None


async def update_playbook_config(playbook_id: int, config_updates: dict) -> bool:
    try:
        await (
            supabase_client.table("remediation_playbooks")
            .update(config_updates)
            .eq("id", playbook_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to update playbook config for {playbook_id}: {e}")
        return False


async def log_playbook_optimization(
    playbook_id: int,
    optimization_type: str,
    previous_config: dict,
    new_config: dict,
    reasoning: str,
) -> bool:
    try:
        await (
            supabase_client.table("playbook_optimization_log")
            .insert(
                {
                    "playbook_id": playbook_id,
                    "optimization_type": optimization_type,
                    "previous_config": previous_config,
                    "new_config": new_config,
                    "reasoning": reasoning,
                }
            )
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to log playbook optimization for {playbook_id}: {e}")
        return False


async def get_all_active_playbooks() -> list[dict]:
    try:
        response = (
            await supabase_client.table("remediation_playbooks")
            .select("id")
            .eq("is_active", True)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get all active playbooks: {e}")
        return []


async def get_remediation_outcomes_for_playbook(playbook_id: int) -> list[dict]:
    try:
        response = (
            await supabase_client.table("remediation_outcomes")
            .select("*")
            .eq("playbook_id", playbook_id)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(
            f"Failed to get remediation outcomes for playbook {playbook_id}: {e}"
        )
        return []


async def get_playbook_details(playbook_id: int) -> Optional[dict]:
    try:
        response = (
            await supabase_client.table("remediation_playbooks")
            .select("*")
            .eq("id", playbook_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        if "PGRST116" not in str(e):
            logging.exception(f"Failed to get playbook details for {playbook_id}: {e}")
        return None


async def update_playbook_config(playbook_id: int, config_updates: dict) -> bool:
    try:
        await (
            supabase_client.table("remediation_playbooks")
            .update(config_updates)
            .eq("id", playbook_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to update playbook config for {playbook_id}: {e}")
        return False


async def log_playbook_optimization(
    playbook_id: int,
    optimization_type: str,
    previous_config: dict,
    new_config: dict,
    reasoning: str,
) -> bool:
    try:
        await (
            supabase_client.table("playbook_optimization_log")
            .insert(
                {
                    "playbook_id": playbook_id,
                    "optimization_type": optimization_type,
                    "previous_config": previous_config,
                    "new_config": new_config,
                    "reasoning": reasoning,
                }
            )
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to log playbook optimization for {playbook_id}: {e}")
        return False


async def get_all_active_playbooks() -> list[dict]:
    try:
        response = (
            await supabase_client.table("remediation_playbooks")
            .select("id")
            .eq("is_active", True)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get all active playbooks: {e}")
        return []


async def get_high_priority_cves_for_exploit_check() -> list[str]:
    """Returns a list of CVE IDs that should be checked for new exploits."""
    return ["CVE-2021-44228", "CVE-2024-21412", "CVE-2023-38843"]


async def store_exploit_feed_data(feed_data: dict) -> Optional[int]:
    try:
        response = (
            await supabase_client.table("exploit_feeds")
            .insert(feed_data)
            .select("id")
            .single()
            .execute()
        )
        return response.data.get("id")
    except Exception as e:
        if "duplicate key value violates unique constraint" not in str(e):
            logging.exception(f"Failed to store exploit feed data: {e}")
        return None


async def upsert_exploit_proof(proof_data: dict) -> bool:
    try:
        await (
            supabase_client.table("exploit_proofs")
            .upsert(proof_data, on_conflict="cve_id, title")
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to upsert exploit proof: {e}")
        return False


async def get_exploit_proofs_for_cve(
    cve_id: str, org_id: Optional[str] = None, validation_status: Optional[str] = None
) -> list[dict]:
    try:
        query = supabase_client.table("exploit_proofs").select("*").eq("cve_id", cve_id)
        if org_id:
            query = query.eq("organization_id", org_id)
        if validation_status:
            query = query.eq("validation_status", validation_status)
        response = await query.execute()
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get exploit proofs for {cve_id}: {e}")
        return []


async def get_pending_validations() -> list[dict]:
    try:
        response = (
            await supabase_client.table("exploit_proofs")
            .select("*")
            .eq("validation_status", "pending")
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to get pending validations: {e}")
        return []


async def update_validation_status(proof_id: int, status: str, evidence: dict) -> bool:
    try:
        await (
            supabase_client.table("exploit_proofs")
            .update(
                {
                    "validation_status": status,
                    "validation_evidence": evidence,
                    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", proof_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(
            f"Failed to update validation status for proof {proof_id}: {e}"
        )
        return False


async def get_queued_retraining_jobs() -> list[dict]:
    try:
        response = (
            await supabase_client.table("model_retraining_queue")
            .select("organization_id")
            .eq("status", "queued")
            .execute()
        )
        return response.data
    except Exception as e:
        logging.exception(f"Failed to fetch queued retraining jobs: {e}")
        return []


async def update_retraining_status(
    org_id: str, status: str, precision: Optional[float] = None
):
    try:
        update_data = {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if precision is not None:
            update_data["precision_at_50"] = precision
        await (
            supabase_client.table("model_retraining_queue")
            .update(update_data)
            .eq("organization_id", org_id)
            .execute()
        )
    except Exception as e:
        logging.exception(f"Failed to update retraining status for org {org_id}: {e}")


async def delete_feedback(feedback_id: int, user_id: str) -> bool:
    try:
        await (
            supabase_client.table("feedback_labels")
            .delete()
            .eq("id", feedback_id)
            .eq("user_id", user_id)
            .execute()
        )
        return True
    except Exception as e:
        logging.exception(f"Failed to delete feedback {feedback_id}: {e}")
        return False