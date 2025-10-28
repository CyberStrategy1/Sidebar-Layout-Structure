import reflex as rx
from typing import Literal, Optional, TypedDict

Question = Literal["exploitation", "technical_impact", "automatable", "mission_impact"]
Answer = Literal[
    "active",
    "poc",
    "none",
    "total",
    "partial",
    "yes",
    "no",
    "critical",
    "high",
    "medium",
    "low",
]
Decision = Literal["Track", "Track*", "Attend", "Act"]


class Option(TypedDict):
    value: Answer
    label: str


class QuestionData(TypedDict):
    text: str
    options: list[Option]


QUESTIONS: dict[Question, QuestionData] = {
    "exploitation": {
        "text": "What is the status of exploitation?",
        "options": [
            {"value": "active", "label": "Active"},
            {"value": "poc", "label": "PoC"},
            {"value": "none", "label": "None"},
        ],
    },
    "technical_impact": {
        "text": "What is the technical impact of a successful exploitation?",
        "options": [
            {"value": "total", "label": "Total"},
            {"value": "partial", "label": "Partial"},
        ],
    },
    "automatable": {
        "text": "Is the exploitation process automatable?",
        "options": [{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}],
    },
    "mission_impact": {
        "text": "What is the mission and well-being impact of a security failure?",
        "options": [
            {"value": "critical", "label": "Critical"},
            {"value": "high", "label": "High"},
            {"value": "medium", "label": "Medium"},
            {"value": "low", "label": "Low"},
        ],
    },
}


class SsvcCalculatorState(rx.State):
    """State for the SSVC Calculator Tool."""

    current_step: int = 0
    answers: dict[Question, Optional[Answer]] = {
        "exploitation": None,
        "technical_impact": None,
        "automatable": None,
        "mission_impact": None,
    }

    @rx.var
    def active_question_key(self) -> str:
        """Get the key for the current question based on the step."""
        if self.current_step >= len(QUESTIONS):
            return ""
        return list(QUESTIONS.keys())[self.current_step]

    @rx.var
    def active_question(self) -> QuestionData:
        """Get the data for the current active question."""
        if self.active_question_key:
            return QUESTIONS[self.active_question_key]
        return {"text": "", "options": []}

    @rx.event
    def select_answer(self, answer: str):
        """Record the user's answer and advance to the next step."""
        if self.active_question_key:
            self.answers[self.active_question_key] = answer
            self.current_step += 1

    @rx.event
    def go_to_step(self, step_index: int):
        """Navigate to a specific step, clearing subsequent answers."""
        self.current_step = step_index
        keys_to_reset = list(QUESTIONS.keys())[step_index:]
        for key in keys_to_reset:
            self.answers[key] = None

    @rx.event
    def reset_calculator(self):
        """Reset the calculator to its initial state."""
        self.current_step = 0
        self.answers = {
            "exploitation": None,
            "technical_impact": None,
            "automatable": None,
            "mission_impact": None,
        }

    @rx.var
    def decision(self) -> Optional[Decision]:
        """Calculate the SSVC decision based on the user's answers."""
        if self.current_step < len(QUESTIONS):
            return None
        expl = self.answers["exploitation"]
        tech = self.answers["technical_impact"]
        auto = self.answers["automatable"]
        mission = self.answers["mission_impact"]
        if expl == "active":
            return "Act"
        if expl == "poc":
            if mission in ["critical", "high"]:
                return "Act"
            if mission == "medium":
                return "Attend"
            if mission == "low":
                return "Track"
        if expl == "none":
            if tech == "total":
                if auto == "yes":
                    if mission in ["critical", "high"]:
                        return "Attend"
                    return "Track*"
                else:
                    return "Track*"
            else:
                return "Track"
        return "Track"

    @rx.var
    def decision_rationale(self) -> str:
        """Provide a human-readable explanation for the calculated decision."""
        d = self.decision
        if not d:
            return ""
        if d == "Act":
            if self.answers["exploitation"] == "active":
                return "The vulnerability is actively being exploited in the wild. Immediate action is required to mitigate the threat."
            return "Proof-of-concept exploit code is available, and the potential mission impact is high or critical. This combination warrants immediate action."
        if d == "Attend":
            if self.answers["exploitation"] == "poc":
                return "Proof-of-concept exploit code exists, and the mission impact is medium. This requires attention sooner rather than later."
            return "The vulnerability has total technical impact and is automatable, with a high or critical mission impact. It should be attended to promptly."
        if d == "Track*":
            return "The vulnerability has a high potential for future exploitation (total impact) but no known exploits exist yet. It should be closely monitored and patched on an accelerated timeline."
        if d == "Track":
            return "The vulnerability has limited technical impact or low mission impact, with no publicly available exploit code. Standard patching procedures are sufficient."
        return "Decision process complete. Review details above."

    @rx.var
    def decision_colors(self) -> dict[str, str]:
        """Provides Tailwind CSS classes for color-coding decisions."""
        return {
            "Act": "text-red-400",
            "Attend": "text-orange-400",
            "Track*": "text-yellow-400",
            "Track": "text-green-400",
        }