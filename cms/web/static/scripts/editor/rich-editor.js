// MyCMS - éditeur de texte enrichi d'un élément : HTML source -> éditeur -> HTML envoyé au serveur

export const VOID_TAGS = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
const LOCK_ICON = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"></rect><path d="M8 11V7a4 4 0 0 1 8 0v4"></path></svg>';

// Contenu source de l'élément -> éditeur. Les éléments éditables imbriqués deviennent des blocs
// verrouillés, et les attributs on* sont mis de côté pour ne pas s'exécuter dans l'éditeur.
export function buildRichEditor(elem) {
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
export function applySiteBoldRules(selectors) {
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
export function serializeRich(editor) {
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

export function fieldValue(field) {
    return field.kind === "rich" ? serializeRich(field.el) : field.el.value;
}
