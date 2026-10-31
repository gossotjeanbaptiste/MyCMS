# MyCMS : notes pour les agents

À lire en début de conversation. À tenir à jour quand l'architecture, les commandes ou les règles changent.

## Le projet

CMS local qui permet de modifier les textes d'un site statique (HTML hébergé sur GitHub / GitHub Pages) sans toucher au code. L'utilisateur final n'est pas technique : c'est la personne qui gère les textes du site. L'interface est web (Flask + Tailwind), servie en local, et distribuée sous Windows en `.exe` et en `.msi`.

- Langue : interface, messages, commentaires et docstrings en **français**. Noms de variables et de fonctions en anglais.
- Branche de travail : `web_v2`. Version courante : 2.3.1 (la 2.0.9 a été sautée).
- **Aucun nom de client dans le dépôt** : MyCMS est une version personnelle. Pas de nom de client ni d'organisation dans le code, les tests, la doc ou les messages de commit ; utiliser des noms neutres (`MyCMS`, `exemple`, `MonSite`).
  - La règle vaut pour les **fichiers actuels et les nouveaux commits**. L'historique existant (`main`, la branche `old`, les commits qui documentent la reprise et le renommage des dossiers) vient de la version d'origine, faite pour un client : il le nomme légitimement, et il ne faut pas le réécrire.
- Site de référence pour les tests : un vrai site local, dont le chemin se passe aux tests par `MYCMS_SITE` (voir « Tests »). Il est en CRLF, compte 17 pages, et `page/formations.html` contient 229 éléments éditables.
  - **Ne jamais modifier ce dossier pendant les tests.** Travailler sur un clone, dans un dossier temporaire.
  - **Tests de publication** : seulement sur la branche `test_for_cms`, prévue pour ça. Cloner cette branche seule (`git clone --single-branch -b test_for_cms …`) et fixer la cible du push (`git config remote.origin.push refs/heads/test_for_cms:refs/heads/test_for_cms`). Jamais de push sur `main`, qui est le site en ligne.
  - Le push passe par SSH : lancer le serveur de test avec `USERPROFILE` temporaire mais le vrai `HOME`, sinon la clé SSH n'est pas trouvée.

## Arborescence

Un dossier par fonctionnalité, des fichiers de **200 lignes au plus**, et **pas de variable globale** (voir « Règles »).

- `cms/web/wsgi.py` : point d'entrée WSGI. `prepare_environment()` règle les chemins et le Git portable, `create_application()` construit l'application Flask, et `wsgi.app` la fournit à la demande (rien n'est créé à l'import). Un autre serveur peut la servir : `waitress-serve --listen=127.0.0.1:5050 wsgi:app`, depuis `cms/web`.
- `cms/web/server.py` : le lanceur, et le point d'entrée de l'exe. `main()` gère l'instance unique, l'icône et le navigateur, puis sert `wsgi.create_application()` avec **Waitress** (`THREADS = 8`). Options `--port`, `--no-browser` et `--no-tray`.
- `cms/web/api/` : l'application Flask.
  - `create_app()` (`__init__.py`) crée l'application et enregistre un blueprint par domaine : `auth` (connexion exigée avant chaque requête, `before_app_request`), `users` (gestion des comptes, administrateurs seulement), `pages`, `settings` (configuration, logs, choix d'un dossier), `repository` (Git), `branches` (branches du site), `publish` (vérification, mise en ligne, reprise de la version en ligne), `editor`, `structure` (dupliquer, supprimer), `media` (images), `site` (sitemap, prévisualisation) et `shutdown` (Quitter).
  - `services.py` : la classe `Services` regroupe les gestionnaires et l'état du processus (`boot_id`, prévisualisation, icône). Elle est rangée dans `app.extensions["mycms"]`, et les routes l'obtiennent avec `services()`.
- `cms/web/templates/` : modèles Jinja.
  - `index.html` inclut `tabs/*.html` (un onglet par fichier ; `settings-users.html` est inclus par `settings.html`) et `dialogs/*.html` (guide, Quitter).
  - `login.html` : la connexion.
