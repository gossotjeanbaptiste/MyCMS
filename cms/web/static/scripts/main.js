// MyCMS - interface web : initialisation des modules, puis démarrage

import { initBrowse } from "./git/browse.js";
import { initCategories } from "./editor/categories.js";
import { toast } from "./core/dom.js";
import { initEditorInput } from "./editor/input.js";
import { initEditor, loadFiles } from "./editor/editor.js";
import { initFormatBar } from "./editor/format-bar.js";
import { initGit, refreshGitStatus } from "./git/git.js";
import { initHeader, openGuide } from "./settings/header.js";
import { initLogs } from "./settings/logs.js";
import { initPane, setPaneMode } from "./preview/pane.js";
import { initPreview, refreshPreview } from "./preview/preview.js";
import { initQuit, openQuitDialog } from "./quit/quit.js";
import { initSearch } from "./editor/search.js";
import { initSettings, loadConfig } from "./settings/settings.js";
import { initStructure } from "./editor/structure.js";
import { initUsers, loadUser } from "./settings/users.js";
import { state } from "./core/state.js";
import { initTabs } from "./core/tabs.js";

function savedPaneMode() {
    try {
        return localStorage.getItem("mycms-pane") || "";
    } catch {
        return "";
    }
}

async function start() {
    await loadUser();
    await loadConfig();
    // Ouvert par « Quitter MyCMS… » de l'icône de notification : fenêtre Quitter plutôt que le guide
    const quitRequested = location.hash === "#quit";
    if (quitRequested) history.replaceState(null, "", "/");
    else if (state.config.show_guide !== false) openGuide();
    await loadFiles();
    await refreshPreview();
    await refreshGitStatus();
    // Aperçu laissé ouvert à la dernière visite
    const pane = savedPaneMode();
    if (pane === "page" || pane === "code") setPaneMode(pane);
    if (quitRequested) await openQuitDialog();
}

[initTabs, initSettings, initUsers, initEditor, initEditorInput, initSearch, initCategories, initStructure, initPane, initFormatBar,
    initGit, initBrowse, initPreview, initLogs, initHeader, initQuit].forEach((init) => init());

start().catch((e) => toast(e.message, true));
