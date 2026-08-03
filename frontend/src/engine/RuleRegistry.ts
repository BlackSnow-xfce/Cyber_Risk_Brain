import type { Rule } from "./Rule";

export interface RuleRegistry {
    readonly rules: readonly Rule[];
}
