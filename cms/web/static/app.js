// MyCMS - interface web
"use strict";

const $ = (id) => document.getElementById(id);

// ======= Utilitaires =======

async function api(method, url, body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if (response.status === 401) {
        // Session expirée ou fermée : retour à la page de connexion
        location.replace("/login");
        throw new Error("Session expirée : reconnectez-vous");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) {
        const error = new Error(data.error || data.message || data.output || `Erreur HTTP ${response.status}`);
        error.data = data;
        throw error;
    }
    return data;
}

function toast(message, isError = false) {
    const el = document.createElement("div");
    el.className = isError ? "toast error" : "toast";
    el.textContent = message;
    $("toasts").appendChild(el);
    setTimeout(() => el.remove(), isError ? 8000 : 4000);
}

// Désactive le bouton pendant l'action et affiche le résultat ou l'erreur
async function withButton(button, action) {
    button.disabled = true;
    button.classList.add("busy");
    try {
        await action();
    } catch (e) {
        toast(e.message, true);
    } finally {
        button.disabled = false;
        button.classList.remove("busy");
    }
}

// ======= Onglets =======

const tabLoaders = {};

document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
        document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tab.dataset.tab}`));
        tabLoaders[tab.dataset.tab]?.();
    });
});

// ======= Configuration =======

let config = {};

async function loadConfig() {
    config = await api("GET", "/api/config");
    $("git-repo").value = config.repo_path;
    $("set-repo").value = config.repo_path;
    $("set-port").value = config.default_port;
    $("set-site-url").value = config.site_url || "";
    $("set-auto-pull").checked = config.auto_pull;
    $("set-auto-refresh").checked = config.auto_refresh;
    if (!previewRunning) $("preview-port").value = config.default_port;
}

$("settings-save").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    await api("POST", "/api/config", {
        repo_path: $("set-repo").value.trim(),
        site_url: $("set-site-url").value.trim(),
        default_port: Number($("set-port").value),
        auto_pull: $("set-auto-pull").checked,
        auto_refresh: $("set-auto-refresh").checked,
    });
    await loadConfig();
    await loadFiles();
    await refreshSitemapInfo();
    toast("Paramètres sauvegardés");
}));

async function refreshSitemapInfo() {
    const info = await api("GET", "/api/sitemap");
    const location = info.location ? `Emplacement : ${info.location}` : "Aucun sitemap : il sera créé à la racine";
    const url = info.base_url ? `URL du site : ${info.base_url}` : "URL du site introuvable : renseignez-la ci-dessus";
    $("sitemap-info").textContent = `${location} · ${url}`;
}

tabLoaders.settings = () => refreshSitemapInfo().catch((e) => toast(e.message, true));

$("sitemap-generate").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    toast((await api("POST", "/api/sitemap")).message);
    await refreshSitemapInfo();
}));

$("pw-save").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    const result = await api("POST", "/api/auth/password", {
        current: $("pw-current").value,
        new: $("pw-new").value,
        confirm: $("pw-confirm").value,
    });
    ["pw-current", "pw-new", "pw-confirm"].forEach((id) => { $(id).value = ""; });
    toast(result.message);
}));

$("settings-reset").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    if (!confirm("Réinitialiser tous les paramètres ?")) return;
    await api("POST", "/api/config/reset");
    await loadConfig();
    await loadFiles();
    toast("Paramètres réinitialisés");
}));

// ======= Éditeur =======

let currentFile = null;
let currentHash = null;
// index -> { el, kind: "rich" | "src", card, initial, locks }
let fields = new Map();

const VOID_TAGS = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
const LOCK_ICON = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"></rect><path d="M8 11V7a4 4 0 0 1 8 0v4"></path></svg>';

async function loadFiles() {
    const { files } = await api("GET", "/api/files");
    const select = $("file-select");
    select.replaceChildren(new Option("Choisir un fichier…", ""));
    files.forEach((f) => select.add(new Option(f, f)));
    if (files.includes(currentFile)) select.value = currentFile;
    return files;
}

// Les pages peuvent être dans des sous-dossiers : encoder chaque segment, garder les "/"
function fileUrl(name, prefix = "/api/files/") {
    return prefix + name.split("/").map(encodeURIComponent).join("/");
}

function dirtyCount() {
    return document.querySelectorAll("#editable-list .field.dirty").length;
}

function updateEditorState() {
    const dirty = dirtyCount();
    $("save-file").disabled = !currentFile || dirty === 0;
    $("save-file").textContent = dirty ? `Sauvegarder (${dirty})` : "Sauvegarder";
    $("reload-file").disabled = !currentFile;
}

// Contenu source de l'élément -> éditeur. Les éléments éditables imbriqués deviennent des blocs
// verrouillés, et les attributs on* sont mis de côté pour ne pas s'exécuter dans l'éditeur.
function buildRichEditor(elem) {
    const template = document.createElement("template");
    template.innerHTML = elem.html;
    template.content.querySelectorAll("*").forEach((node) => {
        for (const attr of [...node.attributes]) {
            if (attr.name.startsWith("on")) {
                node.setAttribute(`data-mycms-${attr.name}`, attr.value);
                node.removeAttribute(attr.name);
            }
        }
    });

    const nestedNodes = [...template.content.querySelectorAll(".editable")];
    if (nestedNodes.length !== elem.nested.length) return null;
    let locks = 0;
    nestedNodes.forEach((node, k) => {
        if (!template.content.contains(node)) return; // Déjà dans un bloc verrouillé
        const lock = document.createElement("span");
        lock.className = "lock";
        lock.contentEditable = "false";
        lock.dataset.locked = elem.nested[k];
        lock.title = `Élément éditable imbriqué : modifiez-le dans la carte [${elem.nested[k]}]`;
        const label = node.textContent.trim().replace(/\s+/g, " ");
        lock.innerHTML = LOCK_ICON;
        lock.append(label.length > 40 ? label.slice(0, 40) + "…" : label || `[${elem.nested[k]}]`);
        node.replaceWith(lock);
        locks++;
    });

    const editor = document.createElement("div");
    editor.className = "rich";
    editor.contentEditable = "true";
    editor.dataset.index = elem.index;
    editor.dataset.tag = elem.tag;
    // Gras seulement si le CSS du site le dit ou si l'élément est un <strong>/<b> (calculé par le serveur)
    editor.style.fontWeight = elem.bold ? "700" : "400";
    editor.append(template.content);
    return { editor, locks };
}

// Sélecteurs simples (balise, .classe) que le CSS du site met en gras, appliqués au contenu des éditeurs
function applySiteBoldRules(selectors) {
    let style = document.getElementById("site-bold-rules");
    if (!style) {
        style = document.createElement("style");
        style.id = "site-bold-rules";
        document.head.append(style);
    }
    const safe = selectors.filter((s) => /^[A-Za-z0-9_.-]+$/.test(s));
    style.textContent = safe.length ? `.rich :is(${safe.join(", ")}) { font-weight: 700; }` : "";
}

// Éditeur -> HTML envoyé au serveur : blocs verrouillés remplacés par un marqueur, attributs on* restaurés
function serializeRich(editor) {
    const clone = editor.cloneNode(true);
    clone.querySelectorAll("[data-locked]").forEach((lock) => {
        const marker = document.createElement("mycms-lock");
        marker.setAttribute("data-index", lock.dataset.locked);
        lock.replaceWith(marker);
    });
    clone.querySelectorAll("*").forEach((node) => {
        for (const attr of [...node.attributes]) {
            if (attr.name.startsWith("data-mycms-on")) {
                node.setAttribute(attr.name.slice("data-mycms-".length), attr.value);
                node.removeAttribute(attr.name);
            }
        }
    });
    return clone.innerHTML;
}

function fieldValue(field) {
    return field.kind === "rich" ? serializeRich(field.el) : field.el.value;
}

function renderElements(elements) {
    // Élément éditable le plus proche qui contient chaque élément imbriqué
    const parentOf = {};
    elements.forEach((elem) => elem.nested.forEach((n) => { parentOf[n] = elem.index; }));

    fields = new Map();
    const fragment = document.createDocumentFragment();
    for (const elem of elements) {
        const card = document.createElement("div");
        card.className = "field";
        card.id = `field-${elem.index}`;

        const meta = document.createElement("div");
        meta.className = "font-mono text-xs [overflow-wrap:anywhere]";
        const tag = document.createElement("div");
        tag.className = "font-bold text-tag";
        tag.textContent = `<${elem.tag.toUpperCase()}>${elem.is_iframe ? " [SRC]" : ""}`;
        const id = document.createElement("div");
        id.className = "text-muted";
        id.textContent = elem.id ? `#${elem.id} [${elem.index}]` : `[${elem.index}]`;
        meta.append(tag, id);
        if (elem.index in parentOf) {
            const inside = document.createElement("div");
            inside.className = "mt-1.5 text-muted";
            inside.textContent = `dans [${parentOf[elem.index]}]`;
            meta.append(inside);
        }

        let control;
        if (elem.is_iframe) {
            control = document.createElement("textarea");
            control.className = "input min-h-10 w-full resize-y";
            control.value = elem.value;
            control.rows = 1;
            fields.set(elem.index, { el: control, kind: "src", card });
        } else {
            const built = VOID_TAGS.has(elem.tag) ? null : buildRichEditor(elem);
            if (built) {
                control = built.editor;
                fields.set(elem.index, { el: control, kind: "rich", card, locks: built.locks });
            } else {
                control = document.createElement("p");
                control.className = "py-2 text-muted";
                control.textContent = VOID_TAGS.has(elem.tag)
                    ? "Élément sans contenu texte : non modifiable ici."
                    : "Structure HTML non reconnue : élément non modifiable ici.";
            }
        }

        card.append(meta, control);
        fragment.appendChild(card);
    }
    $("editable-list").replaceChildren(fragment);
    fields.forEach((field) => { field.initial = fieldValue(field); });
}

