// MyCMS - état partagé entre les modules (pas de variables globales : un seul objet, importé là où il sert)

export const state = {
    // Configuration renvoyée par /api/config
    config: {},
    editor: {
        file: null, // Page ouverte
        hash: null, // Empreinte du fichier au chargement : refus de sauvegarder s'il a changé depuis
        // index -> { el, kind: "rich" | "src", card, initial, locks, published }
        fields: new Map(),
        publishedKnown: false, // Version publiée connue (repository avec une branche distante)
        elementCount: 0,
    },
    preview: {
        running: false, // Serveur de prévisualisation
    },
};
