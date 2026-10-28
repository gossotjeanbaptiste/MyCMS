// MyCMS - onglets : chaque onglet peut charger son contenu à l'ouverture

const loaders = {};

// Fonction appelée à chaque ouverture de l'onglet
export function onTabOpen(name, loader) {
    loaders[name] = loader;
}

export function initTabs() {
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
            document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tab.dataset.tab}`));
            loaders[tab.dataset.tab]?.();
        });
    });
}
