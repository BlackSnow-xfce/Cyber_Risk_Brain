from __future__ import annotations

from core.decision.decision_card import DecisionCard

from dashboard.viewmodels.decision_console import (
    DecisionConsoleViewModel,
)


class DecisionConsoleBuilder:
    """
    Converts a DecisionCard into the
    Dashboard ViewModel.
    """

    def build(
        self,
        card: DecisionCard,
    ) -> DecisionConsoleViewModel:

        return DecisionConsoleViewModel(

            title=card.title,

            decision=card.decision,

            priority=card.priority,

            risk_score=card.risk_score,

            confidence=card.confidence.score,

            confidence_label=(
                f"{card.confidence.score:.0f}%"
            ),

            ai_verdict=card.ai_verdict,

            business_impact=(
                card.business_impact.summary
                if card.business_impact
                else ""
            ),

            estimated_loss=(
                f"€ {card.business_impact.estimated_loss:,.0f}"
                if card.business_impact
                else "-"
            ),

            executive_summary=(
                card.executive_summary
            ),

            reasons=[
                item.title
                for item in card.reasons
            ],

            recommendations=[
                item.title
                for item in card.recommendations
            ],

            counter_arguments=(
                card.counter_arguments
            ),
        )
    