async function openFile(name, { keepScroll = false } = {}) {
    if (!name) return;
    if (dirtyCount() && !confirm("Des modifications non sauvegardées seront perdues. Continuer ?")) {
        $("file-select").value = currentFile || "";
        return;
    }
    const scroll = keepScroll ? $("editable-list").scrollTop : 0;
    const start = performance.now();
    const data = await api("GET", fileUrl(name));
    // Page mise à jour mais serveur Python lancé avant : il ne renvoie pas encore ces champs
    if (data.elements.some((e) => !("html" in e) || !Array.isArray(e.nested))) {
        throw new Error("Le serveur MyCMS tourne sur une ancienne version : fermez la fenêtre de run.bat et relancez-le.");
    }

    if (name !== currentFile) paneIndex = null;
    currentFile = name;
    currentHash = data.hash;
    elementCount = data.elements.length;
    applySiteBoldRules(data.bold_selectors || []);

    if (data.elements.length) {
        renderElements(data.elements);
    } else {
        fields = new Map();
        const p = document.createElement("p");
        p.className = "py-10 text-center text-muted";
        p.textContent = data.notice || "Aucun élément éditable trouvé";
        $("editable-list").replaceChildren(p);
    }
    applySearch();
    $("editable-list").scrollTop = scroll;

    const total = Math.round(performance.now() - start);
    $("editor-info").textContent = `${data.elements.length} éléments · ${total} ms`;
    updateEditorState();
    refreshPane();
}

