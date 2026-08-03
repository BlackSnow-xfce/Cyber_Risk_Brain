import type { Rule } from "./Rule";

export interface RulePack {
    id: string;
    name: string;
    description: string;
    version: string;
    enabled: boolean;
    rules: readonly Rule[];
}
