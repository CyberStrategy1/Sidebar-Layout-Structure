import reflex as rx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging
from datetime import datetime, timedelta, timezone
from app.utils import supabase_client

scheduler = AsyncIOScheduler()


async def scheduled_gap_analysis_job():
    """Execute gap analysis for all active organizations."""
    try:
        organizations = await supabase_client.get_all_active_organizations()
        logging.info(
            f"Starting scheduled gap analysis for {len(organizations)} organizations."
        )
        for org in organizations:
            try:
                last_run = await supabase_client.get_last_completed_run(org["id"])
                if last_run and last_run.get("run_completed_at"):
                    last_run_time = datetime.fromisoformat(last_run["run_completed_at"])
                    if datetime.now(timezone.utc) - last_run_time < timedelta(
                        minutes=5
                    ):
                        logging.info(
                            f"Skipping organization {org['id']} due to 5-minute cooldown."
                        )
                        continue
                from app.state import AppState

                temp_state = AppState()
                await temp_state.run_gap_analysis_engine(organization_id=org["id"])
                logging.info(
                    f"Successfully triggered gap analysis for organization {org['id']}."
                )
            except Exception as e:
                logging.exception(
                    f"Failed to process organization {org['id']} during scheduled job: {e}"
                )
                continue
    except Exception as e:
        logging.exception(f"Scheduled gap analysis job failed entirely: {e}")


def job_listener(event):
    """Log job execution results for monitoring."""
    if event.exception:
        logging.error(
            f"Scheduled job {event.job_id} failed with exception: {event.exception}"
        )
    else:
        logging.info(f"Scheduled job {event.job_id} completed successfully.")


def initialize_scheduler():
    """Set up and start the scheduler with defined jobs."""
    scheduler.add_job(
        scheduled_gap_analysis_job,
        CronTrigger(
            minute="*/5", hour="9-17", day_of_week="mon-fri", timezone="US/Eastern"
        ),
        id="high_frequency_scan",
        max_instances=1,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        scheduled_gap_analysis_job,
        CronTrigger(hour="18-23,0-8", day_of_week="mon-fri", timezone="US/Eastern"),
        id="medium_frequency_scan",
        max_instances=1,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scheduled_gap_analysis_job,
        CronTrigger(hour="*/4", day_of_week="sat-sun", timezone="US/Eastern"),
        id="low_frequency_scan",
        max_instances=1,
        misfire_grace_time=600,
    )
    scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
    from app.services.exploit_feed_scheduler import scheduled_exploit_feed_sync

    scheduler.add_job(
        scheduled_exploit_feed_sync,
        CronTrigger(hour="*/4"),
        id="exploit_feed_sync",
        max_instances=1,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scheduled_model_retraining,
        CronTrigger(hour="3", minute="0", timezone="UTC"),
        id="daily_model_retraining",
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        scheduled_proof_validation_job,
        CronTrigger(minute="*/15"),
        id="exploit_proof_validation",
        max_instances=1,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        scheduled_remediation_optimization,
        CronTrigger(hour="*/12"),
        id="playbook_optimization",
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logging.info("✅ APScheduler started successfully with scheduled jobs.")


async def scheduled_proof_validation_job():
    """Scheduled job to validate pending exploit proofs."""
    from app.states.proof_validation_state import ProofValidationState

    logger.info("Starting scheduled exploit proof validation job...")
    try:
        validation_state = ProofValidationState()
        await validation_state.load_pending_proofs()
        if ~validation_state.pending_proofs:
            logger.info("No pending proofs to validate.")
            return
        proof_to_validate = validation_state.pending_proofs[0]
        logger.info(f"Initiating validation for proof ID: {proof_to_validate['id']}")
        await validation_state.start_validation_for_proof(proof_to_validate["id"])
    except Exception as e:
        logger.exception(f"Scheduled proof validation job failed: {e}")


def shutdown_scheduler():
    """Gracefully shut down the scheduler on application exit."""
    if scheduler.running:
        scheduler.shutdown()
        logging.info("APScheduler has been shut down gracefully.")


async def scheduled_model_retraining():
    """Daily check for organizations that need their models retrained."""
    try:
        queued_orgs = await supabase_client.get_queued_retraining_jobs()
        logging.info(
            f"Found {len(queued_orgs)} organizations queued for model retraining."
        )
        for org in queued_orgs:
            org_id = org["organization_id"]
            try:
                from app.ml_training.retrain_worker import run_retraining_for_org

                logging.info(f"Starting retraining job for org {org_id}...")
                await run_retraining_for_org(org_id)
                logging.info(f"Retraining job completed for org {org_id}.")
            except Exception as e:
                logging.exception(f"Retraining job failed for org {org_id}: {e}")
                await supabase_client.update_retraining_status(org_id, "failed")
                continue
    except Exception as e:
        logging.exception(f"Scheduled model retraining job failed entirely: {e}")


async def scheduled_remediation_optimization():
    """Periodically run the remediation optimizer for all active playbooks."""
    from app.services.remediation_optimizer import remediation_optimizer

    logger.info("Starting scheduled remediation optimization job...")
    try:
        active_playbooks = await supabase_client.get_all_active_playbooks()
        for playbook in active_playbooks:
            await remediation_optimizer.analyze_and_tune_playbook(playbook["id"])
        logger.info(
            f"Remediation optimization check completed for {len(active_playbooks)} playbooks."
        )
    except Exception as e:
        logger.exception(f"Scheduled remediation optimization job failed: {e}")


async def scheduled_remediation_optimization():
    """Periodically run the remediation optimizer for all active playbooks."""
    from app.services.remediation_optimizer import remediation_optimizer

    logger.info("Starting scheduled remediation optimization job...")
    try:
        active_playbooks = await supabase_client.get_all_active_playbooks()
        for playbook in active_playbooks:
            await remediation_optimizer.analyze_and_tune_playbook(playbook["id"])
        logger.info(
            f"Remediation optimization check completed for {len(active_playbooks)} playbooks."
        )
    except Exception as e:
        logger.exception(f"Scheduled remediation optimization job failed: {e}")