from .asset_resolver import AssetResolver
from .correlation.engine import CorrelationEngine
from .context_builder import ContextBuilder
from .risk.engine import RiskEngine
from .story.generator import StoryGenerator


class Pipeline:

    def __init__(self):

        self.resolver = AssetResolver()
        self.builder = ContextBuilder()
        self.correlation = CorrelationEngine()
        self.risk = RiskEngine()
        self.story = StoryGenerator()

    def process(self, findings):

        assets = self.resolver.resolve(findings)

        results = []

        for asset_name, asset_findings in assets.items():

            context = self.builder.build(asset_findings)

            correlations = self.correlation.correlate(asset_findings)

            risk = self.risk.calculate(
                asset_name,
                context,
                correlations
            )

            story = self.story.generate(
                asset_name,
                {
                    "score": risk.score,
                    "reasons": risk.reasons
                }
            )

            results.append({

                "asset": asset_name,

                "risk": risk,

                "story": story

            })

        return results
