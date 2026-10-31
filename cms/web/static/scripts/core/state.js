// MyCMS - état partagé entre les modules (pas de variables globales : un seul objet, importé là où il sert)

export const state = {
    // Configuration renvoyée par /api/config
    config: {},
    // Compte connecté (renvoyé par /api/auth/state)
    user: { name: "", admin: false },
    editor: {
        file: null, // Page ouverte
        hash: null, // Empreinte du fichier au chargement : refus de sauvegarder s'il a changé depuis
        // index -> { el, kind: "rich" | "src", card, initial, locks, published }
        fields: new Map(),
        publishedKnown: false, // Version publiée connue (repository avec une branche distante)
        elementCount: 0,
        category: "", // Catégorie affichée (vide : toutes)
    },
    // Branche du site (onglet Git) : actuelle, et publiée (celle du site en ligne)
    branch: { current: "", published: "" },
    preview: {
        running: false, // Serveur de prévisualisation
    },
};
