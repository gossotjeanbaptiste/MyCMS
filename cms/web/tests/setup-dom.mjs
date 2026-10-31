// Tests de l'interface : DOM de jsdom mis à la place de celui du navigateur.
// À importer en premier : les modules de static/scripts utilisent document et window.

import { JSDOM } from "jsdom";

const dom = new JSDOM(`<!DOCTYPE html><html><head></head><body>
    <input id="search"><span id="search-count"></span>
    <div id="category-bar" class="hidden"></div>
    <div id="editable-list"></div>
    <span id="pub-legend" class="hidden"></span>
    <button id="quit-confirm"></button><div id="quit-content"></div>
    <input id="commit-message" value="">
    <div id="commit-presets"><button>Mise à jour des tarifs</button><button>Correction</button></div>
    <button id="save-file"></button><button id="reload-file"></button>
    <pre id="git-output"></pre><p id="online-status" class="hidden"></p><div id="check-results" class="hidden"></div>
    <button id="git-check"></button><button id="git-reset-remote" class="hidden"></button>
    <ul id="git-history"></ul><a id="update-link" class="hidden"></a>
    <input id="account-name"><input id="account-email"><p id="account-author"></p><button id="account-save"></button>
    <div id="toasts"></div>
</body></html>`, { url: "http://127.0.0.1:5050/", pretendToBeVisual: true });

const { window } = dom;
for (const name of ["window", "document", "Node", "NodeFilter", "Range", "Event", "HTMLElement", "Element"]) {
    globalThis[name] = name === "window" ? window : window[name];
}
// Absent de jsdom
window.Element.prototype.scrollIntoView = function scrollIntoView() {
    this.dataset.scrolled = "true";
};
// Redirection vers la page de connexion (session expirée) : notée au lieu d'être suivie
globalThis.location = { replace(url) { globalThis.redirectedTo = url; } };

export { dom };
