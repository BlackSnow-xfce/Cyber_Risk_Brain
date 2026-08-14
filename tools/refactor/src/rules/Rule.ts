import { SourceFile } from "ts-morph";

export interface RuleResult {
    changed: boolean;
    changes: number;
}

export interface Rule {
    readonly name: string;

    run(
        sourceFile: SourceFile,
    ): RuleResult;
}