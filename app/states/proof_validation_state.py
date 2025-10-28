import reflex as rx
from typing import Optional, Literal
import logging
import asyncio
from app.utils import supabase_client
from app.services.exploit_validation_service import ExploitValidationService

logger = logging.getLogger(__name__)


class ProofValidationState(rx.State):
    """Manages the state and workflow for exploit proof validation."""

    pending_proofs: list[dict] = []
    validating_proofs: dict[int, dict] = {}
    validation_results: dict[int, dict] = {}
    is_loading: bool = False

    @rx.event(background=True)
    async def load_pending_proofs(self):
        """Load exploit proofs that are awaiting validation."""
        async with self:
            self.is_loading = True
        try:
            proofs = await supabase_client.get_pending_validations()
            async with self:
                self.pending_proofs = proofs
        except Exception as e:
            logger.exception(f"Failed to load pending proofs: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def start_validation_for_proof(self, proof_id: int):
        """Initiate the validation process for a single exploit proof."""
        proof_to_validate = None
        async with self:
            for i, p in enumerate(self.pending_proofs):
                if p["id"] == proof_id:
                    proof_to_validate = self.pending_proofs.pop(i)
                    self.validating_proofs[proof_id] = proof_to_validate
                    break
        if not proof_to_validate:
            yield rx.toast.error(f"Proof ID {proof_id} not found.")
            return
        try:
            metasploit_host = "127.0.0.1"
            metasploit_pass = "msfadmin"
            validator = ExploitValidationService(metasploit_host, metasploit_pass)
            result = await validator.validate_exploit_proof(proof_to_validate)
            async with self:
                self.validation_results[proof_id] = result
                del self.validating_proofs[proof_id]
                status_to_update = result.get("status", "failure")
                evidence = result.get("evidence", {"error": result.get("logs")})
            await supabase_client.update_validation_status(
                proof_id, status_to_update, evidence
            )
            yield rx.toast.success(
                f"Validation for {proof_to_validate['title']} completed: {status_to_update}"
            )
        except Exception as e:
            logger.exception(f"Validation process failed for proof {proof_id}: {e}")
            async with self:
                if proof_id in self.validating_proofs:
                    del self.validating_proofs[proof_id]
                self.validation_results[proof_id] = {
                    "status": "failure",
                    "logs": str(e),
                }
            await supabase_client.update_validation_status(
                proof_id, "failure", {"error": str(e)}
            )
            yield rx.toast.error("Validation process encountered a critical error.")