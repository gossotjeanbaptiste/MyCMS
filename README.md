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

## 📦 Installation (Windows)

Lancer `MyCMS-<version>.msi` : il installe MyCMS dans `Program Files`, crée les raccourcis (menu Démarrer et bureau) et embarque Git (MinGit). Il n'y a rien d'autre à installer : ni Python, ni Git.

Sur un nouveau poste, onglet **Git** → **Récupérer le site depuis GitHub** : coller l'adresse du repository puis **Cloner**. GitHub peut demander de se connecter dans le navigateur. Si Git est déjà installé sur le poste, c'est celui-là qui est utilisé.

Au premier lancement, MyCMS demande de créer un identifiant et un mot de passe (8 caractères minimum). Ils sont ensuite demandés à chaque ouverture de l'interface, et le mot de passe se change dans **Paramètres**. Le mot de passe n'est pas stocké, seulement son empreinte (scrypt), dans `%USERPROFILE%\.rout_art_cms\auth.json`. En cas d'oubli : fermer MyCMS, supprimer ce fichier, puis relancer pour recréer les identifiants.

Pour générer l'installeur : `compile_msi.bat`. Il compile l'exécutable, télécharge MinGit (version fixée, vérifiée par SHA-256) puis construit le `.msi` dans `dist/`. Nécessite Python avec `cms/requirements.txt` et le [SDK .NET](https://dotnet.microsoft.com/download) (WiX est récupéré automatiquement). La version du `.msi` est celle de `cms/web/package.json` : l'augmenter pour chaque nouvelle version distribuée.

## 🚀 Lancement depuis les sources

```bash
pip install -r cms/requirements.txt
python app.py
```

Ou sous Windows : `run.bat` (installe les dépendances si besoin). Pour générer seulement le `.exe` (sans le `.msi`) : `python cms/source/build_exe.py`.

Plus de détails dans [cms/DOCUMENTATION.md](cms/DOCUMENTATION.md).

## 🔄 Refonte web à venir

L'application va subir une **refonte totale** : l'interface actuelle, réalisée avec **CustomTkinter (CTk)**, sera remplacée par une **interface web**.

Les différentes issues connues de la version actuelle ne seront donc pas corrigées sur la version CTk : elles devraient (en tout cas c'est l'objectif) être réglées avec ce rework en web.

Autre objectif du rework : le CMS ne s'appuiera plus sur une liste de pages codée en dur, il détectera automatiquement les pages HTML du site.
