// MyCMS - fenêtre Quitter : vérifier ce qui reste à faire, l'exécuter, puis fermer MyCMS

import { $, api, element, toast } from "../core/dom.js";
import { dirtyCount, saveCurrentFile, warnUnsaved } from "../editor/editor.js";
import { stopLogsPolling } from "../settings/logs.js";
import { stopPreviewPolling } from "../preview/preview.js";
import { buildQuitItems, quitSelection, updateQuitButton } from "./quit-content.js";
import { state } from "../core/state.js";

const quit = {
    running: false, // Une étape est en cours : la fenêtre ne se ferme pas
    pending: null, // Ce qui restait à faire à l'ouverture de la fenêtre
    done: new Set(), // Étapes réussies lors d'un essai précédent : pas refaites
};

const refreshQuitButton = () => updateQuitButton(quit.pending?.dirty);

export async function openQuitDialog() {
    const content = $("quit-content");
    content.replaceChildren(element("p", "text-muted", "Vérification de ce qui reste à faire…"));
    $("quit-error").classList.add("hidden");
    $("quit-progress").textContent = "";
    $("quit-confirm").disabled = true;
    $("quit-confirm").textContent = "Quitter";
    quit.done.clear();
    $("quit-dialog").showModal();

    let check;
    try {
        check = await api("GET", "/api/quit/check");
    } catch (e) {
        check = { git: { available: false, message: `Vérification impossible : ${e.message}` }, preview_running: false };
    }
    const git = check.git;
    const files = git.available ? git.files : [];
    quit.pending = {
        dirty: dirtyCount(),
        file: state.editor.file,
        git,
        files,
        untracked: files.filter((f) => f.state === "??"),
        ahead: git.available ? git.ahead : 0,
    };

    content.replaceChildren(...buildQuitItems(check, quit.pending, refreshQuitButton));
    const defaultChoice = $("quit-choice-save");
    if (defaultChoice) defaultChoice.checked = true;
    $("quit-confirm").disabled = false;
    refreshQuitButton();
    $("quit-confirm").focus();
}

function setQuitBusy(busy, progress = "") {
    quit.running = busy;
    $("quit-confirm").disabled = busy;
    $("quit-cancel").disabled = busy;
    $("quit-content").querySelectorAll("input").forEach((input) => { input.disabled = busy; });
    $("quit-progress").textContent = progress;
}

function showClosedScreen(summary) {
    window.removeEventListener("beforeunload", warnUnsaved);
    stopPreviewPolling();
    stopLogsPolling();
    $("preview-frame").removeAttribute("src");
    $("quit-dialog").close();
    $("closed-summary").textContent = summary;
    $("closed-screen").classList.replace("hidden", "flex");
    window.close(); // Sans effet si l'onglet n'a pas été ouvert par un script
}

// Étapes du choix fait ; retourne le résumé affiché une fois MyCMS fermé
async function runChoice(choice) {
    const { dirty, git, files } = quit.pending;
    let summary = "Rien n'a été perdu.";
    if (choice === "discard") {
        if (git.available && files.length) {
            setQuitBusy(true, "Retour au dernier commit…");
            await api("POST", "/api/git/discard", { remove_untracked: Boolean($("quit-clean")?.checked) });
        }
        // Les modifications de l'éditeur sont abandonnées
        document.querySelectorAll("#editable-list .field.dirty").forEach((f) => f.classList.remove("dirty"));
        summary = git.available ? "Modifications annulées : retour au dernier commit." : "Modifications non sauvegardées abandonnées.";
    }

    if ((choice === "save" || choice === "publish") && dirty && !quit.done.has("save")) {
        setQuitBusy(true, "Sauvegarde…");
        await saveCurrentFile();
        quit.done.add("save");
    }
    if (choice === "save") {
        summary = dirty
            ? "Modifications sauvegardées sur cet ordinateur, pas encore publiées."
            : "Les modifications restent sur cet ordinateur, pas encore publiées.";
    }

    if (choice === "publish") {
        // Sans champ message : rien à commiter, seulement des commits en attente à envoyer
        const message = $("quit-message") ? $("quit-message").value.trim() : "Mise à jour du contenu";
        if (!message) throw new Error("Écrivez un message décrivant la modification (ou choisissez un message préfait), ou choisissez « Sauvegarder et quitter ».");
        setQuitBusy(true, "Commit et publication sur GitHub…");
        try {
            await api("POST", "/api/git/push", { message });
        } catch (e) {
            throw new Error(`La publication a échoué. Vérifiez la connexion Internet puis réessayez, ou choisissez « Sauvegarder et quitter ».\nDétail : ${e.message}`);
        }
        summary = "Modifications publiées sur GitHub : le site en ligne sera mis à jour dans quelques minutes.";
    }
    return summary;
}

async function runQuit() {
    const choice = quitSelection();
    if (choice === "discard" && !confirm("Toutes les modifications depuis le dernier commit seront définitivement perdues, même celles déjà sauvegardées. Continuer ?")) return;

    $("quit-error").classList.add("hidden");
    let summary;
    try {
        summary = await runChoice(choice);
        setQuitBusy(true, "Fermeture…");
        await api("POST", "/api/quit");
    } catch (e) {
        // Rien n'est fermé : l'utilisateur peut réessayer ou faire un autre choix
        setQuitBusy(false);
        $("quit-error").textContent = e.message;
        $("quit-error").classList.remove("hidden");
        return;
    }
    showClosedScreen(summary);
}

export function initQuit() {
    $("quit").addEventListener("click", () => openQuitDialog().catch((e) => toast(e.message, true)));
    $("quit-cancel").addEventListener("click", () => $("quit-dialog").close());
    $("quit-confirm").addEventListener("click", runQuit);
    // Échap pendant une étape en cours : la fenêtre reste ouverte
    $("quit-dialog").addEventListener("cancel", (e) => { if (quit.running) e.preventDefault(); });
}
