import {
    JsxAttribute,
    JsxOpeningElement,
    SyntaxKind,
} from "ts-morph";

const STACK_PROPS = [
    "justifyContent",
    "alignItems",
    "flexWrap",
    "alignSelf",
    "justifySelf",
];

export function migrateStackProps(
    openingElement: JsxOpeningElement,
): boolean {
    if (openingElement.getTagNameNode().getText() !== "Stack") {
        return false;
    }

    let changed = false;

    const sx = openingElement
        .getAttributes()
        .find(
            (a) =>
                a.getKind() === SyntaxKind.JsxAttribute &&
                (a as JsxAttribute).getName() === "sx",
        ) as JsxAttribute | undefined;

    const collected: string[] = [];

    for (const prop of STACK_PROPS) {
        const attr = openingElement
            .getAttributes()
            .find(
                (a) =>
                    a.getKind() === SyntaxKind.JsxAttribute &&
                    (a as JsxAttribute).getName() === prop,
            ) as JsxAttribute | undefined;

        if (!attr) {
            continue;
        }

        const initializer = attr.getInitializer();

        if (!initializer) {
            continue;
        }

        const value = initializer
            .getText()
            .replace(/^{|}$/g, "");

        collected.push(`${prop}: ${value}`);

        attr.remove();

        changed = true;
    }

    if (!changed) {
        return false;
    }

    if (!sx) {
        openingElement.addAttribute({
            name: "sx",
            initializer: `{{ ${collected.join(", ")} }}`,
        });

        return true;
    }

    const init = sx.getInitializer();

    if (!init) {
        return true;
    }

    const text = init.getText();

    const merged = text.replace(
        /}\s*$/,
        `, ${collected.join(", ")} }`,
    );

    init.replaceWithText(merged);

    return true;
}