- `cms/web/static/` :
  - `scripts/` : modules ES, sans framework. `main.js` (l'interface) et `login.js` (la connexion) sont les points d'entrée.
    - `core/` : `dom.js` (`$`, `api`, `toast`…), `state.js` (état partagé), `tabs.js` et `poller.js` (interrogation régulière du serveur).
    - `editor/` : `editor.js` (ouverture, sauvegarde), `cards.js`, `input.js`, `rich-editor.js` (`buildRichEditor`, `serializeRich`), `markers.js`, `search.js`, `categories.js` (filtres par catégorie), `structure.js` (actions des cartes), `image-field.js` (carte d'une image) et `format-bar.js`.
    - `preview/` : `pane.js` et `pane-code.js` (aperçu de l'éditeur), `preview.js` (onglet), `preview-helper.js` (injecté dans les pages du site servies par la prévisualisation).
    - `git/` : `git.js`, `branches.js` (carte Branches), `publish-checks.js` (vérification, mise en ligne, conflit), `history.js` et `history-details.js` (historique et détail d'une modification) et `browse.js` (« Parcourir… »).
    - `quit/` : `quit.js` et `quit-content.js`.
    - `settings/` : `settings.js`, `account.js` (« Mon compte »), `users.js` (compte connecté, carte Utilisateurs), `update.js` (nouvelle version), `header.js` (guide, déconnexion) et `logs.js`.
  - `style.css` : généré par Tailwind, ne pas l'éditer à la main.
  - `highlight.css` : surlignage de la recherche, hors Tailwind.
  - `logo.png` : le logo carré de la page de connexion, l'image 256 px de `cms/icon/logo.ico`.
  - `logo-wide.png` : le logo horizontal de l'en-tête (logos à gauche, « MyCMS » à droite).
- `cms/web/src/` : sources Tailwind v4. `input.css` importe `theme.css` (couleurs) et `components/*.css` (une couche `@layer components` par fichier).
- `cms/source/` : le code métier, importé par paquet (`from content.html.html_tree import parse`). Un sous-dossier par fonctionnalité, chacun avec son `__init__.py`.
  - `version.py` : `VERSION`, la version de MyCMS.
  - `core/` :
    - `auth/` : `auth_manager.py` (comptes, rôles, profil ; empreinte par défaut de Werkzeug : scrypt depuis la 3.0, pbkdf2 avant) et `auth_file.py` (`auth.json` verrouillé, reprise de l'ancien format) ;
    - `storage/` : `data_dir.py` (dossier `~/.mycms`, caché, et verrouillage de fichiers) et `config_manager.py` (`config.json`) ;
    - `logs/` : `logger.py` et `log_buffer.py` (journal numéroté) ;
    - `updates.py` : nouvelle version sur GitHub, téléchargement vérifié de son `.msi`.
  - `content/` :
    - `html/` : `html_tree.py` (arbre HTML avec les positions exactes dans le fichier), `hybrid_saver.py` et `node_diff.py` (la sauvegarde hybride), `html_manager.py` (extraction des `.editable`, `apply_editable_html`, extraits de code) ;
    - `pages/` : `page_finder.py` (détection des pages), `css_weights.py` (gras d'après le CSS du site : `<link>`, `@import`, variables, spécificité, héritage), `categories.py` (catégorie de chaque élément éditable) et `structure.py` (dupliquer ou supprimer un élément de liste ou une ligne de tableau) ;
    - `versions/` : `published.py` (version publiée de chaque élément, associée par le contenu) et `changes.py` (changements d'une page entre deux versions, pour l'historique).
  - `publishing/` :
    - `git/` : `git_manager.py` (clone, `pending()`, `unpublished_pages()`, version publiée), `git_sync.py` (pull et push, conflits), `branches.py` (branches du site), `git_status.py` (rapport de l'onglet Git), `history.py` et `commit_details.py` (historique lisible et détail d'une modification) ;
    - `sitemap/` : `sitemap_generator.py`, `sitemap_files.py`, `robots.py` et `site_url.py` (sitemap, robots.txt, URL du site) ;
    - `verification/` : `checks.py` (vérification avant publication) et `online.py` (suivi de la mise en ligne).
  - `desktop/` : `server_manager.py` (prévisualisation, `ThreadingHTTPServer` sur 127.0.0.1), `folder_picker.py` (classe `FolderPicker`), `tray.py` (icône de notification), `startup.py` (instance unique, port libre, `show_error`), `installer.py` (lance `msiexec`) et `auto_update.py` (mise à jour au démarrage).
- `cms/installer/` : compilation. `build_exe.py` et `mycms.spec` (PyInstaller), `build_msi.py`, `MyCMS.wixproj` et `Package.wxs` (WiX, avec Git portable MinGit).
  - Un nouveau module Python doit être ajouté aux `hiddenimports` de `mycms.spec`, et un nouveau dossier de l'interface à ses `datas`.
- `cms/icon/logo.ico` : l'icône de l'exe, de l'installeur et de la zone de notification.
- `scripts/` : `run.bat` (lancement depuis les sources, sur le port 5050), `run_tests.bat` (les tests) et `compile_msi.bat` (l'installeur). Chacun cherche seul la racine du dépôt (son dossier, ou le dossier parent) : ils marchent dans `scripts/` comme copiés à la racine. Dans la suite de ce fichier, `run.bat`, `run_tests.bat` et `compile_msi.bat` désignent ces scripts.
- `.github/workflows/` : `tests.yml` (tests à chaque push) et `release.yml` (`.msi` joint à une release, sur un tag `v<version>` ; l'exe seul n'est pas publié).
- `cms/tests/` (pytest) et `cms/web/tests/` (`node:test`) : les tests, lancés par `scripts/run_tests.bat` (voir « Tests »).
- `docs/` : `AGENTS.md` (ce fichier), `CLAUDE.md` (qui l'importe) et `contrat-licence-commerciale-MyCMS.md` (modèle de contrat de licence d'usage interne, aussi publié sur Notion et lié depuis le README).
  - À la racine, `CLAUDE.md` tient en une ligne, `@docs/AGENTS.md` : Claude Code ne charge automatiquement que le `CLAUDE.md` de la racine. Ne pas le supprimer, sinon les règles de ce fichier ne sont plus chargées en début de session.

## Commandes

- Tests : `scripts\run_tests.bat`, ou `python -m pytest` et `cd cms/web && npm test`.
- Lancer : `python cms/web/server.py`, ou `python cms/web/server.py --port 5060 --no-browser --no-tray`.
- Dépendances : `cms/requirements.txt` pour l'exécution, `cms/requirements-build.txt` (ajoute PyInstaller) pour compiler, `cms/requirements-dev.txt` (ajoute pytest) pour les tests.
- CSS, après toute modification de `src/` ou ajout de classes Tailwind dans les modèles ou les scripts : `cd cms/web && npm run build:css`. `style.css` est versionné, pour que l'application tourne sans Node.
- Exécutable : `python cms/installer/build_exe.py`, qui produit `dist/MyCMS.exe`.
- Installeur : `scripts\compile_msi.bat`, qui produit `dist/MyCMS-<version>.msi`. Nécessite le SDK .NET.
- Version : la changer **à la fois** dans `cms/web/package.json` (lue par le `.msi`) et dans `cms/source/version.py` (lue par l'application), ainsi que dans le badge « Version » du `README.md`. Un test vérifie que les trois sont identiques.
- Publier une version : `git tag v<version>` puis `git push origin v<version>`. Le workflow `release.yml` vérifie que le tag correspond à la version, lance les tests, compile et crée la release.

## Règles à ne pas casser

- **Sauvegarde fidèle.**
  - Jamais de `prettify()` ni de réécriture complète du fichier.
  - `HybridSaver` recopie à l'octet près les nœuds inchangés et ne réécrit que les écarts.
  - Seul le HTML nouveau est nettoyé : `strong`, `em`, `a[href]` et `br` sont gardés, le reste est retiré.
  - Les pages se lisent et s'écrivent avec `newline=""`, car le site est en CRLF.
- **Aller-retour sans modification** : charger une page dans l'éditeur puis la renvoyer sans rien changer doit la laisser identique à l'octet près.
- **Index des éléments** : un élément est identifié par sa position parmi les balises ouvrantes `.editable` du document. La sauvegarde vérifie l'empreinte du fichier et répond 409 s'il a changé depuis son chargement.
- **Éléments `.editable` imbriqués** : ils sont verrouillés dans leur parent, sous la forme du marqueur `<mycms-lock data-index="N">`. Le serveur refuse une sauvegarde qui les supprimerait.
- **Gras** :
  - pas de gras par défaut sur les titres : seulement `<strong>`, `<b>` ou une règle du CSS du site ;
  - on ne retire pas le gras d'un élément qui est lui-même un `<strong>` ou qui est gras via le CSS : un message l'explique à l'utilisateur.
- **Python modifié = serveur à relancer.** Flask ne recharge pas le code. Le JS et le CSS sont relus au F5. Si le JS reçoit une réponse d'un serveur obsolète, il affiche un message pour relancer.
- **Emojis dans la console** : ils plantent sur une console non UTF-8. Le logger et les scripts de compilation sont protégés contre ça ; garder cette protection.
- **200 lignes au plus par fichier**, Python, JS, HTML et CSS. Au-delà, découper par fonctionnalité, dans un sous-dossier si besoin.
- **Pas de variable globale.**
  - Python : pas de `global` ni d'état modifiable au niveau d'un module. L'état vit dans une instance : `Services`, ou une classe comme `FolderPicker`. Seules les constantes en MAJUSCULES et les blueprints `bp` restent au niveau du module.
  - JS : modules ES uniquement, sans rien poser sur `window`. L'état partagé est dans `core/state.js`, et l'état propre à une fonctionnalité dans un objet privé de son module. Chaque module exporte une fonction `init…()`, appelée par `main.js`.
- **Prévisualisation** : servie sur `127.0.0.1` (pas `localhost`, qui coûte environ 2 s sous Windows) et multi-thread (les préconnexions des navigateurs bloquaient un serveur mono-thread).

## Fonctionnalités de la v2.0.1

- **Guide d'utilisation** : une boîte de dialogue qui explique les étapes Récupérer → Modifier → Vérifier → Publier → Quitter.
  - Elle s'ouvre au démarrage tant que `show_guide` vaut vrai dans la config, et se rouvre avec le bouton *Guide*.
- **Bouton Quitter** :
  - `GET /api/quit/check` liste ce qui reste à faire : fichiers non publiés, commits pas encore envoyés, prévisualisation active. Les modifications non sauvegardées de l'éditeur sont comptées côté navigateur.
  - L'interface propose trois choix, les seuls pertinents étant affichés :
    - **Revenir à l'état de base** : retour au dernier commit avec `POST /api/git/discard` (`git reset --hard HEAD`). Les commits pas encore envoyés sont conservés. Les fichiers nouveaux ne sont supprimés (`git clean -fd`) que si la case dédiée est cochée. Ce choix est affiché en rouge et demande une confirmation.
    - **Sauvegarder et quitter** : sauvegarde sans commit, pour reprendre plus tard. C'est le choix par défaut.
    - **Publier sur le site et quitter** : sauvegarde, commit et push (le site en ligne est mis à jour). Le message du commit propose les mêmes messages préfaits que l'onglet Git, recopiés depuis `#commit-presets`. Sans rien à commiter, envoie seulement les commits en attente.
  - En cas d'échec, MyCMS ne se ferme pas, et une étape déjà réussie n'est pas refaite.
  - `POST /api/quit` arrête la prévisualisation et ferme la session, puis termine le processus avec `os._exit` juste après la réponse.
- **Marqueurs « pas encore publié »** : chaque élément de l'éditeur est comparé à sa version envoyée sur GitHub.
  - Un badge et une carte teintée indiquent **+** (vert, plus de texte), **−** (rouge, moins de texte) ou **~** (même longueur, contenu modifié).
  - Les marqueurs restent tant que ce n'est pas poussé, et tiennent compte des modifications non sauvegardées.
  - Côté serveur, `git_manager.published_file` lit la version de la branche distante suivie, dans son dernier état connu, sans requête réseau. Le chargement d'une page renvoie `published_known` ainsi que `published_html` et `published_value` pour chaque élément.
  - Côté navigateur, la version publiée passe par `buildRichEditor` puis `serializeRich`, pour être comparable à `fieldValue()`. La page ouverte est rechargée après un pull ou un push.
- **`git_manager.push`** envoie aussi les commits restés en attente, par exemple après un push précédent qui a échoué.

## Fonctionnalités de la v2.0.2

- **Plus de terminal** : l'exécutable est compilé avec `console=False` dans `mycms.spec`. `run.bat` garde sa console pour le développement.
- **Icône dans la zone de notification** (`pystray` et Pillow) : « Ouvrir MyCMS » ouvre l'interface ; « Quitter MyCMS… » ouvre `/#quit`, c'est-à-dire la fenêtre Quitter de l'interface, avec les mêmes vérifications. Le `#quit` survit à la redirection vers `/login` (voir `login.js`). L'icône est retirée avant `os._exit`, sinon elle resterait affichée jusqu'au survol.
- **Instance unique** : au démarrage, si MyCMS répond déjà sur le port, on ouvre simplement l'interface et on s'arrête.
- **Erreurs visibles sans console** : `show_error` (`desktop/startup.py`) affiche une boîte de message Windows (`MessageBoxW`), par exemple si le port est pris par un autre programme ou si le serveur s'arrête sur une erreur. Dans les tests, remplacer `desktop.startup.show_error`, sinon la boîte bloque le test et s'affiche sur l'écran de l'utilisateur.

## Fonctionnalités de la v2.0.3

- **Reconnexion obligatoire après un relancement** : `BOOT_ID`, tiré au hasard à chaque démarrage du serveur et jamais enregistré, est exigé dans la session (`session["boot"]`). La clé secrète des cookies, enregistrée dans `auth.json`, ne change pas ; sans ce contrôle, un navigateur resté ouvert retrouvait sa session après un relancement.

- **Bouton « Parcourir… »** à côté des champs de chemin (onglet Git, dossier de destination du clone, Paramètres) : ouvre la fenêtre « Choisir un dossier » de l'Explorateur Windows.
  - Le navigateur ne donne jamais le chemin complet d'un dossier : c'est le serveur local qui ouvre la fenêtre, par `POST /api/browse-folder`.
  - `folder_picker.py` appelle l'API Windows `IFileOpenDialog` via `ctypes` : pas de dépendance, et tkinter n'est pas embarqué. Un thread COM « STA » dédié est utilisé, et une seule fenêtre peut être ouverte à la fois (409 sinon).
  - La fenêtre a pour propriétaire la fenêtre active au moment du clic (le navigateur), pour s'ouvrir au premier plan.
  - Onglet Git : le dossier choisi est aussitôt utilisé, comme avec « Vérifier ».
  - Tests : la vraie fenêtre s'ouvre. La trouver par son titre (`FindWindowW`), puis la valider (`WM_COMMAND` avec `IDOK`) ou l'annuler (`WM_CLOSE`), depuis un processus séparé lancé **sans bloquer** Node.

- **Dossier de données `~/.mycms`** : il reçoit l'attribut « caché » de Windows, puisque le point au début du nom ne cache rien sous Windows.
- **`auth.json` verrouillé** : règle NTFS `icacls /deny *S-1-1-0:(WD,AD)` (SID de « Tout le monde », indépendant de la langue). Ailleurs : `chmod 400`.
  - `AuthManager._save` lève le verrou, écrit, puis le remet. Le verrou est aussi posé au démarrage sur un fichier existant.
  - La lecture et la suppression restent possibles : supprimer `auth.json` reste la procédure en cas de mot de passe oublié. Ne pas ajouter l'attribut « lecture seule » ni interdire la suppression.
  - C'est une protection contre une modification à la main, pas contre le propriétaire du fichier, qui peut retirer la règle.
  - `icacls` écrit dans l'encodage OEM de la console : ne pas décoder sa sortie en UTF-8.

## Optimisations de la v2.0.4

- **Exe allégé** : `mycms.spec` exclut ce que PyInstaller embarquerait parce que c'est installé sur le poste de compilation (`numpy`, que Pillow importe s'il est présent ; `psutil`, `yaml`, `setuptools`, `unittest`, `pydoc`…) et les extensions de Pillow inutiles (`_avif`, `_webp`, `_imagingcms`…). Seul le format de l'icône (`.ico`) sert à Pillow. Après un ajout de dépendance, vérifier que l'exe démarre bien, car une exclusion de trop ne se voit qu'à l'exécution.
- **MinGit** reste complet : il contient Git Credential Manager (connexion à GitHub dans le navigateur).
- **Supprimés** : l'ancienne interface CustomTkinter (`mycms.py`) et ses anciennes docs, `app.py` (doublon de `run.bat`), `logo.png` (l'icône de notification utilise `logo.ico`), la classe `GitManager` en double et les méthodes jamais appelées. `config_manager` ignore les clés obsolètes d'une ancienne configuration (`theme`, `window_width`, `window_height`, `auto_refresh`).
- **Croix de l'aperçu de l'éditeur** : ferme l'aperçu **et** arrête le serveur de prévisualisation (`POST /api/preview/stop`). Il redémarre tout seul quand on rouvre l'aperçu. Le bouton « Aperçu » se contente de masquer ou d'afficher le panneau.
- **Réglage « Rafraîchir automatiquement l'éditeur » supprimé** (`auto_refresh`) : il était enregistré mais n'avait jamais d'effet, déjà dans la version CTk. La page ouverte se recharge de toute façon après un pull ou un push.

## Changements de la v2.0.5

- **Nouveau logo** (`cms/icon/logo.ico`) : logos Python et Git sur une tuile bleu nuit arrondie (`#1E293B`).
  - En 64, 128 et 256 px, le texte « MyCMS » est ajouté sous les logos : « My » en jaune Python (`#FFD43B`), « CMS » en orange Git (`#F05133`), police Segoe UI Black.
  - En 16, 24, 32 et 48 px, la tuile n'a pas de texte, qui serait illisible.
  - Le `.ico` contient donc deux dessins différents selon la taille. Pour le régénérer avec Pillow, passer chaque taille déjà redimensionnée dans `append_images`, sinon Pillow redimensionne une seule image pour toutes les tailles. Les images sources ne sont pas versionnées.

## Changements de la v2.0.6

- **Icône de notification absente avec `run.bat`** : `run.bat` ne testait que `import flask`. Un poste qui avait déjà Flask ne recevait donc jamais `pystray` ni Pillow, ajoutés en v2.0.2, et le serveur démarrait sans icône, avec seulement une ligne dans les logs.
  - `run.bat` vérifie désormais toutes les dépendances d'exécution avec `importlib.util.find_spec`, sans les importer. `import git` échoue sur un poste sans Git, et relancerait l'installation à chaque démarrage.
  - **Une dépendance ajoutée à `cms/requirements.txt` doit aussi être ajoutée à la liste de `run.bat`**, en utilisant le nom du module (`bs4`, `git`, `PIL`) et non celui du paquet.
- **Guide, section « Bon à savoir »** (`index.html`) : l'ordre des points est changé.
  - En premier : seuls les éléments `class="editable"` sont modifiables. C'est volontaire, et rendre un nouveau texte modifiable demande un développeur.
  - En dernier : « Sauvegarder n'est pas publier ».

## Changements de la v2.0.7

- **Ménage : fichiers de 200 lignes au plus, rangés par fonctionnalité, sans variable globale.** Le comportement ne change pas, et l'arborescence est décrite plus haut.
  - `server.py` (714 lignes) devient `server.py`, avec `cms/web/api/` (un blueprint par domaine et `Services`) et `desktop/tray.py` et `startup.py`.
  - `app.js` (1425 lignes) devient une vingtaine de modules ES dans `static/scripts/`, et `index.html` des modèles Jinja dans `templates/`.
  - `html_source.py`, `git_manager.py`, `sitemap_generator.py` et `input.css` sont découpés.
  - Les scripts de compilation passent dans `cms/installer/`.
- **Vérifié** : les sorties du code métier (sauvegarde, extraction, gras, extraits, sitemap, statut Git) sont identiques avant et après le découpage, sur les 17 pages du site. Le CSS compilé est identique à l'octet près.
- **Configuration incomplète au premier lancement (corrigé)** : sans `config.json`, le cache de `ConfigManager` restait vide, puis ne contenait que le premier réglage enregistré. `get_all_config()` renvoyait alors seulement `repo_path`, et l'aperçu refusait de démarrer (« Le port doit être un nombre valide ») jusqu'au relancement. `get_all_config()` renvoie maintenant `self.config`, qui est toujours complet.

## Changements de la v2.0.8

- **Plusieurs utilisateurs**, chacun avec son identifiant et son mot de passe.
  - `auth.json` : `{"secret_key", "users": {"identifiant": {"password_hash", "session_id", "admin", "owner"}}}`. L'ancien format à un seul compte (`username`, `password_hash`, `session_id`) est converti au démarrage, et ce compte devient administrateur principal.
  - Deux rôles : **éditeur** (modifier et publier le site, changer son mot de passe) et **administrateur** (gérer les comptes, en plus).
  - **Administrateur principal** (`owner`) : le compte créé au premier lancement. Personne, pas même lui, ne peut le rétrograder ni le supprimer, et lui seul peut changer son mot de passe. Un fichier sans `owner` en reçoit un au démarrage : le premier administrateur.
  - L'identifiant est reconnu sans tenir compte des majuscules, à la connexion comme pour les doublons.
  - La session contient l'identifiant (`session["user"]`) et le `session_id` du compte. Supprimer un compte, ou changer ou réinitialiser son mot de passe, ferme donc ses sessions ouvertes.
  - API `users` (403 pour un éditeur) : `GET /api/users`, `POST /api/users`, `POST /api/users/<nom>/password`, `POST /api/users/<nom>/role` et `DELETE /api/users/<nom>`. `GET /api/auth/state` renvoie aussi `admin`.
  - Il reste toujours au moins un administrateur : on ne peut ni supprimer ni rétrograder le dernier. On ne peut pas supprimer son propre compte, et son propre mot de passe se change avec « Changer le mot de passe ».
  - Onglet Paramètres, carte **Utilisateurs** (administrateurs seulement) : liste, ajout, nouveau mot de passe, rôle, suppression.
  - Les connexions, déconnexions et changements de comptes sont écrits dans les logs avec le nom de l'utilisateur.

## Changements de la v2.1.0

- **Filtrage par catégories dans l'éditeur** : une barre de filtres au-dessus de la liste (« Tout », puis une par catégorie, avec le nombre d'éléments) et un intertitre dans la liste à chaque changement de catégorie.
  - Le serveur calcule les catégories (`content/pages/categories.py`) et le chargement d'une page renvoie `category` pour chaque élément. Rien n'est écrit dans le site.
  - Règles, dans l'ordre :
    1. attribut `data-category` sur l'élément ou un de ses parents : imposé par le développeur du site ;
    2. `<header>`, `<nav>`, `<footer>` : « En-tête », « Menu », « Pied de page » ;
    3. bloc nommé par la page : visé par un lien interne (`<a href="#cfa">CFA</a>` d'un sommaire), ou dont l'`id` correspond à une `<option value>` (`id="table-b-traditionnel"` pour `value="b-traditionnel"`). On prend le texte du lien ou de l'option, celui que voit le visiteur. Un lien placé dans le bloc qu'il vise (« haut de page ») et les liens vers `html`, `body`, `main` ou `header` sont ignorés ;
    4. tableau avec une `<caption>`, ou une seule cellule `<th>` sur sa première ligne : ce titre (plusieurs `<th>` sont des en-têtes de colonnes) ;
    5. sinon, le dernier titre `<h1>` à `<h3>` qui précède l'élément (lui compris), hors en-tête, menu et pied de page, ou « Autres ». Un sous-titre, c'est-à-dire un titre qui suit un titre plus important dans le même parent (le `<h3>` sous le `<h2>` d'un bloc), ne crée pas de catégorie.
  - Les catégories sont comparées sur leur texte complet : deux titres qui commencent pareil ne sont pas fusionnés. Seule l'interface raccourcit l'affichage.
  - Sur le site de référence : 11 catégories pour `formations.html` et `tarifs.html` (les mêmes noms), 8 pour les mentions légales, 3 pour `financement.html` (les liens de son sommaire).
  - La barre est masquée s'il n'y a qu'une catégorie. Le filtre se combine avec la recherche. Il est gardé au rechargement de la même page (après une sauvegarde) et remis à « Tout » à l'ouverture d'une autre page.
  - Un point bleu sur un filtre signale des modifications non sauvegardées dans cette catégorie.
  - Une carte masquée par le filtre ou la recherche est réaffichée quand on y va depuis l'aperçu ou un bloc verrouillé (`revealCard`).

## Changements de la v2.1.1

- **Jeu de tests** : 354 tests Python et 61 tests de l'interface, dont l'aller-retour complet. Voir « Tests ».
  - Côté Python : 200 tests unitaires et fonctionnels, et 153 vérifications des règles du projet. Le dernier test lance l'aller-retour sur une copie du vrai site, et il est ignoré sans `MYCMS_SITE`.
- **Destination par défaut d'un clone (corrigé)** : sans dossier choisi, le nom du dossier vient de l'adresse du repository. Un chemin Windows (`C:\…\site.git`) n'était pas découpé sur `\`, et le clone partait à côté de la source au lieu du dossier personnel. Les adresses GitHub n'étaient pas touchées.

## Changements de la v2.1.2

- **Boutons des cartes**, sous le numéro de l'élément (`cards.js`, `structure.js`). Ce sont des icônes, et le libellé complet est dans l'infobulle.
  - **↺ Version en ligne** : visible quand la carte a un marqueur. Il remet le contenu publié dans l'éditeur, qu'il reste à sauvegarder.
  - **＋ Dupliquer** et **✕ Supprimer** : pour un élément de liste ou une ligne de tableau (`content/pages/structure.py`, `POST /api/structure/<page>` avec `hash`, `action` et `index`).
    - Élément de liste : depuis un `<li>` éditable, ou un élément éditable placé dans un `<li>`.
    - Ligne de tableau : seulement depuis une cellule éditable (`<td>`, `<th>`). Un paragraphe dans une cellule ne duplique pas la ligne.
    - Le fichier est modifié tout de suite. Ce qui n'est pas sauvegardé l'est d'abord (après confirmation), puis la page est rechargée.
    - La copie est placée sur sa propre ligne, avec la même indentation, et ses `id` reçoivent un suffixe (`-2`, `-3`…). On ne peut pas supprimer le dernier élément d'une liste ni la dernière ligne d'un tableau.
    - Contrôle d'empreinte (409) comme pour la sauvegarde, et sitemap régénéré.
  - Le texte des boutons est exclu de la recherche.
- **Images éditables** (`<img class="editable">`) : traitées comme les iframes, seul l'attribut `src` change (`SRC_TAGS` dans `html_tree.py`). Le site de référence n'en a pas encore : il faut ajouter la classe dans le HTML.
  - La carte montre une vignette (`GET /api/site-image`, limité aux images du site), l'adresse modifiable et un bouton « Choisir une image… ».
  - `POST /api/images` (multipart : `page`, `file`) copie le fichier dans `images/` sous un nom libre (`photo-2.png`…) et renvoie son adresse relative à la page.
  - Formats acceptés : PNG, JPG, GIF, WebP, AVIF ; pas de SVG, qui peut contenir du script. 10 Mo au plus.
  - `api()` (`dom.js`) envoie un `FormData` tel quel.
- **Version publiée associée par le contenu (corrigé)** (`content/versions/published.py`) : elle était associée par la position. Après un ajout ou une suppression, tous les éléments suivants recevaient de faux marqueurs, et « Version en ligne » aurait remis le texte d'un autre élément.
  - Maintenant : alignement `difflib` sur (balise, contenu). Dans un bloc modifié, les éléments les plus semblables sont associés, dans l'ordre (programmation dynamique, bornée à 2 500 comparaisons). Une copie fraîchement ajoutée est « nouvelle » (+).

## Changements de la v2.1.3

- **Vérification avant publication** (`publishing/verification/checks.py`, `GET /api/checks`). Avant chaque push (onglet Git et fenêtre Quitter), les pages pas encore publiées sont vérifiées. S'il y a des problèmes, ils s'affichent et l'utilisateur choisit de publier quand même ou non. Le bouton « Vérifier le site » (`?scope=all`) vérifie tout le site.
  - Vérifié : liens et images vers des fichiers absents (adresses résolues comme le navigateur, sans remonter au-dessus de la racine), ancres `#…` introuvables, `mailto:` et `tel:` mal formés, éléments éditables vides, `src` vide.
  - Les adresses externes ne sont pas vérifiées : pas de réseau.
  - Le site de référence a 2 vrais liens cassés dans `page/financement.html` (lignes 352 et 358) : `../files/…pdf` au lieu de `../files/voiture/…pdf`.
- **Suivi de la mise en ligne** (`publishing/verification/online.py`, `GET /api/online?page=…`). Le push renvoie `pages`, les pages HTML envoyées. L'onglet Git interroge le site en ligne toutes les 10 s, pendant 10 min au plus, jusqu'à ce qu'il renvoie le même contenu que les fichiers locaux, fins de ligne mises à part.
- **Conflits** (`publishing/git/git_sync.py`) : le repository n'est jamais laissé à moitié fusionné.
  - **Push refusé** parce que GitHub a reçu d'autres commits : MyCMS rejoue les commits locaux par-dessus (rebase), puis renvoie. En cas de vrai conflit, le rebase est annulé, le commit local est gardé, et la réponse contient `conflict: true` avec un message clair.
  - Le refus se détecte avec les drapeaux de `PushInfo` : Git écrit « rejected » dans la sortie, pas dans l'erreur (`_send`).
  - **Pull** : en cas de conflit, la fusion est annulée (`merge --abort`) et rien n'est récupéré. Si des modifications non commitées touchent les mêmes fichiers, un message demande de les publier ou de les annuler.
  - Après un conflit, le bouton rouge « Reprendre la version en ligne » (`POST /api/git/reset-to-remote`, `reset --hard` sur la branche distante) abandonne les modifications et commits locaux, après confirmation.
- **Pull avec des commits des deux côtés (corrigé)** : Git refusait avec « Need to specify how to reconcile divergent branches », sa configuration par défaut n'indiquant pas comment fusionner. Le pull passe maintenant `--no-rebase --no-edit`.

## Changements de la v2.1.4

- **Commits signés de la personne connectée** : l'auteur du commit créé par un push est le compte connecté. L'identité Git du poste reste le committer : GitHub affiche donc qui a écrit, et depuis quel poste.
  - `AuthManager.author()` donne le profil (nom, e-mail), sinon l'identifiant et `identifiant@mycms.local`.
  - Carte **« Mon compte »** dans les Paramètres (`settings-account.html`, `account.js`, `GET`/`POST /api/auth/profile`) : nom affiché et e-mail facultatif, enregistrés dans `auth.json` (`name`, `email`).
  - Les commits déjà en attente gardent leur auteur.
- **Historique lisible** dans l'onglet Git (`publishing/git/history.py`, `GET /api/git/history`, `git/history.js`). Il montre les 20 derniers commits : « Marie a modifié page/tarifs.html (et 1 autre fichier) », la date en français, la première ligne du message, et l'état « Publié » ou « Pas encore publié » (commit présent ou non sur la branche distante).
  - Il est rafraîchi avec le statut, après chaque action Git.
- Tests : GitPython lit l'identité du poste dans `~/.gitconfig` (pas dans `GIT_CONFIG_GLOBAL`). `conftest.py` y écrit donc la même identité de test.

## Changements de la v2.1.5

- **GitHub Actions** (`.github/workflows/`) :
  - `tests.yml` : `pytest -v` et `npm test` à chaque push et pull request, sous `windows-latest` (verrou NTFS, CRLF).
  - `release.yml` : sur un tag `v*`, vérifie que le tag correspond à `package.json`, lance les tests, compile `MyCMS-<version>.msi` (`build_msi.py` compile l'exe dans un dossier temporaire) et le joint à une release GitHub. L'exe seul n'est pas publié : le contrat de licence ne couvre que l'installeur.
  - Sur un dépôt privé, les minutes Windows comptent double dans le quota d'Actions.
- **Nouvelle version disponible** (`core/updates.py`, `GET /api/update`, `settings/update.js`) : au démarrage, la dernière release de `gossotjeanbaptiste/MyCMS` est comparée à `VERSION`. Si elle est plus récente, un lien « Nouvelle version X » apparaît dans l'en-tête.
  - La vérification est faite une fois par lancement (`Services.update`). Sans réseau, rien n'est signalé.
  - **L'API des releases n'est accessible que si le dépôt est public** : il est privé aujourd'hui (404), donc rien n'est signalé.
- **Version dans `cms/source/version.py`** (`VERSION`) au lieu de `cms/source/__init__.py`, que l'application ne pouvait pas importer (`cms/source` n'est pas un paquet) et que l'exe n'embarquait pas.
- **Ménage** :
  - Flask 3 et Werkzeug 3 (`flask>=3.0.0` dans `requirements.txt`). Les nouveaux mots de passe sont en scrypt, et les anciens en pbkdf2 se connectent toujours (testé).
  - Favicon de l'interface (`/favicon.ico`, public : c'est `logo.ico`). Elle donnait un 404 à chaque page.
  - `git_status.py` : l'ancien code de secours est retiré, et le rapport est identique (vérifié en comparant avec l'ancienne version).

## Changements de la v2.1.6

- **Détail d'une modification de l'historique** : un clic sur une ligne de l'historique de l'onglet Git la déplie (`git/history-details.js`, `GET /api/git/commit/<hash>`, `publishing/git/commit_details.py`, `content/versions/changes.py`). Le détail est chargé une seule fois.
  - Pour chaque page modifiée, les éléments éditables sont associés entre les deux versions comme pour les marqueurs (`published.align`). Chaque changement est classé « Modifié », « Mise en forme » (même texte : gras, lien…), « Ajouté » ou « Supprimé », avec sa catégorie.
  - Les mots supprimés sont barrés en rouge, les mots ajoutés surlignés en vert (`word_diff` : `difflib` sur les mots, chacun suivi de ses espaces, pour faire des blocs).
  - Une page dont aucun texte modifiable n'a changé l'indique (modification du code). Le diff Git reste dans un volet repliable « Voir le code modifié » (300 lignes au plus), puis viennent les autres fichiers.
  - Au plus 100 changements par page. Un premier commit, sans parent, montre toute la page comme ajoutée.
  - Un hash au bon format mais inconnu fait lever `BadName` par gitdb : la réponse est « Modification introuvable » (404).
- **Statut du repository** : la carte passe avant l'historique, et sa section « Historique récent » est retirée.
- **« Vérifier le site »** : les problèmes s'affichent dans un encadré rouge sous les boutons (`#check-results`, `.check-results.error`), avec la page, la ligne et une phrase sur quoi faire. Le message en bas de l'écran est rouge. Sans problème, l'encadré est vert. Avant, la liste allait dans le statut, plus bas, et le message était vert.
- **« ↺ Version en ligne »** : le message dit « sauvegardez » seulement s'il reste quelque chose à sauvegarder. Si le fichier enregistré était déjà la version en ligne, il dit « Texte revenu à la version en ligne : rien à sauvegarder ».

## Changements de la v2.1.7

- **Moins de requêtes inutiles** dans les onglets Prévisualisation et Logs, qui interrogeaient le serveur toutes les 2 s et toutes les secondes.
  - `core/poller.js` (`createPoller(intervalle, tick, active)`) n'interroge que si `active()` est vrai, se met en pause quand la fenêtre est cachée (`document.hidden`) et rattrape dès le retour (`visibilitychange`). Une erreur arrête l'interrogation.
  - Prévisualisation : seulement si l'onglet est ouvert **et** le serveur lancé. Serveur arrêté : une requête à l'ouverture, puis plus rien.
  - Journaux numérotés (`core/logs/log_buffer.py`, `LogBuffer`) : `GET /api/logs?since=n` et `GET /api/preview?since=n` ne renvoient que les lignes reçues après les n premières, avec `total` et `reset`. `reset` vaut vrai si des lignes ont été effacées ou sont trop anciennes : il faut alors remplacer l'affichage. Sans `since`, tout le journal.
  - Vérifié dans Chrome : serveur arrêté, 1 requête en 6,5 s (avant : 4) ; fenêtre cachée, 0.
- Tests JS : jsdom considère la page comme cachée par défaut. `setup-dom.mjs` lui passe `pretendToBeVisual: true`.

## Changements de la v2.1.8

- **Logo à la place du titre texte**, dans l'en-tête (40 px) et sur la page de connexion (96 px). `alt="MyCMS"` est gardé pour les lecteurs d'écran.
  - `static/logo.png` est l'image 256 px extraite de `cms/icon/logo.ico`, avec Pillow : `im = Image.open(ico); im.size = (256, 256); im.save(png)`.
  - **À régénérer quand l'icône change** : un test (`test_project_rules.py`) vérifie qu'ils sont identiques.
  - `/static/logo.png` fait partie des adresses publiques (`PUBLIC_PATHS`), car la page de connexion l'affiche.

## Changements de la v2.1.9

- **Logo horizontal dans l'en-tête** (`static/logo-wide.png`, 393 × 128, affiché en 40 px de haut). Les logos Python et Git de l'icône 256 px sont à gauche, sans son texte. À droite, « My » est en jaune Python (`#FFD43B`) et « CMS » en orange Git (`#F05133`), en Segoe UI Black, sur la tuile bleu nuit (`#1E293B`) aux coins arrondis.
  - La tuile garde le texte lisible dans les deux thèmes : le jaune serait illisible sur l'en-tête blanc du thème clair.
  - Composé avec Pillow à partir de `logo.ico`. Le script n'est pas versionné, comme les autres sources d'images : seule l'image l'est.
  - La page de connexion garde le logo carré (`logo.png`).

## Changements de la v2.1.10

- **`cms/source` rangé en sous-dossiers par fonctionnalité** (voir « Arborescence ») : `core/auth`, `core/logs`, `core/storage`, `content/html`, `content/pages`, `content/versions`, `publishing/git`, `publishing/sitemap` et `publishing/verification`. `desktop/` (4 fichiers) et `core/updates.py` restent à plat.
  - Les noms de fichiers sont gardés, et les déplacements faits avec `git mv` (historique conservé). Les imports deviennent `from content.html.html_tree import parse`, `from publishing.git.git_manager import GitManager`, etc.
  - Les `hiddenimports` de `mycms.spec` sont mis à jour et regroupés par dossier. L'exe recompilé a été vérifié.
- **Supprimés** : `cms/icon/make_wide_logo.py`, car les sources d'images ne sont pas versionnées (seul `logo-wide.png` l'est), et le dossier `assets/` vide à la racine.
- **Lancement** : le `.msi` installe `MyCMS.exe`, compilé par PyInstaller depuis `cms/web/server.py`. Il n'y a ni `app.py` (supprimé en v2.0.4) ni `wsgi.py`. Le serveur est celui de Flask (`app.run`, multi-thread, sur 127.0.0.1).

## Changements de la v2.2.0

- **Point d'entrée WSGI et serveur de production** : l'application n'est plus servie par le serveur de développement de Flask (`app.run`), mais par **Waitress** (`waitress>=3.0.0` dans `requirements.txt`, dans `run.bat` et dans les `hiddenimports`).
  - `cms/web/wsgi.py` fournit l'application (`create_application()`, `wsgi:app`), et `server.py` la lance avec `serve(app, host, port, threads=8, ident="MyCMS")`. `Resources` et `prepare_environment` passent de `server.py` à `wsgi.py`.
  - **8 threads** : certaines requêtes occupent un thread longtemps (fenêtre « Choisir un dossier », clone, push, démarrage de l'aperçu). Le nombre de threads est fixe, contrairement au serveur de Flask qui en créait un par requête.
  - Plus d'avertissement « development server ». L'en-tête HTTP `Server` vaut `MyCMS`.
  - Quitter garde `os._exit` après la réponse : vérifié dans l'exe recompilé (14,0 Mo, +180 Ko), le processus se ferme.
  - Dans les tests, `server.serve` est remplacé (il bloquerait). `test_waitress_serves_the_application` lance un vrai serveur Waitress sur un port libre.
- La version passe à 2.2.0 (changement de serveur).

## Changements de la v2.2.1

- **Aucune référence à un nom de client** dans le code, les tests et la doc : remplacée par `MyCMS` ou des noms neutres (`exemple`, `MonSite`). À vérifier avant chaque commit, avec un `git grep` insensible à la casse.
- **Dossier du site par défaut (corrigé)** : `~/mycms` (`ConfigManager.default_config`). Pendant le renommage, il était devenu le dossier personnel lui-même : l'éditeur aurait cherché des pages HTML dans tout le profil Windows, et deux tests échouaient.
- **Retiré** : la reprise automatique d'un ancien dossier de données au premier lancement (`data_dir.py`). Une installation qui aurait encore ses identifiants dans cet ancien dossier ne les retrouve plus.

## Changements de la v2.2.2

- **Ménage du code mort**, comme en v2.0.4 et v2.0.7. Le comportement ne change pas, sauf le correctif ci-dessous.
  - Recherche outillée : `vulture` (code jamais utilisé) et `pyflakes` (imports inutilisés) pour Python, plus une vérification des exports, imports, fonctions internes et `id` côté JS, des classes CSS des composants, et des routes de l'API sans appel dans l'interface. Ces outils ne sont pas des dépendances du projet. Il faut écarter leurs faux positifs : routes Flask, méthodes appelées par `HTMLParser` ou `http.server`, `__getattr__` de `wsgi.py`.
  - Résultat : pas d'import inutilisé, pas de route ni de classe CSS orpheline, pas de fonction JS jamais appelée. Le code mort était dans `config_manager.py`.
- **`ConfigManager` simplifié** :
  - retiré : le « cache » qui doublait `self.config` (il avait causé le bogue de la v2.0.7), l'attribut `_cache_dirty` jamais lu, les clés `required` du schéma jamais lues, la vérification `allowed` qui ne concernait aucune clé, et `get_show_guide()` et `get_default_port()`, jamais appelés (l'interface lit `get_all_config()`) ;
  - les accesseurs lisent `self.config`.
- **Réglage invalide sur une console non UTF-8 (corrigé)** : le message affiché contenait un emoji. Avec `run.bat`, son affichage plantait, et toute la configuration repartait des valeurs par défaut. Le message est maintenant sans emoji, et un test le vérifie.
- **Divers** :
  - un test sans intérêt retiré (`test_sitemap_info_reads_site`) ;
  - trois lignes mortes du `.gitignore` retirées (deux doublons de `__pycache__/`, un `.docx` temporaire étranger au projet) ;
  - le README ne dit plus que la sauvegarde passe par BeautifulSoup.

## Changements de la v2.2.3

- **Nouveau README**, sur le modèle de celui d'Echoing Void : logo centré (`cms/web/static/logo.png`), accroche, badges (Python, Flask, Waitress, Windows, version), puis « À propos », « Points forts », « Installation », « Pour les développeurs » et « Crédits & Licences ».
  - La documentation technique reste dans AGENTS.md, vers lequel le README renvoie.
  - **Licence PolyForm Noncommercial 1.0.0** (`LICENSE` : la ligne `Required Notice` avec le copyright de Jean-Baptiste GOSSOT, puis le texte officiel, inchangé). Les autres peuvent utiliser, modifier et partager MyCMS sans but commercial ; **seul l'auteur peut le vendre** ou accorder une licence commerciale. Ce n'est pas une licence open source au sens de l'OSI, et c'est voulu.
  - Le README annonce la licence par un badge et dans « Crédits & Licences », qui crédite aussi les dépendances, MinGit (GPLv2 : en cas de vente du `.msi`, indiquer où trouver le code source de Git) et les logos Python et Git.
  - Ne pas changer de licence sans l'accord de l'auteur, et ne jamais remettre une licence permissive (MIT…) dans l'historique : elle autoriserait la revente.
  - Le badge de version est vérifié par un test (`test_readme_version_badge`).
- **Publication prévue de la v2.2.3**, faite par l'auteur après relecture de son contrat de licence d'usage interne :
  1. pousser `web_v2` ;
  2. ouvrir une PR de `web_v2` vers `main` (la branche par défaut sur GitHub, qui contient encore la version d'origine) et la fusionner ;
  3. taguer `v2.2.3` sur le résultat.
- **`.gitattributes`** : fins de ligne fixées, quel que soit le réglage `core.autocrlf` du poste.
  - `cms/web/static/style.css` est en LF, comme Tailwind l'écrit. Git le prenait pour un fichier binaire (lignes très longues) et le stockait tel quel : chaque recompilation apparaissait comme une modification, sans aucun changement de règle CSS.
  - Les `.bat` sont toujours en CRLF : cmd gère mal les fins de ligne LF (étiquettes `goto`).
  - Ne pas repasser `style.css` en CRLF à la main avant un commit.
- **Scripts `.bat` rangés dans `scripts/`** (`run.bat`, `run_tests.bat`, `compile_msi.bat`), pour alléger la racine. Ils cherchent seuls la racine du dépôt, donc marchent aussi copiés ailleurs dans le dépôt (racine ou `scripts/`). `run.bat` et `compile_msi.bat` comptaient avant sur le dossier courant, ce qui ne marchait que par double-clic. `test_project_rules.py` lit la liste des dépendances dans `scripts/run.bat`.
- **Documentation rangée dans `docs/`** : `AGENTS.md`, `CLAUDE.md` et le modèle de contrat de licence d'usage interne. Un `CLAUDE.md` d'une ligne reste à la racine, et les liens (README, `pytest.ini`, `test_project_rules.py`) pointent vers `docs/AGENTS.md`.
  - Le contrat : usage interne seulement, à partir de l'installeur `.msi`, versions 2.2.3 et suivantes pendant la durée du contrat, commercialisation réservée à l'auteur, et clause d'interopérabilité (code source public sur GitHub). Le README renvoie à sa version Notion.
  - Pourquoi : ce contrat affirme que le code source de chaque version couverte (à partir de la 2.2.3) est publié sur https://github.com/gossotjeanbaptiste/MyCMS, ce qui écarte la décompilation au titre de l'interopérabilité (article L. 122-6-1, IV, du Code de la propriété intellectuelle). Le dépôt doit donc rester public, et chaque version doit être retrouvable par son tag.

## Changements de la v2.2.4

- **Release : le `.msi` seul** (`release.yml`). L'exe n'est plus joint à la release : le contrat de licence ne couvre que l'installeur. L'étape qui compilait l'exe à part est retirée, car `build_msi.py` le compile lui-même dans un dossier temporaire et ne laisse que le `.msi` dans `dist/`.
- Publiée comme la 2.2.3 : PR de `web_v2` vers `main`, fusion, puis tag `v2.2.4`.

## Changements de la v2.2.5

- **Tests lancés une seule fois par commit** (`tests.yml`). Ils se déclenchaient sur `push` et sur `pull_request` : un commit de `web_v2` avec une PR ouverte était testé deux fois, et un tag une troisième fois, alors que `release.yml` lance déjà les tests.
  - Maintenant : `push` sur les branches seulement (`branches: ["**"]`). Une PR affiche le résultat du push de sa branche, et les tags sont testés par `release.yml`.
  - Une PR venant d'un fork n'est donc pas testée automatiquement.

## Changements de la v2.3.0

- **Mise à jour depuis MyCMS**, sans passer par GitHub.
  - `core/updates.py` : la release donne aussi son `.msi` (`installer` : nom, adresse, taille, `sha256` tiré du champ `digest` de GitHub). `download()` l'enregistre dans `%TEMP%\MyCMS-update` et le supprime (`ValueError`) si sa taille ou son empreinte ne correspond pas.
  - `desktop/installer.py` : `msiexec /i <msi> /passive LAUNCHAPP=1`, détaché de MyCMS. Mode passif : une barre de progression, sans questions ; Windows demande l'autorisation d'administrateur (installation par machine).
  - `Package.wxs` : avec `LAUNCHAPP=1`, l'action `LaunchApplication` est aussi jouée après `InstallFinalize`, et relance MyCMS. L'assistant normal garde sa case « Lancer MyCMS ».
  - **Bouton « Nouvelle version »** (`settings/update.js`) : pour un administrateur, dans l'application installée (`GET /api/update` renvoie `auto`), il demande confirmation, sauvegarde l'éditeur, puis appelle `POST /api/update/install` (`api/shutdown.py`) : téléchargement, installeur, puis fermeture comme Quitter, et l'écran « MyCMS est fermé ». Sinon (éditeur, lancement depuis les sources), il mène toujours à la page de la release.
  - **Mise à jour automatique au démarrage** (`desktop/auto_update.py`, appelé par `server.main` après le contrôle d'instance unique) : réglage `auto_update`, **actif par défaut**, case « Mise à jour automatique au démarrage » dans les Paramètres. Si une version plus récente a un `.msi`, MyCMS le télécharge, lance l'installeur et ne démarre pas son serveur ; l'installeur le relance.
  - **Une seule tentative automatique par version** (`update_tried` dans `config.json`) : si l'autorisation est refusée ou l'installation échoue, MyCMS démarre normalement au lancement suivant, au lieu de relancer l'installeur à chaque fois. Le bouton reste disponible. Un téléchargement raté n'est pas compté.
  - Rien de tout ça depuis les sources (`sys.frozen` absent) : il n'y a pas d'exe à remplacer.
  - Pendant le téléchargement au démarrage, rien n'est affiché (pas de console) : quelques secondes avant la barre de l'installeur.
- **Avertissement WiX ICE61 supprimé** (`SuppressIces` dans `MyCMS.wixproj`) : il découle de `AllowSameVersionUpgrades`, voulu pour réinstaller la même version par-dessus elle-même.
- La 2.2.5 (simple changement de CI) a été fusionnée sans tag : la 2.3.0 la contient. Dépôt GitHub protégé : `main` sans force-push ni suppression, test `tests` exigé pour fusionner ; tags `v*` impossibles à supprimer ou déplacer (ruleset « Tags de version ») ; alertes Dependabot et détection de secrets actives.

## Changements de la v2.3.1

- **Gestion des branches du site** : carte « Branches », en bas de l'onglet Git car rarement utile (`tabs/git-branches.html`, `git/branches.js`), `publishing/git/branches.py`, `api/branches.py`.
  - `GET /api/git/branches` : branches de cet ordinateur et de GitHub (dernier état connu), actuelle et **publiée**. `?fetch=1` demande d'abord la liste à GitHub (`fetch --prune`).
  - Branche publiée : la branche par défaut de GitHub (`origin/HEAD`), sinon `main` ou `master`. C'est celle du site en ligne.
  - `POST /api/git/branches` avec `action` et `name` :
    - `create` : à partir de la branche actuelle, qui devient la branche actuelle. Les modifications non commitées la suivent. Nom vérifié par `git check-ref-format --branch`. Elle n'existe sur GitHub qu'après le premier push (`set_upstream`, déjà géré par le push) ;
    - `switch` : refusé s'il reste des modifications non commitées. Une branche qui n'est que sur GitHub est récupérée et suivie ;
    - `merge` : dans la branche actuelle, avec un commit de fusion (`--no-ff`). En cas de conflit, `merge --abort` : rien n'est changé (409, `conflict`). Il reste à faire un push ;
    - `delete` : ni la branche actuelle ni la publiée. Sur cet ordinateur, et avec `remote` (case « aussi sur GitHub ») sur GitHub aussi (`push origin --delete`). Une branche qui n'est que sur GitHub exige `remote`.
    - Avant de supprimer, MyCMS vérifie lui-même que ses commits restent dans une branche gardée : l'actuelle, la publiée, ou sa copie sur GitHub si elle n'est pas supprimée. Git (`branch -d`) se contente de la copie sur GitHub, même quand on la supprime aussi. Sinon : 409 (`unmerged`), l'interface demande confirmation, puis renvoie `force`.
  - Interface : changer ou fusionner exige un éditeur sans modification non sauvegardée. Après un changement, la liste des pages et la page ouverte sont rechargées.
  - Sur une autre branche que la publiée, la carte indique que les push ne changent pas le site, et le suivi de la mise en ligne n'est pas lancé après un push (`state.branch`).
  - Non changé : les marqueurs « pas encore publié » comparent toujours à la branche distante de la branche actuelle, et « Publier sur le site et quitter » envoie la branche actuelle.

## Tests

**Lancer `scripts\run_tests.bat` avant chaque commit.** Il installe ce qui manque, puis lance les deux suites. GitHub Actions (`tests.yml`) les relance à chaque push, sous Windows. Ses arguments sont passés à pytest (`run_tests.bat -q`, `run_tests.bat -k editor`).

- **Python** : `python -m pytest`, depuis la racine (`pytest.ini`). Il dépend de `cms/requirements-dev.txt`.
  - `cms/tests/` contient un dossier par paquet : `core/`, `content/`, `publishing/` et `desktop/` (dont `wsgi.py` et `server.py`, avec un vrai serveur Waitress).
  - `api/` contient les tests fonctionnels de chaque route, avec le client de test Flask.
  - `test_project_rules.py` vérifie les règles de ce fichier : 200 lignes, pas de `global`, versions identiques, `hiddenimports` de `mycms.spec`, dépendances de `run.bat`, CSS recompilé.
- **Site de test** : `site_builder.py` écrit en CRLF des pages qui reprennent les cas du vrai site (options de liste déroulante, sommaire, éléments imbriqués, iframe, gras du CSS, page `noindex`, page exclue par le robots.txt).
  - Fixtures de `conftest.py` : `site`, `git_site` (dépôt avec un remote bare local), `client` (administrateur connecté) et `site_client`.
- **Isolation, automatique pour chaque test** :
  - `USERPROFILE` et `HOME` temporaires ;
  - `GIT_CONFIG_GLOBAL` temporaire et `GIT_CONFIG_NOSYSTEM`, car `_ensure_git_config` écrit dans la config Git **globale** ;
  - `show_error` remplacé, pour qu'aucune boîte de message ne s'ouvre.
  - Garder cette isolation dans tout test qui lance Git ou le serveur.
- **Interface** : `cd cms/web && npm test` (`node:test` et jsdom, devDependency).
  - `tests/setup-dom.mjs`, à importer en premier, met le DOM de jsdom à la place de celui du navigateur.
  - Fichiers testés : éditeur enrichi, marqueurs, catégories et recherche, utilitaires et fenêtre Quitter. `modules.test.mjs` charge tous les modules et vérifie les 200 lignes, `window` et les `init…()` appelées par `main.js`.
- **Aller-retour complet** (`cms/tests/test_roundtrip.py`) : chaque page passe par l'API, par les vraies fonctions `buildRichEditor` et `serializeRich` (via `cms/web/tests/roundtrip-cli.mjs`), puis par la sauvegarde. Le fichier doit rester identique à l'octet près.
  - Avec `set MYCMS_SITE=<chemin du vrai site>`, le test tourne aussi sur une **copie** du vrai site, dans un dossier temporaire.
- Non couverts automatiquement : la vraie fenêtre « Choisir un dossier », la vraie icône de notification et le rendu dans un navigateur. Pour eux, voir ci-dessous.
- **Bout en bout dans Chrome** avec `puppeteer-core` (pas dans le dépôt).
  - Chrome se trouve dans `C:\Program Files\Google\Chrome\Application\chrome.exe`.
  - Lancer le serveur avec `USERPROFILE` pointant vers un dossier temporaire, pour isoler la config et les identifiants. Seulement pour le serveur : Chrome ne démarre pas avec ce profil.
  - Arrêter le serveur de test par son PID : `POST /api/quit` exige une session ouverte.
  - Se connecter avec `POST /api/auth/setup` (premier lancement), sinon `POST /api/auth/login`.
  - Attention : après une sauvegarde, l'éditeur se recharge. Attendre la fin du rechargement avant d'agir dessus.

## Conventions Git

- **Petits commits ciblés**, un par fonctionnalité ou correctif, dans l'ordre des dépendances. Jamais un gros commit unique.
- Messages en anglais, préfixés `[ADD]`, `[FIX]`, `[UPDATE]` ou `[DEL]`.
- Ne commiter et ne pousser que sur demande.
