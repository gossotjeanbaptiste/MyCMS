// Tests de l'onglet Logs (v2.1.7) : seulement les nouvelles lignes, journal complet à l'ouverture

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { initLogs, stopLogsPolling } from "../static/scripts/settings/logs.js";
import { initTabs } from "../static/scripts/core/tabs.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;
const flush = async () => { for (let i = 0; i < 5; i++) await new Promise((r) => setImmediate(r)); };

document.body.insertAdjacentHTML("beforeend", `<button class="tab" data-tab="logs"></button>
    <section id="tab-logs" class="panel"><pre id="logs-output"></pre><button id="logs-clear"></button>
    <button id="logs-export"></button></section>`);
initTabs();
initLogs();

afterEach(() => { globalThis.fetch = realFetch; stopLogsPolling(); });

test("ouverture : tout le journal ; ensuite : seulement les nouvelles lignes", async () => {
    const urls = [];
    const answers = [{ logs: ["un", "deux"], total: 2, reset: true }, { logs: ["trois"], total: 3, reset: false },
        { logs: [], total: 3, reset: false }];
    globalThis.fetch = async (url) => { urls.push(url); return Response.json(answers.shift()); };
    document.querySelector('[data-tab="logs"]').click();
    await flush();
    assert.equal($("logs-output").textContent, "un\ndeux");
    await new Promise((r) => setTimeout(r, 1100));
    await flush();
    assert.equal($("logs-output").textContent, "un\ndeux\ntrois");
    assert.deepEqual(urls.slice(0, 2), ["/api/logs", "/api/logs?since=2"]);
});

test("« Effacer » : le journal repart de zéro", async () => {
    const urls = [];
    globalThis.fetch = async (url, options = {}) => {
        urls.push(`${options.method || "GET"} ${url}`);
        return Response.json(options.method === "DELETE" ? { success: true } : { logs: [], total: 3, reset: true });
    };
    $("logs-clear").click();
    await flush();
    assert.equal($("logs-output").textContent, "");
    assert.deepEqual(urls, ["DELETE /api/logs", "GET /api/logs"]);
});
