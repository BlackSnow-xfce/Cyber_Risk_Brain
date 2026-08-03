import { RulePackRegistry } from "./RulePackRegistry";
import {
    assetRulePack,
    exposureRulePack,
    investigationRulePack,
    kevRulePack,
    mitreRulePack,
    threatIntelRulePack,
} from "./packs";

export const defaultRulePackRegistry = new RulePackRegistry([
    kevRulePack,
    mitreRulePack,
    exposureRulePack,
    assetRulePack,
    investigationRulePack,
    threatIntelRulePack,
]);

export const defaultRules = defaultRulePackRegistry.getAllRules();
export const defaultRuleRegistry = defaultRulePackRegistry;
