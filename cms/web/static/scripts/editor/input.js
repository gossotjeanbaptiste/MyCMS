// MyCMS - saisie dans les cartes de l'éditeur : verrous, retours à la ligne, collage, clics

import { $, toast } from "../core/dom.js";
import { markDirty } from "./editor.js";
import { applySearch } from "./search.js";
import { state } from "../core/state.js";

export function initEditorInput() {
    const editableList = $("editable-list");

    editableList.addEventListener("input", (e) => {
        const card = e.target.closest(".field");
        if (!card) return;
        const index = Number(card.id.slice("field-".length));
        const field = state.editor.fields.get(index);
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
            const field = state.editor.fields.get(Number(lock.dataset.locked));
            field?.card.scrollIntoView({ behavior: "smooth", block: "center" });
            field?.el.focus();
            return;
        }
        // Les liens de l'éditeur ne s'ouvrent pas au clic
        if (e.target.closest(".rich a")) e.preventDefault();
    });
}
