// Tests de l'historique lisible et de « Mon compte » (v2.1.4)

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { describe, refreshHistory } from "../static/scripts/git/history.js";
import { initAccount } from "../static/scripts/settings/account.js";
import { initTabs } from "../static/scripts/core/tabs.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;
const flush = async () => { for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r)); };
const entry = (overrides) => ({ hash: "abc1234", author: "Marie", date: "2026-11-12T14:03:00+01:00",
    message: "Mise à jour des tarifs", pages: ["page/tarifs.html"], other_files: 0, published: true, ...overrides });

afterEach(() => { globalThis.fetch = realFetch; });

test("phrase d'une modification", () => {
    assert.equal(describe(entry({})), "Marie a modifié page/tarifs.html");
    assert.equal(describe(entry({ pages: ["a.html", "b.html", "c.html", "d.html"], other_files: 1 })),
        "Marie a modifié a.html, b.html, c.html (et 1 autre page, 1 autre fichier)");
    assert.equal(describe(entry({ pages: [], other_files: 2 })), "Marie a modifié 2 fichiers");
    assert.equal(describe(entry({ pages: [], other_files: 0 })), "Marie a modifié aucun fichier");
});

test("historique affiché avec l'état de publication et la date en français", async () => {
    globalThis.fetch = async () => Response.json({ success: true, entries: [entry({}), entry({ published: false })] });
    await refreshHistory();
    const items = [...$("git-history").children];
    assert.equal(items.length, 2);
    assert.match(items[0].textContent, /Marie a modifié page\/tarifs\.htmlPublié/);
    assert.match(items[0].textContent, /le 12 novembre 2026 à \d{2}:03 · « Mise à jour des tarifs » · abc1234/);
    assert.match(items[1].textContent, /Pas encore publié/);
});

test("historique vide ou indisponible", async () => {
    globalThis.fetch = async () => Response.json({ success: false, error: "Pas de repository" }, { status: 500 });
    await refreshHistory();
    assert.equal($("git-history").textContent, "Aucune modification enregistrée.");
});

test("« Mon compte » : chargement à l'ouverture des paramètres, puis enregistrement", async () => {
    const sent = [];
    globalThis.fetch = async (url, options = {}) => {
        if (options.method === "POST") sent.push(JSON.parse(options.body));
        return Response.json(options.method === "POST" ? { success: true, message: "Profil enregistré" }
            : { name: "Marie Dupont", email: "", author: "Marie Dupont <Marie@mycms.local>" });
    };
    document.body.insertAdjacentHTML("beforeend", '<button class="tab" data-tab="settings"></button><section id="tab-settings" class="panel"></section>');
    initTabs();
    initAccount();
    document.querySelector('[data-tab="settings"]').click();
    await flush();
    assert.equal($("account-name").value, "Marie Dupont");
    assert.equal($("account-author").textContent, "Vos publications sont signées : Marie Dupont <Marie@mycms.local>");
    $("account-email").value = "marie@rout-art.fr";
    $("account-save").click();
    await flush();
    assert.deepEqual(sent, [{ name: "Marie Dupont", email: "marie@rout-art.fr" }]);
});
