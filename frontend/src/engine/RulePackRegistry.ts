import type { Rule } from "./Rule";
import type { RulePack } from "./RulePack";
import type { RuleRegistry } from "./RuleRegistry";

export class RulePackRegistry implements RuleRegistry {
    private readonly packs = new Map<string, RulePack>();

    constructor(packs: readonly RulePack[] = []) {
        packs.forEach((pack) => this.register(pack));
    }

    get rules(): readonly Rule[] {
        return this.getAllRules();
    }

    register(pack: RulePack): void {
        this.packs.set(pack.id, pack);
    }

    unregister(packId: string): void {
        this.packs.delete(packId);
    }

    getEnabledRulePacks(): readonly RulePack[] {
        return [...this.packs.values()].filter((pack) => pack.enabled);
    }

    getAllRules(): readonly Rule[] {
        return this.getEnabledRulePacks().flatMap((pack) => pack.rules);
    }
}
