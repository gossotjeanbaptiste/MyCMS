// MyCMS - aperçu en direct : la page du site avec les modifications non sauvegardées, ou le code de l'élément

import { $, api, toast } from "../core/dom.js";
import { dirtyValues } from "../editor/editor.js";
import { paneMessage, refreshSnippet, setPaneInfo } from "./pane-code.js";
import { showPreview } from "./preview.js";
import { revealCard } from "../editor/categories.js";
import { state } from "../core/state.js";

const pane = {
    open: false,
    mode: "page", // "page" : page du site, "code" : code source de l'élément
    index: null, // Dernier élément cliqué dans l'éditeur ou dans la page
    timer: null,
    frameReady: false, // Le script d'aperçu de la page a répondu
    frameOrigin: "",
    frameKey: null, // Fichier et version chargés dans l'aperçu
    frameScroll: 0,
    frameInfo: "",
};

function postToFrame(message) {
    if (pane.frameReady) $("preview-frame").contentWindow.postMessage({ mycms: true, ...message }, pane.frameOrigin);
}

// Nouvelle page ouverte : plus d'élément sélectionné
export function forgetPaneElement() {
    pane.index = null;
}

// La page est servie par le serveur de prévisualisation (démarré si besoin), avec ?mycms-preview
async function loadPreviewFrame() {
    const { file, hash } = state.editor;
    const sameFile = pane.frameKey?.startsWith(`${file}\n`);
    pane.frameReady = false;
    pane.frameKey = `${file}\n${hash}`;
    if (!sameFile) pane.frameScroll = 0;
    setPaneInfo(pane.frameInfo = "Chargement…");

    let status = await api("GET", "/api/preview");
    if (!status.running) {
        setPaneInfo("Démarrage du serveur de prévisualisation…");
        status = await api("POST", "/api/preview/start", { port: Number($("preview-port").value) || state.config.default_port });
    }
    showPreview(status);
    pane.frameOrigin = `http://127.0.0.1:${status.port}`;
    const path = file.split("/").map(encodeURIComponent).join("/");
    $("preview-frame").src = `${pane.frameOrigin}/${path}?mycms-preview&mycms-y=${Math.round(pane.frameScroll)}`;
}

export function refreshPane() {
    if (!pane.open) return;
    const { file, hash } = state.editor;
    if (!file) {
        $("code-view").replaceChildren(paneMessage("Sélectionnez un fichier."));
        setPaneInfo("Sélectionnez un fichier");
        return;
    }
    if (pane.mode === "code") {
        refreshSnippet(pane.index);
    } else if (pane.frameKey !== `${file}\n${hash}`) {
        loadPreviewFrame().catch((e) => {
            pane.frameKey = null;
            setPaneInfo(pane.frameInfo = e.message);
            toast(e.message, true);
        });
    } else {
        setPaneInfo(pane.frameInfo);
        postToFrame({ type: "values", values: dirtyValues() });
    }
}

// Pendant la saisie : l'aperçu suit sans recharger la page
export function schedulePaneUpdate() {
    if (!pane.open) return;
    clearTimeout(pane.timer);
    pane.timer = setTimeout(refreshPane, pane.mode === "page" ? 100 : 300);
}

function togglePane(open) {
    pane.open = open;
    $("side-pane").classList.toggle("hidden", !open);
    $("side-pane").classList.toggle("flex", open);
    $("toggle-pane").setAttribute("aria-pressed", String(open));
    try {
        localStorage.setItem("mycms-pane", open ? pane.mode : "");
    } catch {}
    refreshPane();
}

export function setPaneMode(mode) {
    pane.mode = mode;
    document.querySelectorAll("#side-pane [data-pane]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pane === mode)));
    $("preview-frame").classList.toggle("hidden", mode !== "page");
    $("code-view").classList.toggle("hidden", mode !== "code");
    togglePane(true);
}

// Messages du script d'aperçu (preview-helper.js) chargé dans la page
function onFrameMessage(e) {
    if (e.source !== $("preview-frame").contentWindow || !e.data?.mycms) return;
    if (e.data.type === "ready") {
        pane.frameReady = true;
        const count = state.editor.elementCount;
        pane.frameInfo = e.data.count === count
            ? "En direct · modifications non sauvegardées incluses"
            : `Attention : ${e.data.count} éléments éditables dans la page, ${count} dans l'éditeur`;
        if (pane.mode === "page") setPaneInfo(pane.frameInfo);
        postToFrame({ type: "values", values: dirtyValues() });
    } else if (e.data.type === "scroll") {
        pane.frameScroll = e.data.y;
    } else if (e.data.type === "select") {
        // Clic dans la page : ouvrir l'élément dans l'éditeur
        const field = state.editor.fields.get(e.data.index);
        const card = $(`field-${e.data.index}`);
        if (!card) return;
        revealCard(card);
        pane.index = e.data.index; // Pas de défilement en retour dans la page
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        field?.el.focus({ preventScroll: true });
    }
}

export function initPane() {
    $("toggle-pane").addEventListener("click", () => togglePane(!pane.open));
    // La croix ferme l'aperçu et arrête le serveur de prévisualisation ; il redémarre à la prochaine ouverture
    $("pane-close").addEventListener("click", async () => {
        togglePane(false);
        $("preview-frame").removeAttribute("src");
        pane.frameReady = false;
        pane.frameKey = null; // La page sera rechargée à la réouverture
        if (!state.preview.running) return;
        try {
            showPreview(await api("POST", "/api/preview/stop"));
        } catch (e) {
            toast(e.message, true);
        }
    });
    document.querySelectorAll("#side-pane [data-pane]").forEach((b) => b.addEventListener("click", () => setPaneMode(b.dataset.pane)));

    $("editable-list").addEventListener("focusin", (e) => {
        const card = e.target.closest(".field");
        const index = card && Number(card.id.slice("field-".length));
        if (!card || index === pane.index) return;
        pane.index = index;
        if (pane.mode === "page") postToFrame({ type: "focus", index });
        else if (pane.open) refreshSnippet(index);
    });

    $("preview-frame").addEventListener("load", () => {
        // Page chargée sans réponse du script (bloqué par la page, ou erreur 404) : affichage simple
        if (pane.frameKey && !pane.frameReady) setPaneInfo(pane.frameInfo = "Page affichée telle qu'enregistrée : aperçu en direct indisponible");
    });

    window.addEventListener("message", onFrameMessage);
}
