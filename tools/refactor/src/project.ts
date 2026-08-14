import path from "node:path";

import { Project } from "ts-morph";

export function createProject() {
    const root = path.resolve(
        process.cwd(),
        "..",
        "..",
    );

    const frontend = path.join(root, "frontend");

    const tsconfig = path.join(
        frontend,
        "tsconfig.json",
    );

    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log(" PredatorAI Refactor Engine");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log();

    console.log("Root       :", root);
    console.log("Frontend   :", frontend);
    console.log("TSConfig   :", tsconfig);
    console.log();

    return new Project({
        tsConfigFilePath: tsconfig,
        skipAddingFilesFromTsConfig: false,
    });
}