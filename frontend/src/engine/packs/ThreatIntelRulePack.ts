import type { Rule } from "../Rule";
import type { RulePack } from "../RulePack";
import { unmatchedRuleResult } from "../RuleResult";
import {
    buildInferenceResult,
    createInference,
    getBoundKnowledge,
} from "../RuleUtilities";

const threatCampaignBindingRule: Rule = {
    id: "threat-campaign-binding",
    name: "Threat campaign binding",
    description:
        "Identifies entities with explicitly bound threat-campaign knowledge.",
    priority: 30,
    enabled: true,
    evaluate: (context) => {
        const campaign = getBoundKnowledge(context, "THREAT_CAMPAIGN");
        if (campaign.bindingIds.length === 0) {
            return unmatchedRuleResult(
                "No threat-campaign knowledge binding.",
            );
        }

        const confidence = Math.min(
            ...context.knowledgeBindings
                .filter((binding) => campaign.bindingIds.includes(binding.id))
                .map((binding) => binding.confidence),
        );
        return buildInferenceResult(
            createInference(
                context,
                "threat-campaign-binding",
                "ACTIVE_CAMPAIGN_RELATED",
                "Active threat campaign is related",
                "Threat-campaign knowledge is explicitly bound to the entity.",
                confidence,
                campaign.knowledgeIds,
                campaign.bindingIds,
                [],
                [],
            ),
        );
    },
};

export const threatIntelRulePack: RulePack = {
    id: "threat-intelligence",
    name: "Threat Intelligence Rules",
    description: "Rules based on threat intelligence knowledge bindings.",
    version: "1.0.0",
    enabled: true,
    rules: [threatCampaignBindingRule],
};