function markDirty(index) {
    const field = fields.get(index);
    if (field) field.card.classList.toggle("dirty", fieldValue(field) !== field.initial);
    updateEditorState();
    schedulePaneUpdate();
}

// Valeurs des éléments modifiés, par index
function dirtyValues() {
    const values = {};
    fields.forEach((field, index) => {
        if (field.card.classList.contains("dirty")) values[index] = fieldValue(field);
    });
    return values;
}

const editableList = $("editable-list");

editableList.addEventListener("input", (e) => {
    const card = e.target.closest(".field");
    if (!card) return;
    const index = Number(card.id.slice("field-".length));
    const field = fields.get(index);
    if (!field) return;
    // Un élément imbriqué ne doit pas disparaître de son parent (il a sa propre carte)
    if (field.kind === "rich" && field.el.querySelectorAll("[data-locked]").length < field.locks) {
        document.execCommand("undo");
        toast("Un élément éditable imbriqué ne peut pas être supprimé ici : modifiez-le dans sa propre carte.", true);
    }
    markDirty(index);
    applySearch({ refilter: false });
});

editableList.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || !e.target.closest(".rich")) return;
    // Retour à la ligne = <br>, pas un nouveau <div>
    e.preventDefault();
    if (!document.execCommand("insertLineBreak")) document.execCommand("insertHTML", false, "<br>");
});

