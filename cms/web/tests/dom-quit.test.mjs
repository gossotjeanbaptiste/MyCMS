// Tests des utilitaires (appels à l'API, messages, boutons) et du contenu de la fenêtre Quitter

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { api, element, plural, toast, withButton } from "../static/scripts/core/dom.js";
import { buildQuitItems, quitSelection, updateQuitButton } from "../static/scripts/quit/quit-content.js";

const realFetch = globalThis.fetch;
const reply = (status, body) => { globalThis.fetch = async () => new Response(JSON.stringify(body), { status }); };

afterEach(() => { globalThis.fetch = realFetch; });

// ======= Utilitaires =======

test("api envoie du JSON et renvoie la réponse", async () => {
    let sent;
    globalThis.fetch = async (url, options) => { sent = { url, options }; return Response.json({ success: true, x: 1 }); };
    assert.deepEqual(await api("POST", "/api/config", { a: 1 }), { success: true, x: 1 });
    assert.equal(sent.options.headers["Content-Type"], "application/json");
    assert.equal(sent.options.body, '{"a":1}');
});

test("api : message d'erreur du serveur", async () => {
    reply(409, { success: false, error: "Le fichier a été modifié" });
    await assert.rejects(api("GET", "/x"), { message: "Le fichier a été modifié" });
    reply(500, {});
    await assert.rejects(api("GET", "/x"), { message: "Erreur HTTP 500" });
    reply(200, { success: false, message: "Refusé" });
    await assert.rejects(api("GET", "/x"), { message: "Refusé" });
});

test("api : session expirée, retour à la page de connexion", async () => {
    reply(401, { error: "Session expirée" });
    await assert.rejects(api("GET", "/x"), { message: "Session expirée : reconnectez-vous" });
    assert.equal(globalThis.redirectedTo, "/login");
});

test("withButton désactive le bouton pendant l'action et affiche l'erreur", async () => {
    const button = document.createElement("button");
    let during;
    await withButton(button, async () => { during = button.disabled; throw new Error("Échec du push"); });
    assert.equal(during, true);
    assert.equal(button.disabled, false);
    assert.equal(document.querySelector("#toasts .toast.error").textContent, "Échec du push");
});

test("toast, element et plural", () => {
    toast("Sauvegardé");
    assert.equal(document.querySelector("#toasts .toast:not(.error)").textContent, "Sauvegardé");
    const p = element("p", "text-muted", "Bonjour");
    assert.equal(p.outerHTML, '<p class="text-muted">Bonjour</p>');
    assert.equal(plural(1, "commit"), "1 commit");
    assert.equal(plural(3, "commit"), "3 commits");
    assert.equal(plural(2, "élément modifié", "éléments modifiés"), "2 éléments modifiés");
});

// ======= Fenêtre Quitter =======

const GIT = { available: true };
const pending = (overrides) => ({ dirty: 0, file: "index.html", git: GIT, files: [], untracked: [], ahead: 0, ...overrides });
const show = (check, data) => {
    document.getElementById("quit-content").replaceChildren(...buildQuitItems(check, data, () => {}));
    return document.getElementById("quit-content");
};
const choices = (content) => [...content.querySelectorAll('input[name="quit-choice"]')].map((r) => r.value);

test("rien à faire : message rassurant, aucun choix", () => {
    const content = show({ preview_running: false }, pending({}));
    assert.match(content.textContent, /Tout est sauvegardé et publié/);
    assert.deepEqual(choices(content), []);
    assert.equal(quitSelection(), "quit");
});

test("modifications non sauvegardées et fichiers non publiés : les trois choix", () => {
    const files = [{ state: "M", path: "index.html" }, { state: "??", path: "nouveau.html" }];
    const content = show({ preview_running: true }, pending({ dirty: 2, files, untracked: [files[1]], ahead: 1 }));
    assert.deepEqual(choices(content), ["discard", "save", "publish"]);
    assert.match(content.textContent, /2 éléments modifiés pas encore sauvegardés/);
    assert.match(content.textContent, /nouveau\.html : nouveau, sauvegardé mais pas publié/);
    assert.match(content.textContent, /1 commit pas encore envoyé/);
    assert.match(content.textContent, /serveur de prévisualisation sera arrêté/);
    assert.ok(content.querySelector("#quit-clean"));  // Case pour supprimer les nouveaux fichiers
    assert.equal(content.querySelector("#quit-message").value, "Mise à jour du contenu");
    assert.equal(content.querySelectorAll("#quit-content .btn").length, 2);  // Messages préfaits recopiés
});

test("commits en attente seulement : publier sans message de commit", () => {
    const content = show({}, pending({ ahead: 2 }));
    assert.deepEqual(choices(content), ["save", "publish"]);
    assert.equal(content.querySelector("#quit-message"), null);
    assert.match(content.textContent, /Envoie sur GitHub les commits en attente/);
});

test("sans Git : pas de publication, l'explication est affichée", () => {
    const content = show({}, pending({ dirty: 1, git: { available: false, message: "Git est introuvable" } }));
    assert.deepEqual(choices(content), ["discard", "save"]);
    assert.match(content.textContent, /Git est introuvable/);
});

test("le bouton suit le choix", () => {
    const content = show({}, pending({ dirty: 1, files: [{ state: "M", path: "index.html" }] }));
    const button = document.getElementById("quit-confirm");
    content.querySelector('input[value="discard"]').checked = true;
    updateQuitButton(1);
    assert.equal(button.textContent, "Annuler les modifications et quitter");
    assert.ok(button.classList.contains("btn-danger"));
    content.querySelector('input[value="save"]').checked = true;
    updateQuitButton(0);
    assert.equal(button.textContent, "Quitter sans publier");
    assert.ok(button.classList.contains("btn-primary") && !button.classList.contains("btn-danger"));
});
