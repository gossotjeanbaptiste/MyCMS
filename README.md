# MyCMS

Petit CMS local en Python, avec une interface web, pour mettre à jour le contenu de son site web statique (HTML hébergé sur un dépôt Git) sans avoir à toucher au code HTML ni à la ligne de commande Git.

## 🎯 Ce que fait l'application

- **Édition du contenu** : sélection d'une page HTML du site, affichage des éléments modifiables (textes, prix…) sous forme de champs, puis sauvegarde dans le fichier (via BeautifulSoup).
- **Synchronisation Git** : pull, statut du dépôt, ajout des fichiers non suivis, commit et push vers GitHub (via GitPython), pour publier les modifications sur le site.
- **Prévisualisation locale** : serveur HTTP intégré (port configurable) pour vérifier le rendu dans le navigateur avant de publier.
- **Génération du sitemap** : mise à jour automatique de `sitemap.xml` avec les vraies dates de modification des pages.
- **Paramètres** : chemin du dépôt du site (choisi dans l'Explorateur Windows), pull automatique au démarrage, URL du site, sauvegardés entre deux sessions.
- **Logs** : historique des opérations consultable et exportable.

Workflow type : **Pull → Éditer → Prévisualiser → Push**.

## 📦 Installation (Windows)

Lancer `MyCMS-<version>.msi` : il installe MyCMS dans `Program Files`, crée les raccourcis (menu Démarrer et bureau) et embarque Git (MinGit). Il n'y a rien d'autre à installer : ni Python, ni Git.

Sur un nouveau poste, onglet **Git** → **Récupérer le site depuis GitHub** : coller l'adresse du repository puis **Cloner**. GitHub peut demander de se connecter dans le navigateur. Si Git est déjà installé sur le poste, c'est celui-là qui est utilisé.

Au premier lancement, MyCMS demande de créer un identifiant et un mot de passe (8 caractères minimum). Ils sont ensuite demandés à chaque ouverture de l'interface et après chaque relancement de MyCMS, et le mot de passe se change dans **Paramètres**. Le mot de passe n'est pas stocké, seulement son empreinte (scrypt), dans `%USERPROFILE%\.mycms\auth.json`. Le dossier `.mycms` est caché (afficher les éléments masqués dans l'Explorateur pour le voir), et `auth.json` est verrouillé : il peut être lu ou supprimé, mais pas modifié. En cas d'oubli : fermer MyCMS, supprimer ce fichier, puis relancer pour recréer les identifiants.

Pour générer l'installeur : `compile_msi.bat`. Il compile l'exécutable, télécharge MinGit (version fixée, vérifiée par SHA-256) puis construit le `.msi` dans `dist/`. Nécessite Python avec `cms/requirements-build.txt` et le [SDK .NET](https://dotnet.microsoft.com/download) (WiX est récupéré automatiquement). La version du `.msi` est celle de `cms/web/package.json` : l'augmenter pour chaque nouvelle version distribuée.

## 🚀 Lancement depuis les sources

```bash
pip install -r cms/requirements.txt
python cms/web/server.py
```

Ou sous Windows : `run.bat` (installe les dépendances si besoin). Pour générer seulement le `.exe` (sans le `.msi`) : `pip install -r cms/requirements-build.txt` puis `python cms/installer/build_exe.py`.

Les notes techniques (architecture, règles à respecter, tests) sont dans [AGENTS.md](AGENTS.md).
