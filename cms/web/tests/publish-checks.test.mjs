// Tests de la publication plus sûre (v2.1.3) : vérification avant push, mise en ligne, conflits

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import { bindPublishChecks, confirmPublication, formatProblems, showConflict, watchOnline } from "../static/scripts/git/publish-checks.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;
const PROBLEM = { page: "page/financement.html", line: 352, message: "Fichier introuvable : ../files/a.pdf" };
const flush = async () => { for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r)); };

afterEach(() => { globalThis.fetch = realFetch; mock.timers.reset(); });

test("format des problèmes", () => {
    assert.equal(formatProblems([PROBLEM]), "• page/financement.html, ligne 352 : Fichier introuvable : ../files/a.pdf");
});

test("aucun problème : la publication continue sans question", async () => {
    globalThis.fetch = async () => Response.json({ success: true, pages: ["index.html"], problems: [] });
    globalThis.confirm = () => assert.fail("pas de question attendue");
    assert.equal(await confirmPublication(), true);
});

test("des problèmes : ils sont affichés et l'utilisateur choisit", async () => {
    globalThis.fetch = async () => Response.json({ success: true, pages: [], problems: [PROBLEM] });
    let asked = "";
    globalThis.confirm = (text) => { asked = text; return false; };
    assert.equal(await confirmPublication(), false);
    assert.match(asked, /1 problème trouvé[\s\S]*Publier quand même/);
    // Liste en rouge sous les boutons, avec la page, la ligne et le problème
    assert.equal($("check-results").className, "check-results error");
    assert.match($("check-results").textContent, /Avant la publication : 1 problème trouvé/);
    assert.match($("check-results").textContent, /page\/financement\.html, ligne 352 : Fichier introuvable/);
});

test("suivi de la mise en ligne jusqu'à ce que toutes les pages soient à jour", async () => {
    mock.timers.enable({ apis: ["setTimeout", "Date"] });
    const answers = [{ online: [], waiting: ["index.html"] }, { online: ["index.html"], waiting: [] }];
    const urls = [];
    globalThis.fetch = async (url) => { urls.push(url); return Response.json({ success: true, base_url: "https://site.fr", ...answers.shift() }); };
    watchOnline(["index.html"]);
    assert.match($("online-status").textContent, /Mise en ligne en cours/);
    mock.timers.tick(10000);
    await flush();
    assert.match($("online-status").textContent, /0 \/ 1 page/);
    mock.timers.tick(10000);
    await flush();
    assert.equal($("online-status").textContent, "✓ En ligne sur https://site.fr (1 page)");
    assert.equal(urls[0], "/api/online?page=index.html");
});

test("rien d'envoyé : pas de suivi", () => {
    watchOnline([]);
    assert.ok($("online-status").classList.contains("hidden"));
});

test("conflit : le bouton « Reprendre la version en ligne » apparaît", async () => {
    showConflict(true);
    assert.ok(!$("git-reset-remote").classList.contains("hidden"));
    let reset = false;
    bindPublishChecks({ afterReset: async () => { reset = true; } });
    globalThis.confirm = () => true;
    globalThis.fetch = async () => Response.json({ success: true, message: "✓ Version en ligne reprise" });
    $("git-reset-remote").click();
    await flush();
    assert.ok(reset && $("git-reset-remote").classList.contains("hidden"));
    globalThis.fetch = async () => Response.json({ success: true, pages: ["a.html", "b.html"], problems: [] });
    $("git-check").click();
    await flush();
    assert.equal($("check-results").className, "check-results ok");
    assert.equal($("check-results").textContent, "✓ Aucun problème trouvé (2 pages vérifiées).");
    globalThis.fetch = async () => Response.json({ success: true, pages: ["a.html"], problems: [PROBLEM, PROBLEM] });
    $("git-check").click();
    await flush();
    assert.equal($("check-results").className, "check-results error");
    assert.equal($("check-results").querySelectorAll("li").length, 2);
    // Message en rouge, qui dit où est la liste
    assert.match(document.querySelector("#toasts .toast.error:last-child").textContent, /2 problèmes trouvés : la liste est sous les boutons/);
});
