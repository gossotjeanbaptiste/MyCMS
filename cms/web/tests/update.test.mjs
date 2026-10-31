// Tests de l'annonce d'une nouvelle version (v2.1.5)

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { checkForUpdate } from "../static/scripts/settings/update.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;

afterEach(() => { globalThis.fetch = realFetch; });

test("nouvelle version : lien dans l'en-tête vers la release", async () => {
    globalThis.fetch = async () => Response.json({ available: true, current: "2.1.5", latest: "2.2.0",
        url: "https://github.com/gossotjeanbaptiste/MyCMS/releases/tag/v2.2.0" });
    await checkForUpdate();
    const link = $("update-link");
    assert.ok(!link.classList.contains("hidden"));
    assert.equal(link.textContent, "Nouvelle version 2.2.0");
    assert.equal(link.href, "https://github.com/gossotjeanbaptiste/MyCMS/releases/tag/v2.2.0");
    assert.match(link.title, /Vous avez MyCMS 2\.1\.5/);
});

test("à jour, ou pas de réseau : rien n'est affiché", async () => {
    globalThis.fetch = async () => Response.json({ available: false, current: "2.1.5", latest: null, url: null });
    await checkForUpdate();
    assert.ok($("update-link").classList.contains("hidden"));
    globalThis.fetch = async () => { throw new TypeError("Failed to fetch"); };
    await checkForUpdate();
    assert.ok($("update-link").classList.contains("hidden"));
});
