// MyCMS - contenu de la fenêtre Quitter : ce qui n'est pas encore publié, et les choix proposés

import { $, element, plural } from "../core/dom.js";

const FILE_STATES = { M: "modifié", A: "ajouté", D: "supprimé", R: "renommé", C: "copié", "??": "nouveau" };

const QUIT_BUTTONS = {
    discard: "Annuler les modifications et quitter",
    save: "Sauvegarder et quitter",
    publish: "Publier sur le site et quitter",
    quit: "Quitter",
};

function bulletList(lines, className = "text-muted") {
    const list = element("ul", `flex list-disc flex-col gap-0.5 pl-5 ${className}`);
    lines.forEach((line) => list.append(element("li", "[overflow-wrap:anywhere]", line)));
    return list;
}

// Un choix : toute la carte est cliquable, le bouton radio porte le libellé
function quitChoice({ value, title, description, notes = [], extra, danger = false }, onSelect) {
    const card = element("div", danger ? "quit-choice danger" : "quit-choice");
    const radio = element("input", "mt-1 accent-accent");
    radio.type = "radio";
    radio.name = "quit-choice";
    radio.value = value;
    radio.id = `quit-choice-${value}`;
    const body = element("div", "flex min-w-0 flex-1 flex-col gap-1");
    const label = element("label", "cursor-pointer font-semibold", title);
    label.htmlFor = radio.id;
    body.append(label, element("p", "text-muted", description));
    if (notes.length) body.append(bulletList(notes));
    if (extra) body.append(extra);
    card.append(radio, body);
    card.addEventListener("click", (e) => {
        if (!radio.disabled && !e.target.closest("input:not([type=radio]), label")) radio.checked = true;
        onSelect();
    });
    radio.addEventListener("change", onSelect);
    return card;
}

export function quitSelection() {
    return document.querySelector('#quit-content input[name="quit-choice"]:checked')?.value || "quit";
}

export function updateQuitButton(dirty) {
    const choice = quitSelection();
    const button = $("quit-confirm");
    button.textContent = choice === "save" && !dirty ? "Quitter sans publier" : QUIT_BUTTONS[choice];
    button.classList.toggle("btn-danger", choice === "discard");
    button.classList.toggle("btn-primary", choice !== "discard");
}

// Ce qui n'est pas encore publié
function pendingLines({ dirty, file, files, ahead }) {
    const pending = [];
    if (dirty) pending.push(`${plural(dirty, "élément modifié", "éléments modifiés")} pas encore sauvegardé${dirty > 1 ? "s" : ""} (${file})`);
    files.slice(0, 6).forEach((f) => pending.push(`${f.path} : ${FILE_STATES[f.state] || f.state}, sauvegardé mais pas publié`));
    if (files.length > 6) pending.push(`… et ${plural(files.length - 6, "autre fichier")}`);
    if (ahead) pending.push(`${plural(ahead, "commit")} pas encore envoyé${ahead > 1 ? "s" : ""} sur GitHub`);
    return pending;
}

// 1. Revenir à l'état de base : dernier commit
function discardChoice({ git, untracked, ahead }, onSelect) {
    let extra;
    if (untracked.length) {
        extra = element("div", "flex flex-col gap-1");
        const row = element("div", "flex items-center gap-2");
        const box = element("input", "accent-accent");
        box.type = "checkbox";
        box.id = "quit-clean";
        const boxLabel = element("label", "cursor-pointer", `Supprimer aussi les nouveaux fichiers (${untracked.length})`);
        boxLabel.htmlFor = "quit-clean";
        row.append(box, boxLabel);
        extra.append(row, bulletList(untracked.slice(0, 5).map((f) => f.path).concat(
            untracked.length > 5 ? [`… et ${untracked.length - 5} autre(s)`] : []), "text-xs text-muted"));
    }
    return quitChoice({
        value: "discard",
        title: "Revenir à l'état de base",
        description: git.available
            ? "Annule toutes les modifications depuis le dernier commit, même celles déjà sauvegardées : les fichiers reprennent leur version du dernier commit."
            : "Abandonne les modifications pas encore sauvegardées.",
        notes: ahead ? [`Les ${plural(ahead, "commit")} pas encore envoyé${ahead > 1 ? "s" : ""} sont conservés.`] : [],
        extra,
        danger: true,
    }, onSelect);
}

