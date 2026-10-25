# MyCMS

Petit CMS de bureau en Python pour mettre à jour le contenu de son site web statique (HTML hébergé sur un dépôt Git) sans avoir à toucher au code HTML ni à la ligne de commande Git.

> ⚠️ **Refonte en cours** — voir la section [Refonte web à venir](#-refonte-web-à-venir).

## 🎯 Ce que fait l'application

- **Édition du contenu** : sélection d'une page HTML du site, affichage des éléments modifiables (textes, prix…) sous forme de champs, puis sauvegarde dans le fichier (via BeautifulSoup).
- **Synchronisation Git** : pull, statut du dépôt, ajout des fichiers non suivis, commit et push vers GitHub (via GitPython), pour publier les modifications sur le site.
- **Prévisualisation locale** : serveur HTTP intégré (port configurable) pour vérifier le rendu dans le navigateur avant de publier.
- **Génération du sitemap** : mise à jour automatique de `sitemap.xml` avec les vraies dates de modification des pages.
- **Paramètres** : chemin du dépôt du site, options de pull/refresh automatiques, sauvegardés entre deux sessions.
- **Logs** : historique des opérations consultable et exportable.

Workflow type : **Pull → Éditer → Prévisualiser → Push**.

## 🚀 Lancement

```bash
pip install -r cms/requirements.txt
python app.py
```

Ou sous Windows : `run.bat` (installe les dépendances si besoin), et `compile.bat` pour générer un `.exe` avec PyInstaller.

Plus de détails dans [cms/DOCUMENTATION.md](cms/DOCUMENTATION.md).

## 🔄 Refonte web à venir

L'application va subir une **refonte totale** : l'interface actuelle, réalisée avec **CustomTkinter (CTk)**, sera remplacée par une **interface web**.

Les différentes issues connues de la version actuelle ne seront donc pas corrigées sur la version CTk : elles devraient (en tout cas c'est l'objectif) être réglées avec ce rework en web.

Autre objectif du rework : le CMS ne s'appuiera plus sur une liste de pages codée en dur, il détectera automatiquement les pages HTML du site.
