import { Rule } from "./Rule.js";

export class RuleRegistry {
    private readonly rules: Rule[] = [];

    register(rule: Rule) {
        this.rules.push(rule);
    }

    getRules() {
        return this.rules;
    }
}