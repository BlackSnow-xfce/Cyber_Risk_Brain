import type { Rule } from "../Rule";
import type { RulePack } from "../RulePack";
import { unmatchedRuleResult } from "../RuleResult";
import {
    buildInferenceResult,
    createInference,
    getBoundKnowledge,
} from "../RuleUtilities";

const businessCriticalAttackPathRule: Rule = {
    id: "business-critical-attack-path",
    name: "Business-critical attack path",
    description:
        "Identifies business-critical entities with an explicit attack-path correlation.",
    priority: 20,
    enabled: true,
    evaluate: (context) => {
        const classification = getBoundKnowledge(
            context,
            "ASSET_CLASSIFICATION",
        );
        const attackPaths = context.correlations.filter(
            (correlation) => correlation.type === "SAME_ATTACK_PATH",
        );
        if (
            classification.bindingIds.length === 0 ||
            attackPaths.length === 0
        ) {
            return unmatchedRuleResult(
                "No business-critical classification or attack-path correlation.",
            );
        }

        return buildInferenceResult(
            createInference(
                context,
                "business-critical-attack-path",
                "CRITICAL_ASSET_EXPOSED",
                "Business-critical asset has an attack path",
                "Business-critical classification and an explicit attack-path correlation apply to the entity.",
                Math.min(...attackPaths.map((path) => path.confidence)),
                classification.knowledgeIds,
                classification.bindingIds,
                [],
                attackPaths.map((path) => path.id),
            ),
        );
    },
};

export const assetRulePack: RulePack = {
    id: "asset",
    name: "Asset Rules",
    description: "Rules for asset classification and exposure context.",
    version: "1.0.0",
    enabled: true,
    rules: [businessCriticalAttackPathRule],
};