// Coller en texte brut : pas de mise en forme venue de Word ou d'une page web
editableList.addEventListener("paste", (e) => {
    if (!e.target.closest(".rich")) return;
    const text = e.clipboardData?.getData("text/plain");
    if (text == null) return;
    e.preventDefault();
    document.execCommand("insertText", false, text);
});

editableList.addEventListener("click", (e) => {
    // Clic sur un bloc verrouillé : aller à la carte de l'élément imbriqué
    const lock = e.target.closest("[data-locked]");
    if (lock) {
        e.preventDefault();
        const field = fields.get(Number(lock.dataset.locked));
        field?.card.scrollIntoView({ behavior: "smooth", block: "center" });
        field?.el.focus();
        return;
    }
    // Les liens de l'éditeur ne s'ouvrent pas au clic
    if (e.target.closest(".rich a")) e.preventDefault();
});

// ======= Recherche =======

// Cartes qui correspondent à la recherche, et celle atteinte avec Entrée
let searchMatches = [];
let searchCurrent = -1;

// Minuscules sans accents ("Équipe" trouve "equipe"), avec la position d'origine de chaque caractère
function fold(text) {
    let folded = "";
    const offsets = [];
    let i = 0;
    for (const char of text) {
        const f = char.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
        for (let k = 0; k < f.length; k++) offsets.push(i);
        folded += f;
        i += char.length;
    }
    offsets.push(i);
    return { folded, offsets };
}

function searchQuery() {
    return fold($("search").value.trim()).folded;
}

// Texte d'une carte : balise, id, index et contenu
function cardText(field, card) {
    return card.textContent + (field?.kind === "src" ? " " + field.el.value : "");
}

// Occurrences dans les nœuds texte d'un éditeur, même à cheval sur plusieurs balises (<b>, <a>…)
function searchRanges(root, query) {
    const pieces = [];
    let folded = "";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let node; (node = walker.nextNode());) {
        const f = fold(node.data);
        pieces.push({ node, start: folded.length, offsets: f.offsets });
        folded += f.folded;
    }
    const locate = (pos, isEnd) => {
        const piece = pieces.findLast((p) => (isEnd ? p.start < pos : p.start <= pos));
        return [piece.node, piece.offsets[pos - piece.start]];
    };
    const ranges = [];
    for (let pos = folded.indexOf(query); pos !== -1; pos = folded.indexOf(query, pos + query.length)) {
        const range = new Range();
        range.setStart(...locate(pos, false));
        range.setEnd(...locate(pos + query.length, true));
        ranges.push(range);
    }
    return ranges;
}

function updateSearchCount() {
    const query = searchQuery();
    $("search-count").textContent = !query || !currentFile ? ""
        : !searchMatches.length ? "Aucun résultat"
        : searchCurrent >= 0 ? `${searchCurrent + 1} / ${searchMatches.length}`
        : `${searchMatches.length} élément${searchMatches.length > 1 ? "s" : ""}`;
}

// refilter = false pendant la saisie dans un éditeur : la carte en cours d'édition ne doit pas disparaître
function applySearch({ refilter = true } = {}) {
    const query = searchQuery();
    const ranges = [];
    if (refilter) {
        searchMatches = [];
        searchCurrent = -1;
        document.querySelectorAll("#editable-list .field").forEach((card) => {
            const index = Number(card.id.slice("field-".length));
            const match = !query || fold(cardText(fields.get(index), card)).folded.includes(query);
            card.classList.toggle("hidden", !match);
            card.classList.remove("search-current");
            if (match && query) searchMatches.push(card);
        });
        let empty = $("search-empty");
        if (query && !searchMatches.length && fields.size) {
            if (!empty) {
                empty = document.createElement("p");
                empty.id = "search-empty";
                empty.className = "py-10 text-center text-muted";
                editableList.append(empty);
            }
            empty.textContent = `Aucun élément ne contient « ${$("search").value.trim()} »`;
        } else {
            empty?.remove();
        }
    }
    if (query && window.CSS?.highlights) {
        searchMatches.forEach((card) => {
            const editor = card.querySelector(".rich");
            if (editor) ranges.push(...searchRanges(editor, query));
        });
    }
    if (window.CSS?.highlights) {
        if (ranges.length) CSS.highlights.set("mycms-search", new Highlight(...ranges));
        else CSS.highlights.delete("mycms-search");
    }
    updateSearchCount();
}

