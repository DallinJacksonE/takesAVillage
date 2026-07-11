from dataclasses import dataclass

from ..goap_actions import PlannedAction
from ..goals import GOAPGoal


@dataclass(frozen=True)
class DecisionTrace:
    """Compact explanation for a selected GOAP goal/action pair."""

    goal: str
    action_command: str
    action_score: float
    goal_utility: float
    total_score: float
    explanation: dict

    @classmethod
    def from_plan(cls, goal: GOAPGoal, planned: PlannedAction,
                  goal_utility: float, total_score: float):
        return cls(
            goal=goal.name,
            action_command=str(planned.server_action.get("action_command")),
            action_score=planned.score,
            goal_utility=goal_utility,
            total_score=total_score,
            explanation=planned.explanation or {},
        )

    def as_dict(self) -> dict:
        data = dict(self.explanation)
        data.update({
            "goal": self.goal,
            "action_command": self.action_command,
            "action_score": self.action_score,
            "goal_utility": self.goal_utility,
            "total_score": self.total_score,
        })
        return data
