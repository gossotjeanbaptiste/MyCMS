// MyCMS - injecté par le serveur de prévisualisation dans les pages ouvertes avec ?mycms-preview.
// Applique en direct les modifications non sauvegardées de l'éditeur, sans toucher au fichier.
(() => {
    "use strict";
    if (window.parent === window) return;

    const send = (message) => window.parent.postMessage({ mycms: true, ...message }, "*");
    const editables = [...document.querySelectorAll(".editable")];

    // Contenu d'origine au format de l'éditeur : éléments éditables imbriqués remplacés par <mycms-lock>
    const originals = editables.map((el, i) => {
        if (el.tagName === "IFRAME") return el.getAttribute("src") || "";
        const clone = el.cloneNode(true);
        const nested = editables.filter((other, k) => k > i && el.contains(other));
        [...clone.querySelectorAll(".editable")].forEach((node, k) => {
            if (!clone.contains(node) || !nested[k]) return; // Déjà dans un élément remplacé
            const marker = document.createElement("mycms-lock");
            marker.setAttribute("data-index", editables.indexOf(nested[k]));
            node.replaceWith(marker);
        });
        return clone.innerHTML;
    });

    function apply(index, value) {
        const el = editables[index];
        if (el.tagName === "IFRAME") {
            if (el.getAttribute("src") !== value) el.setAttribute("src", value);
            return;
        }
        el.innerHTML = value;
        // Remettre les éléments imbriqués existants (ils ont leurs propres modifications)
        el.querySelectorAll("mycms-lock").forEach((marker) => {
            const nested = editables[Number(marker.getAttribute("data-index"))];
            if (nested) marker.replaceWith(nested);
            else marker.remove();
        });
    }

    let applied = new Set();
    function applyValues(values) {
        const next = new Set(Object.keys(values).map(Number).filter((i) => i >= 0 && i < editables.length));
        // Ordre du document : un parent replacé avant ses éléments imbriqués
        [...new Set([...applied, ...next])].sort((a, b) => a - b).forEach((i) => {
            apply(i, next.has(i) ? values[i] : originals[i]);
        });
        applied = next;
    }

    let flashTimer = null;
    function focusElement(index) {
        const el = editables[index];
        if (!el) return;
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        document.querySelectorAll("[data-mycms-flash]").forEach((node) => node.removeAttribute("data-mycms-flash"));
        el.setAttribute("data-mycms-flash", "");
        clearTimeout(flashTimer);
        flashTimer = setTimeout(() => el.removeAttribute("data-mycms-flash"), 1500);
    }

    window.addEventListener("message", (e) => {
        if (e.source !== window.parent || !e.data?.mycms) return;
        if (e.data.type === "values") applyValues(e.data.values || {});
        else if (e.data.type === "focus") focusElement(e.data.index);
    });

    const style = document.createElement("style");
    style.textContent = `
        .editable { cursor: pointer; }
        .editable:hover { outline: 2px dashed rgba(37, 99, 235, 0.6); outline-offset: 2px; }
        [data-mycms-flash] { outline: 3px solid #2563eb !important; outline-offset: 2px; }
    `;
    document.head.append(style);

    // Clic dans la page : ouvrir l'élément éditable correspondant dans l'éditeur.
    // Les liens ne quittent pas la page prévisualisée (sauf les ancres internes).
    document.addEventListener("click", (e) => {
        const link = e.target.closest("a[href]");
        if (link && !link.getAttribute("href").startsWith("#")) e.preventDefault();
        const el = e.target.closest(".editable");
        if (el) send({ type: "select", index: editables.indexOf(el) });
    }, true);

    // Position de défilement : conservée quand l'éditeur recharge l'aperçu
    const y = Number(new URLSearchParams(location.search).get("mycms-y"));
    if (y) window.addEventListener("load", () => window.scrollTo(0, y), { once: true });
    let scrollTimer = null;
    window.addEventListener("scroll", () => {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(() => send({ type: "scroll", y: window.scrollY }), 150);
    }, { passive: true });

    send({ type: "ready", count: editables.length });
})();