// Entrée : résultat suivant, Maj+Entrée : précédent
function goToMatch(step) {
    if (!searchMatches.length) return;
    searchMatches[searchCurrent]?.classList.remove("search-current");
    searchCurrent = (searchCurrent + step + searchMatches.length) % searchMatches.length;
    const card = searchMatches[searchCurrent];
    card.classList.add("search-current");
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    updateSearchCount();
}

$("search").addEventListener("input", () => {
    applySearch();
    editableList.scrollTop = 0;
});

$("search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        goToMatch(e.shiftKey ? -1 : 1);
    } else if (e.key === "Escape" && e.currentTarget.value) {
        e.preventDefault();
        e.currentTarget.value = "";
        applySearch();
    }
});

// Ctrl+F dans l'onglet Éditeur : rechercher dans les éléments plutôt que dans la page
document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f" && $("tab-editor").classList.contains("active")) {
        e.preventDefault();
        $("search").focus();
        $("search").select();
    }
});

// ======= Aperçu en direct =======

let elementCount = 0;
let paneOpen = false;
let paneMode = "page"; // "page" : page du site, "code" : code source de l'élément
let paneIndex = null; // Dernier élément cliqué dans l'éditeur ou dans la page
let paneTimer = null;
let frameReady = false; // Le script d'aperçu de la page a répondu
let frameOrigin = "";
let frameKey = null; // Fichier et version chargés dans l'aperçu
let frameScroll = 0;
let frameInfo = "";
let snippetRequest = 0;
let snippetShown = null;

function setPaneInfo(text) {
    $("pane-info").textContent = text;
    $("pane-info").title = text;
}

function paneMessage(text) {
    const p = document.createElement("p");
    p.className = "px-3 py-10 text-center font-sans text-sm text-muted";
    p.textContent = text;
    return p;
}

function postToFrame(message) {
    if (frameReady) $("preview-frame").contentWindow.postMessage({ mycms: true, ...message }, frameOrigin);
}

// La page est servie par le serveur de prévisualisation (démarré si besoin), avec ?mycms-preview
async function loadPreviewFrame() {
    const sameFile = frameKey?.startsWith(`${currentFile}\n`);
    frameReady = false;
    frameKey = `${currentFile}\n${currentHash}`;
    if (!sameFile) frameScroll = 0;
    setPaneInfo(frameInfo = "Chargement…");

    let status = await api("GET", "/api/preview");
    if (!status.running) {
        setPaneInfo("Démarrage du serveur de prévisualisation…");
        status = await api("POST", "/api/preview/start", { port: Number($("preview-port").value) || config.default_port });
    }
    showPreview(status);
    frameOrigin = `http://127.0.0.1:${status.port}`;
    const path = currentFile.split("/").map(encodeURIComponent).join("/");
    $("preview-frame").src = `${frameOrigin}/${path}?mycms-preview&mycms-y=${Math.round(frameScroll)}`;
}

async function refreshSnippet() {
    const view = $("code-view");
    if (paneIndex === null) {
        snippetShown = null;
        view.replaceChildren(paneMessage("Cliquez dans un élément pour afficher son code source."));
        setPaneInfo("");
        return;
    }
    const request = ++snippetRequest;
    const index = paneIndex;
    let data;
    try {
        data = await api("POST", fileUrl(currentFile, "/api/snippet/"), { hash: currentHash, values: dirtyValues(), index });
    } catch (e) {
        if (request === snippetRequest) view.replaceChildren(paneMessage(e.message));
        return;
    }
    if (request !== snippetRequest) return; // Une réponse plus récente arrive

    const fragment = document.createDocumentFragment();
    data.lines.forEach((text, k) => {
        const number = data.first_line + k;
        const line = document.createElement("div");
        line.className = number >= data.start_line && number <= data.end_line ? "code-line hl" : "code-line";
        const ln = document.createElement("span");
        ln.className = "ln";
        ln.textContent = number;
        const code = document.createElement("span");
        code.className = "pr-3";
        code.textContent = text || " ";
        line.append(ln, code);
        fragment.append(line);
    });
    view.replaceChildren(fragment);
    if (snippetShown !== index) view.scrollTop = 0;
    snippetShown = index;

    const dirty = $(`field-${index}`)?.classList.contains("dirty");
    const lines = data.start_line === data.end_line ? `ligne ${data.start_line}` : `lignes ${data.start_line} à ${data.end_line}`;
    setPaneInfo(`[${index}] · ${lines}${dirty ? " · non sauvegardé" : ""}`);
}

