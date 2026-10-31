// Tous les modules de l'interface se chargent (pas d'erreur de syntaxe ni d'import cassé),
// et respectent les règles du projet : 200 lignes au plus, rien posé sur window.

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPTS = fileURLToPath(new URL("../static/scripts/", import.meta.url));
// Points d'entrée (ils démarrent l'interface) et script injecté dans les pages du site
const NOT_IMPORTED = new Set(["main.js", "login.js", join("preview", "preview-helper.js")]);

function scripts(dir = SCRIPTS) {
    return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
        const path = join(dir, entry.name);
        return entry.isDirectory() ? scripts(path) : entry.name.endsWith(".js") ? [path] : [];
    });
}

for (const path of scripts()) {
    const name = relative(SCRIPTS, path);
    test(`${name} : 200 lignes au plus, sans variable globale`, async () => {
        const source = readFileSync(path, "utf-8");
        assert.ok(source.split("\n").length <= 201, `${source.split("\n").length} lignes`);
        assert.doesNotMatch(source, /window\.\w+\s*=[^=]/, "pas d'état posé sur window");
        if (!NOT_IMPORTED.has(name)) {
            const module = await import(pathToFileURL(path));
            assert.ok(Object.keys(module).length > 0, "le module exporte ses fonctions");
        }
    });
}

test("chaque module de fonctionnalité exporte sa fonction init…() appelée par main.js", () => {
    const main = readFileSync(join(SCRIPTS, "main.js"), "utf-8");
    const inits = [...main.matchAll(/\binit\w+\b/g)].map((m) => m[0]);
    for (const path of scripts()) {
        for (const [, name] of readFileSync(path, "utf-8").matchAll(/export function (init\w+)\(/g)) {
            assert.ok(inits.includes(name), `${name} (${relative(SCRIPTS, path)}) n'est pas appelée par main.js`);
        }
    }
});
