// MyCMS - recherche dans les éléments de l'éditeur (sans accents ni majuscules), avec surlignage

import { $ } from "../core/dom.js";
import { state } from "../core/state.js";

// Cartes qui correspondent à la recherche, et celle atteinte avec Entrée
const search = { matches: [], current: -1 };

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
    $("search-count").textContent = !query || !state.editor.file ? ""
        : !search.matches.length ? "Aucun résultat"
        : search.current >= 0 ? `${search.current + 1} / ${search.matches.length}`
        : `${search.matches.length} élément${search.matches.length > 1 ? "s" : ""}`;
}

// refilter = false pendant la saisie dans un éditeur : la carte en cours d'édition ne doit pas disparaître
export function applySearch({ refilter = true } = {}) {
    const query = searchQuery();
    const ranges = [];
    if (refilter) {
        search.matches = [];
        search.current = -1;
        document.querySelectorAll("#editable-list .field").forEach((card) => {
            const index = Number(card.id.slice("field-".length));
            const match = !query || fold(cardText(state.editor.fields.get(index), card)).folded.includes(query);
            card.classList.toggle("hidden", !match);
            card.classList.remove("search-current");
            if (match && query) search.matches.push(card);
        });
        let empty = $("search-empty");
        if (query && !search.matches.length && state.editor.fields.size) {
            if (!empty) {
                empty = document.createElement("p");
                empty.id = "search-empty";
                empty.className = "py-10 text-center text-muted";
                $("editable-list").append(empty);
            }
            empty.textContent = `Aucun élément ne contient « ${$("search").value.trim()} »`;
        } else {
            empty?.remove();
        }
    }
    if (query && window.CSS?.highlights) {
        search.matches.forEach((card) => {
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
    if (!search.matches.length) return;
    search.matches[search.current]?.classList.remove("search-current");
    search.current = (search.current + step + search.matches.length) % search.matches.length;
    const card = search.matches[search.current];
    card.classList.add("search-current");
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    updateSearchCount();
}

// Carte masquée par la recherche (ex. : clic dans l'aperçu) : effacer la recherche pour l'afficher
export function clearSearch() {
    $("search").value = "";
    applySearch();
}

export function initSearch() {
    $("search").addEventListener("input", () => {
        applySearch();
        $("editable-list").scrollTop = 0;
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
}