function refreshPane() {
    if (!paneOpen) return;
    if (!currentFile) {
        $("code-view").replaceChildren(paneMessage("Sélectionnez un fichier."));
        setPaneInfo("Sélectionnez un fichier");
        return;
    }
    if (paneMode === "code") {
        refreshSnippet();
    } else if (frameKey !== `${currentFile}\n${currentHash}`) {
        loadPreviewFrame().catch((e) => {
            frameKey = null;
            setPaneInfo(frameInfo = e.message);
            toast(e.message, true);
        });
    } else {
        setPaneInfo(frameInfo);
        postToFrame({ type: "values", values: dirtyValues() });
    }
}

// Pendant la saisie : l'aperçu suit sans recharger la page
function schedulePaneUpdate() {
    if (!paneOpen) return;
    clearTimeout(paneTimer);
    paneTimer = setTimeout(refreshPane, paneMode === "page" ? 100 : 300);
}

function togglePane(open) {
    paneOpen = open;
    $("side-pane").classList.toggle("hidden", !open);
    $("side-pane").classList.toggle("flex", open);
    $("toggle-pane").setAttribute("aria-pressed", String(open));
    try {
        localStorage.setItem("mycms-pane", open ? paneMode : "");
    } catch {}
    refreshPane();
}

function setPaneMode(mode) {
    paneMode = mode;
    document.querySelectorAll("#side-pane [data-pane]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pane === mode)));
    $("preview-frame").classList.toggle("hidden", mode !== "page");
    $("code-view").classList.toggle("hidden", mode !== "code");
    togglePane(true);
}

$("toggle-pane").addEventListener("click", () => togglePane(!paneOpen));
$("pane-close").addEventListener("click", () => togglePane(false));
document.querySelectorAll("#side-pane [data-pane]").forEach((b) => b.addEventListener("click", () => setPaneMode(b.dataset.pane)));

editableList.addEventListener("focusin", (e) => {
    const card = e.target.closest(".field");
    const index = card && Number(card.id.slice("field-".length));
    if (!card || index === paneIndex) return;
    paneIndex = index;
    if (paneMode === "page") postToFrame({ type: "focus", index });
    else if (paneOpen) refreshSnippet();
});

$("preview-frame").addEventListener("load", () => {
    // Page chargée sans réponse du script (bloqué par la page, ou erreur 404) : affichage simple
    if (frameKey && !frameReady) setPaneInfo(frameInfo = "Page affichée telle qu'enregistrée : aperçu en direct indisponible");
});

window.addEventListener("message", (e) => {
    if (e.source !== $("preview-frame").contentWindow || !e.data?.mycms) return;
    if (e.data.type === "ready") {
        frameReady = true;
        frameInfo = e.data.count === elementCount
            ? "En direct · modifications non sauvegardées incluses"
            : `Attention : ${e.data.count} éléments éditables dans la page, ${elementCount} dans l'éditeur`;
        if (paneMode === "page") setPaneInfo(frameInfo);
        postToFrame({ type: "values", values: dirtyValues() });
    } else if (e.data.type === "scroll") {
        frameScroll = e.data.y;
    } else if (e.data.type === "select") {
        // Clic dans la page : ouvrir l'élément dans l'éditeur
        const field = fields.get(e.data.index);
        const card = $(`field-${e.data.index}`);
        if (!card) return;
        if (card.classList.contains("hidden")) {
            $("search").value = "";
            applySearch();
        }
        paneIndex = e.data.index; // Pas de défilement en retour dans la page
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        field?.el.focus({ preventScroll: true });
    }
});

// ======= Barre de mise en forme =======

function selectionElement() {
    const node = document.getSelection()?.anchorNode;
    return node && (node.nodeType === 1 ? node : node.parentElement);
}

function activeEditor() {
    return selectionElement()?.closest("#editable-list .rich") || null;
}

function updateFormatBar() {
    const editor = activeEditor();
    document.querySelectorAll("#format-bar .fmt").forEach((button) => {
        button.disabled = !editor;
        const cmd = button.dataset.cmd;
        if (cmd === "bold" || cmd === "italic") {
            button.setAttribute("aria-pressed", editor && document.queryCommandState(cmd) ? "true" : "false");
        }
    });
    $("format-hint").textContent = editor
        ? `Élément [${editor.dataset.index}] : sélectionnez du texte puis appliquez une mise en forme`
        : "Cliquez dans un élément pour le modifier.";
}

document.addEventListener("selectionchange", updateFormatBar);

document.querySelectorAll("#format-bar .fmt").forEach((button) => {
    // mousedown : garder la sélection dans l'éditeur
    button.addEventListener("mousedown", (e) => e.preventDefault());
    button.addEventListener("click", () => {
        const editor = activeEditor();
        if (!editor) return;
        const cmd = button.dataset.cmd;
        if (cmd === "bold" && document.queryCommandState("bold") && !selectionElement()?.closest(".rich strong, .rich b")) {
            // Le navigateur ajouterait un <span style="font-weight: normal">, retiré à la sauvegarde
            const reason = ["strong", "b"].includes(editor.dataset.tag)
                ? `cet élément est déjà lui-même une balise <${editor.dataset.tag}>`
                : "le CSS du site met déjà ce texte en gras";
            toast(`Le CMS n'autorise pas à retirer le gras ici : ${reason}.`, true);
            return;
        }
        if (cmd === "link") {
            const current = selectionElement()?.closest("a");
            const url = prompt("Adresse du lien (https://…, page.html, mailto:…)", current?.getAttribute("href") || "https://");
            if (url && url.trim() && url.trim() !== "https://") document.execCommand("createLink", false, url.trim());
        } else if (cmd === "removeFormat") {
            document.execCommand("removeFormat");
            document.execCommand("unlink");
        } else {
            document.execCommand(cmd);
        }
        markDirty(Number(editor.dataset.index));
        updateFormatBar();
    });
});

updateFormatBar();

$("file-select").addEventListener("change", (e) => {
    openFile(e.target.value).catch((err) => toast(err.message, true));
});

$("refresh-files").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    const files = await loadFiles();
    toast(`${files.length} fichiers trouvés`);
}));

