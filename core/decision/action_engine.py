from __future__ import annotations

from core.decision.models import (
    DecisionAction,
    DecisionPriority,
)


class ActionEngine:
    """
    Determines the required action from the calculated priority.
    """

    def calculate(
        self,
        priority: DecisionPriority,
    ) -> DecisionAction:

        mapping = {

            DecisionPriority.CRITICAL:
                DecisionAction.REMEDIATE_NOW,

            DecisionPriority.HIGH:
                DecisionAction.REMEDIATE_PLANNED,

            DecisionPriority.MEDIUM:
                DecisionAction.MITIGATE,

            DecisionPriority.LOW:
                DecisionAction.MONITOR,

            DecisionPriority.INFORMATIONAL:
                DecisionAction.ACCEPT,
        }

        return mapping[priority]