// Aller-retour dans l'éditeur, pour le test Python cms/tests/test_roundtrip.py :
// lit sur l'entrée standard les éléments d'une page (comme les renvoie /api/files/<page>),
// les fait passer par les vraies fonctions buildRichEditor puis serializeRich,
// et écrit sur la sortie standard les valeurs que l'éditeur renverrait au serveur, par index.

import "./setup-dom.mjs";
import { buildRichEditor, serializeRich, VOID_TAGS } from "../static/scripts/editor/rich-editor.js";

let input = "";
process.stdin.setEncoding("utf-8");
for await (const chunk of process.stdin) input += chunk;

const values = {};
for (const elem of JSON.parse(input)) {
    if (elem.is_iframe || elem.is_image) {
        values[elem.index] = elem.value;
    } else if (!VOID_TAGS.has(elem.tag)) {
        const built = buildRichEditor(elem);
        if (built) values[elem.index] = serializeRich(built.editor);
    }
}
process.stdout.write(JSON.stringify(values));