$("reload-file").addEventListener("click", (e) => withButton(e.currentTarget, () => openFile(currentFile, { keepScroll: true })));

$("save-file").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    // Seuls les éléments modifiés sont envoyés
    const result = await api("POST", fileUrl(currentFile), { hash: currentHash, values: dirtyValues() });
    document.querySelectorAll("#editable-list .field.dirty").forEach((f) => f.classList.remove("dirty"));
    toast(`${result.message}\n${result.sitemap}`);
    // Recharger depuis le fichier : l'éditeur affiche exactement ce qui a été écrit
    await openFile(currentFile, { keepScroll: true });
}).then(updateEditorState));

function warnUnsaved(e) {
    if (dirtyCount()) e.preventDefault();
}

window.addEventListener("beforeunload", warnUnsaved);

// ======= Git =======

function showGitOutput(text) {
    $("git-output").textContent = text;
}

// Dossier choisi sans .git : proposer de récupérer le site, dans ce dossier par défaut
let clonePathPrefill = "";

function showCloneCard(hasGit) {
    $("clone-card").classList.toggle("hidden", hasGit);
    const input = $("clone-path");
    if (!hasGit && (!input.value || input.value === clonePathPrefill)) {
        input.value = clonePathPrefill = config.repo_path || "";
    }
}

async function refreshGitStatus() {
    let status;
    try {
        status = await api("GET", "/api/git/status");
    } catch (e) {
        status = { ...e.data, output: e.message };
    }
    showGitOutput(status.output);
    showCloneCard(status.has_git !== false);
}

tabLoaders.git = refreshGitStatus;

$("git-verify").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    // Le chemin saisi devient le repository courant
    await api("POST", "/api/config", { repo_path: $("git-repo").value.trim() });
    await loadConfig();
    const result = await api("POST", "/api/git/verify");
    toast(result.message);
    await loadFiles();
    await refreshGitStatus();
}));

$("git-clone").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    const url = $("clone-url").value.trim();
    if (!url) throw new Error("Veuillez entrer l'adresse du repository");
    showGitOutput("Récupération du site en cours…");
    try {
        const result = await api("POST", "/api/git/clone", { url, path: $("clone-path").value.trim() });
        toast(result.message);
        $("clone-url").value = "";
        $("clone-path").value = "";
        await loadConfig();
        await loadFiles();
    } finally {
        await refreshGitStatus();
    }
}));

