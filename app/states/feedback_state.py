import reflex as rx
from typing import TypedDict, Literal, Optional
import logging
from datetime import datetime, timezone
from app.utils import supabase_client
from app.state import AppState
from app.states.auth_state import AuthState


class FeedbackLabel(TypedDict):
    id: int
    finding_id: int
    user_id: str
    label: Literal["exploitable", "false_positive", "uncertain"]
    confidence: int
    notes: Optional[str]
    created_at: str


class FeedbackState(rx.State):
    """Manages the Human-in-the-Loop feedback system."""

    is_submitting: bool = False
    feedback_for_finding: Optional[FeedbackLabel] = None
    last_submitted_label: str = ""
    error_message: str = ""

    @rx.event(background=True)
    async def get_feedback_for_finding(self, finding_id: int):
        """Retrieve the current user's feedback for a specific finding."""
        async with self:
            self.feedback_for_finding = None
            auth_state = await self.get_state(AuthState)
            user_id = auth_state.user_id
        if not user_id or not finding_id:
            return
        try:
            feedback = await supabase_client.get_user_feedback_for_finding(
                finding_id, user_id
            )
            if feedback:
                async with self:
                    self.feedback_for_finding = feedback
        except Exception as e:
            logging.exception(f"Failed to get feedback for finding {finding_id}: {e}")

    @rx.event(background=True)
    async def submit_feedback(
        self, finding_id: int, label: str, confidence: int, notes: str
    ):
        """Submit feedback for a finding."""
        async with self:
            self.is_submitting = True
            app_state = await self.get_state(AppState)
            auth_state = await self.get_state(AuthState)
            org_id = app_state.active_organization_id
            user_id = auth_state.user_id
        if not all([org_id, user_id, finding_id]):
            async with self:
                self.is_submitting = False
            yield rx.toast.error("Missing required information to submit feedback.")
            return
        try:
            feedback_id = await supabase_client.submit_feedback_label(
                finding_id=finding_id,
                org_id=org_id,
                user_id=user_id,
                label=label,
                confidence=confidence,
                notes=notes,
            )
            if feedback_id:
                async with self:
                    self.feedback_for_finding = {
                        "id": feedback_id,
                        "finding_id": finding_id,
                        "user_id": user_id,
                        "label": label,
                        "confidence": confidence,
                        "notes": notes,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    self.last_submitted_label = label
                yield rx.toast.success(f"Feedback '{label}' submitted successfully!")
            else:
                raise Exception("Feedback submission returned no ID.")
        except Exception as e:
            logging.exception(f"Failed to submit feedback: {e}")
            yield rx.toast.error("An error occurred while submitting feedback.")
        finally:
            async with self:
                self.is_submitting = False

    @rx.event(background=True)
    async def undo_feedback(self):
        """Retract the last feedback submission for the current finding."""
        if not self.feedback_for_finding:
            return
        feedback_id = self.feedback_for_finding["id"]
        async with self:
            self.is_submitting = True
            auth_state = await self.get_state(AuthState)
            user_id = auth_state.user_id
        if not user_id:
            async with self:
                self.is_submitting = False
            return
        try:
            success = await supabase_client.delete_feedback(feedback_id, user_id)
            if success:
                async with self:
                    self.feedback_for_finding = None
                    self.last_submitted_label = ""
                yield rx.toast.info("Feedback has been retracted.")
            else:
                yield rx.toast.error("Failed to undo feedback.")
        except Exception as e:
            logging.exception(f"Failed to undo feedback: {e}")
        finally:
            async with self:
                self.is_submitting = False