// 3. Commit et publication sur GitHub
function publishChoice({ dirty, files, ahead }, onSelect) {
    // Message seulement s'il y a un commit à créer (sinon : envoi des commits en attente)
    const toCommit = dirty || files.length;
    let extra;
    if (toCommit) {
        extra = element("div", "mt-1 flex flex-col gap-1.5");
        const label = element("label", "text-xs text-muted", "Message décrivant la modification");
        label.htmlFor = "quit-message";
        const input = element("input", "input");
        input.id = "quit-message";
        input.value = $("commit-message").value.trim() || "Mise à jour du contenu";
        input.addEventListener("focus", () => { $("quit-choice-publish").checked = true; onSelect(); });

        // Mêmes messages préfaits que l'onglet Git : un clic remplit le champ, qui reste modifiable
        const presets = element("div", "flex flex-wrap gap-1.5");
        const markPreset = () => presets.querySelectorAll("button").forEach((b) => {
            b.setAttribute("aria-pressed", String(b.textContent === input.value.trim()));
        });
        document.querySelectorAll("#commit-presets button").forEach((source) => {
            const preset = element("button", "btn px-2.5 py-1 text-xs", source.textContent);
            preset.type = "button";
            preset.addEventListener("click", () => {
                input.value = preset.textContent;
                markPreset();
            });
            presets.append(preset);
        });
        input.addEventListener("input", markPreset);
        markPreset();
        extra.append(label, input, presets);
    }
    return quitChoice({
        value: "publish",
        title: "Publier sur le site et quitter",
        description: !toCommit
            ? `Envoie sur GitHub ${ahead > 1 ? "les commits" : "le commit"} en attente : le site en ligne est mis à jour.`
            : `${dirty ? "Sauvegarde, crée" : "Crée"} un commit et l'envoyer sur GitHub : le site en ligne est mis à jour.`,
        extra,
    }, onSelect);
}

// Contenu de la fenêtre. pending : { dirty, file, git, files, untracked, ahead } ; onSelect : un choix a changé
export function buildQuitItems(check, pending, onSelect) {
    const { dirty, git, files } = pending;
    const items = [];
    const lines = pendingLines(pending);

    if (!lines.length) {
        items.push(element("p", "", git.available
            ? "Tout est sauvegardé et publié : rien ne sera perdu."
            : "Aucune modification non sauvegardée."));
    } else {
        const summary = element("section", "quit-item");
        summary.append(element("h3", "font-semibold", "Pas encore publié sur le site"), bulletList(lines, ""));
        items.push(summary);

        const choices = element("fieldset", "flex flex-col gap-2");
        choices.append(element("legend", "mb-1 font-semibold", "Que faire avant de quitter ?"));
        if (dirty || files.length) choices.append(discardChoice(pending, onSelect));
        // 2. Sauvegarder sans commit : pour reprendre plus tard
        choices.append(quitChoice({
            value: "save",
            title: dirty ? "Sauvegarder et quitter" : "Quitter sans publier",
            description: "Les modifications restent sur cet ordinateur, sans commit : vous pourrez les reprendre plus tard. Le site en ligne ne change pas.",
        }, onSelect));
        if (git.available) choices.append(publishChoice(pending, onSelect));
        else if (git.message) choices.append(element("p", "text-xs text-muted", git.message));
        items.push(choices);
    }

    if (check.preview_running) items.push(element("p", "text-muted", "Le serveur de prévisualisation sera arrêté."));
    return items;
}