// Messages de commit préfaits : remplissent le champ, le message reste modifiable
function updateCommitPresets() {
    const message = $("commit-message").value.trim();
    document.querySelectorAll("#commit-presets button").forEach((b) => {
        b.setAttribute("aria-pressed", String(b.textContent === message));
    });
}

document.querySelectorAll("#commit-presets button").forEach((button) => {
    button.addEventListener("click", () => {
        const input = $("commit-message");
        input.value = button.textContent;
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
        updateCommitPresets();
    });
});

$("commit-message").addEventListener("input", updateCommitPresets);
updateCommitPresets();

$("git-pull").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    try {
        toast((await api("POST", "/api/git/pull")).message);
    } finally {
        await refreshGitStatus();
    }
}));

$("git-push").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    try {
        toast((await api("POST", "/api/git/push", { message: $("commit-message").value })).message);
    } finally {
        await refreshGitStatus();
    }
}));

$("git-status").addEventListener("click", (e) => withButton(e.currentTarget, refreshGitStatus));

$("git-add").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    try {
        toast((await api("POST", "/api/git/add")).message);
    } finally {
        await refreshGitStatus();
    }
}));

// ======= Prévisualisation =======

let previewRunning = false;
let previewTimer = null;

function showPreview(status) {
    previewRunning = status.running;
    $("preview-state").className = status.running ? "badge-on" : "badge-off";
    $("preview-state").textContent = status.running ? `Actif (port ${status.port})` : "Arrêté";
    $("preview-toggle").textContent = status.running ? "Arrêter" : "Démarrer";
    $("preview-port").disabled = status.running;
    const url = status.running ? `http://127.0.0.1:${status.port}` : "";
    $("preview-url").href = url || "#";
    $("preview-url").textContent = url;
    $("preview-logs").textContent = status.logs.join("\n");
}

async function refreshPreview() {
    showPreview(await api("GET", "/api/preview"));
}

tabLoaders.preview = () => {
    refreshPreview();
    clearInterval(previewTimer);
    previewTimer = setInterval(() => {
        if ($("tab-preview").classList.contains("active")) refreshPreview();
        else clearInterval(previewTimer);
    }, 2000);
};

$("preview-toggle").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    if (previewRunning) {
        showPreview(await api("POST", "/api/preview/stop"));
        toast("Serveur arrêté");
    } else {
        const status = await api("POST", "/api/preview/start", { port: Number($("preview-port").value) });
        showPreview(status);
        toast(`Serveur local démarré sur http://127.0.0.1:${status.port}`);
    }
}));

// ======= Logs =======

async function refreshLogs() {
    const output = $("logs-output");
    const wasAtBottom = output.scrollTop + output.clientHeight >= output.scrollHeight - 20;
    output.textContent = (await api("GET", "/api/logs")).logs.join("\n");
    if (wasAtBottom) output.scrollTop = output.scrollHeight;
}

let logsTimer = null;
tabLoaders.logs = () => {
    refreshLogs();
    clearInterval(logsTimer);
    logsTimer = setInterval(() => {
        if ($("tab-logs").classList.contains("active")) refreshLogs();
        else clearInterval(logsTimer);
    }, 1000);
};

$("logs-clear").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
    await api("DELETE", "/api/logs");
    await refreshLogs();
    toast("Logs effacés");
}));

$("logs-export").addEventListener("click", () => {
    const blob = new Blob([$("logs-output").textContent], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `mycms-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    link.click();
    URL.revokeObjectURL(link.href);
});

// ======= Session =======

$("logout").addEventListener("click", async () => {
    if (dirtyCount() && !confirm("Des modifications non sauvegardées seront perdues. Se déconnecter ?")) return;
    await api("POST", "/api/auth/logout").catch(() => {});
    window.removeEventListener("beforeunload", warnUnsaved);
    location.replace("/login");
});

// ======= Démarrage =======

(async () => {
    try {
        $("user-name").textContent = (await api("GET", "/api/auth/state")).username || "";
        await loadConfig();
        await loadFiles();
        await refreshPreview();
        await refreshGitStatus();
        // Aperçu laissé ouvert à la dernière visite
        let pane = "";
        try {
            pane = localStorage.getItem("mycms-pane") || "";
        } catch {}
        if (pane === "page" || pane === "code") setPaneMode(pane);
    } catch (e) {
        toast(e.message, true);
    }
})();
