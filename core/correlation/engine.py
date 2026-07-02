from ..context_builder import ContextBuilder
from .rules import RULES


class CorrelationEngine:

    def __init__(self):

        self.builder = ContextBuilder()

    def correlate(self, findings):

        context = self.builder.build(findings)

        correlations = []

        for rule in RULES:

            result = rule(context)

            if result:
                correlations.extend(result)

        return correlations
