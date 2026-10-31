// Tests du détail d'une modification de l'historique (v2.1.6)

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { refreshHistory } from "../static/scripts/git/history.js";
import { buildDetails } from "../static/scripts/git/history-details.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;
const flush = async () => { for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r)); };

const DETAILS = {
    hash: "abc1234", author: "Marie", date: "2026-11-12T14:03:00+01:00", message: "Mise à jour des tarifs",
    other_files: ["sitemap.xml"],
    pages: [{
        path: "page/tarifs.html", status: "modified", total: 4, diff: "@@ -1 +1 @@\n-<td>70€</td>\n+<td>75€</td>",
        changes: [
            { kind: "modified", tag: "td", category: "Permis B", before: "70€", after: "75€",
                words: [{ op: "del", text: "70€" }, { op: "ins", text: "75€" }] },
            { kind: "added", tag: "li", category: "Permis B", before: "", after: "Livre de code" },
            { kind: "removed", tag: "li", category: "Moto", before: "Ancienne ligne", after: "" },
        ],
    }, { path: "page/vide.html", status: "added", total: 0, changes: [], diff: "" }],
};

afterEach(() => { globalThis.fetch = realFetch; });

test("textes modifiés, ajoutés et supprimés, page par page", () => {
    const box = buildDetails(DETAILS);
    const items = [...box.querySelectorAll("ul li")];
    assert.deepEqual(items.map((li) => li.querySelector(".pub-badge").textContent), ["Modifié", "Ajouté", "Supprimé"]);
    assert.equal(items[0].querySelector(".diff-del").textContent, "70€");
    assert.equal(items[0].querySelector(".diff-ins").textContent, "75€");
    assert.match(items[0].textContent, /Permis B/);
    assert.equal(items[2].querySelector(".diff-del").textContent, "Ancienne ligne");
    assert.match(box.textContent, /… et 1 autre changement/);
    assert.match(box.textContent, /page\/vide\.html \(nouvelle page\)Aucun texte modifiable n'a changé/);
    assert.match(box.textContent, /Autres fichiers modifiés : sitemap\.xml/);
    const code = box.querySelector("details pre");
    assert.equal(code.querySelector(".diff-del").textContent, "-<td>70€</td>");
    assert.equal(code.querySelector(".diff-ins").textContent, "+<td>75€</td>");
});

test("mise en forme seule", () => {
    const box = buildDetails({ ...DETAILS, other_files: [], pages: [{ path: "a.html", status: "modified", total: 1,
        diff: "", changes: [{ kind: "formatted", tag: "p", category: "Accueil", before: "x", after: "x", words: [] }] }] });
    assert.match(box.textContent, /Mise en forme.*Même texte : le gras, l'italique ou un lien a changé/s);
});

test("clic sur une modification : détail chargé une fois, puis replié", async () => {
    const urls = [];
    globalThis.fetch = async (url) => {
        urls.push(url);
        return Response.json(url === "/api/git/history" ? { success: true, entries: [{ hash: "abc1234", author: "Marie",
            date: DETAILS.date, message: "Tarifs", pages: ["page/tarifs.html"], other_files: 1, published: true }] }
            : { success: true, ...DETAILS });
    };
    await refreshHistory();
    const button = $("git-history").querySelector(".history-summary");
    button.click();
    await flush();
    assert.equal(button.getAttribute("aria-expanded"), "true");
    assert.ok($("git-history").querySelector(".history-details:not(.hidden) .diff-ins"));
    button.click();
    assert.ok($("git-history").querySelector(".history-details").classList.contains("hidden"));
    button.click();
    await flush();
    assert.deepEqual(urls, ["/api/git/history", "/api/git/commit/abc1234"]);
});
