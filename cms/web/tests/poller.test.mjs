// Tests de l'interrogation régulière du serveur (v2.1.7) : seulement quand c'est utile

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, beforeEach, mock, test } from "node:test";
import { createPoller } from "../static/scripts/core/poller.js";

const flush = async () => { for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r)); };
const visibility = { hidden: false };
Object.defineProperty(document, "hidden", { configurable: true, get: () => visibility.hidden });

beforeEach(() => { visibility.hidden = false; mock.timers.enable({ apis: ["setTimeout"] }); });
afterEach(() => mock.timers.reset());

async function advance(ms) {
    mock.timers.tick(ms);
    await flush();
}

test("interroge à intervalle régulier tant que c'est actif, puis s'arrête", async () => {
    const calls = [];
    const condition = { active: true };
    const poller = createPoller(1000, async () => calls.push(1), () => condition.active);
    poller.start();
    await advance(1000);
    await advance(1000);
    assert.equal(calls.length, 2);
    condition.active = false;  // Ex. : serveur de prévisualisation arrêté
    await advance(5000);
    assert.equal(calls.length, 2);
});

test("en pause quand la fenêtre est cachée, reprise tout de suite au retour", async () => {
    const calls = [];
    const poller = createPoller(1000, async () => calls.push(1), () => true);
    poller.start();
    visibility.hidden = true;
    await advance(5000);
    assert.equal(calls.length, 0);
    visibility.hidden = false;
    document.dispatchEvent(new window.Event("visibilitychange"));
    await flush();
    assert.equal(calls.length, 1);
    await advance(1000);
    assert.equal(calls.length, 2);
    poller.stop();
    await advance(5000);
    assert.equal(calls.length, 2);
});

test("une erreur (serveur injoignable) arrête l'interrogation", async () => {
    const calls = [];
    const poller = createPoller(1000, async () => { calls.push(1); throw new Error("injoignable"); }, () => true);
    poller.start();
    await advance(1000);
    await advance(5000);
    assert.equal(calls.length, 1);
});
