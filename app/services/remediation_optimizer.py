import logging
from typing import Optional
from app.utils import supabase_client

logger = logging.getLogger(__name__)


class RemediationOptimizer:
    """AI-driven engine for optimizing remediation playbooks based on historical outcomes."""

    async def calculate_remediation_effectiveness_score(
        self, playbook_id: int
    ) -> float:
        """
        Calculates the Remediation Effectiveness Score (RES) for a given playbook.
        RES = (successful_verifications / total_attempts) * avg_confidence_score
        """
        try:
            outcomes = await supabase_client.get_remediation_outcomes_for_playbook(
                playbook_id
            )
            if not outcomes:
                return 0.0
            total_attempts = len(outcomes)
            successful_verifications = sum((1 for o in outcomes if o["was_successful"]))
            if total_attempts == 0:
                return 0.0
            avg_confidence = (
                sum(
                    (
                        o.get("verification_confidence", 0.75)
                        for o in outcomes
                        if o["was_successful"]
                    )
                )
                / successful_verifications
                if successful_verifications > 0
                else 0.0
            )
            success_rate = successful_verifications / total_attempts
            res = success_rate * avg_confidence
            logger.info(
                f"Calculated RES for playbook {playbook_id}: {res:.2f} (Success Rate: {success_rate:.2f}, Avg Confidence: {avg_confidence:.2f})"
            )
            return round(res, 4)
        except Exception as e:
            logger.exception(f"Failed to calculate RES for playbook {playbook_id}: {e}")
            return 0.0

    async def analyze_and_tune_playbook(self, playbook_id: int):
        """Analyzes playbook performance and suggests/applies optimizations."""
        try:
            playbook = await supabase_client.get_playbook_details(playbook_id)
            if not playbook:
                logger.warning(f"Playbook {playbook_id} not found for tuning.")
                return
            res_score = await self.calculate_remediation_effectiveness_score(
                playbook_id
            )
            if res_score < 0.75:
                optimization_type = "adjust_blast_radius"
                previous_config = {
                    "blast_radius_limit": playbook.get("blast_radius_limit", 10)
                }
                new_blast_radius = max(
                    1, int(playbook.get("blast_radius_limit", 10) * 0.8)
                )
                new_config = {"blast_radius_limit": new_blast_radius}
                reasoning = f"Remediation Effectiveness Score (RES) is low ({res_score:.2f}). Reducing blast radius from {previous_config['blast_radius_limit']} to {new_blast_radius} to improve success rate on smaller batches."
                await supabase_client.update_playbook_config(playbook_id, new_config)
                await supabase_client.log_playbook_optimization(
                    playbook_id=playbook_id,
                    optimization_type=optimization_type,
                    previous_config=previous_config,
                    new_config=new_config,
                    reasoning=reasoning,
                )
                logger.info(f"AI-tuned playbook {playbook_id}: {reasoning}")
        except Exception as e:
            logger.exception(f"Failed to tune playbook {playbook_id}: {e}")


remediation_optimizer = RemediationOptimizer()