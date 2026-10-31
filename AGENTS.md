# MyCMS : notes pour les agents

À lire en début de conversation. À tenir à jour quand l'architecture, les commandes ou les règles changent.

## Le projet

CMS local qui permet de modifier les textes d'un site statique (HTML hébergé sur GitHub / GitHub Pages) sans toucher au code. L'utilisateur final n'est pas technique : c'est le personnel du site de l'auto-école Rout'Art. L'interface est web (Flask + Tailwind), servie en local, et distribuée sous Windows en `.exe` et en `.msi`.

- Langue : interface, messages, commentaires et docstrings en **français**. Noms de variables et de fonctions en anglais.
- Branche de travail : `web_v2`. Version courante : 2.1.6 (la 2.0.9 a été sautée).
- Site de référence pour les tests : `C:\Users\jbgos\Documents\Tek\Rout'Art` (dépôt `autoecoleroutart/autoecoleroutart.github.io`). Il est en CRLF, compte 17 pages, et `page/formations.html` contient 229 éléments éditables.
  - **Ne jamais modifier ce dossier pendant les tests.** Travailler sur un clone, dans un dossier temporaire.
  - **Tests de publication** : seulement sur la branche `test_for_cms`, prévue pour ça. Cloner cette branche seule (`git clone --single-branch -b test_for_cms …`) et fixer la cible du push (`git config remote.origin.push refs/heads/test_for_cms:refs/heads/test_for_cms`). Jamais de push sur `main`, qui est le site en ligne.
  - Le push passe par SSH : lancer le serveur de test avec `USERPROFILE` temporaire mais le vrai `HOME`, sinon la clé SSH n'est pas trouvée.

## Arborescence

Un dossier par fonctionnalité, des fichiers de **200 lignes au plus**, et **pas de variable globale** (voir « Règles »).

- `cms/web/server.py` : point d'entrée. `prepare_environment()` règle les chemins et le Git portable, `main()` gère l'instance unique, l'icône et le lancement. Options `--port`, `--no-browser` et `--no-tray`.
- `cms/web/api/` : l'application Flask.
  - `create_app()` (`__init__.py`) crée l'application et enregistre un blueprint par domaine : `auth` (connexion exigée avant chaque requête, `before_app_request`), `users` (gestion des comptes, administrateurs seulement), `pages`, `settings` (configuration, logs, choix d'un dossier), `repository` (Git), `publish` (vérification, mise en ligne, reprise de la version en ligne), `editor`, `structure` (dupliquer, supprimer), `media` (images), `site` (sitemap, prévisualisation) et `shutdown` (Quitter).
  - `services.py` : la classe `Services` regroupe les gestionnaires et l'état du processus (`boot_id`, prévisualisation, icône). Elle est rangée dans `app.extensions["mycms"]`, et les routes l'obtiennent avec `services()`.
- `cms/web/templates/` : modèles Jinja.
  - `index.html` inclut `tabs/*.html` (un onglet par fichier ; `settings-users.html` est inclus par `settings.html`) et `dialogs/*.html` (guide, Quitter).
  - `login.html` : la connexion.
- `cms/web/static/` :
  - `scripts/` : modules ES, sans framework. `main.js` (l'interface) et `login.js` (la connexion) sont les points d'entrée.
    - `core/` : `dom.js` (`$`, `api`, `toast`…), `state.js` (état partagé) et `tabs.js`.
    - `editor/` : `editor.js` (ouverture, sauvegarde), `cards.js`, `input.js`, `rich-editor.js` (`buildRichEditor`, `serializeRich`), `markers.js`, `search.js`, `categories.js` (filtres par catégorie), `structure.js` (actions des cartes), `image-field.js` (carte d'une image) et `format-bar.js`.
    - `preview/` : `pane.js` et `pane-code.js` (aperçu de l'éditeur), `preview.js` (onglet), `preview-helper.js` (injecté dans les pages du site servies par la prévisualisation).
    - `git/` : `git.js`, `publish-checks.js` (vérification, mise en ligne, conflit), `history.js` et `history-details.js` (historique et détail d'une modification) et `browse.js` (« Parcourir… »).
    - `quit/` : `quit.js` et `quit-content.js`.
    - `settings/` : `settings.js`, `account.js` (« Mon compte »), `users.js` (compte connecté, carte Utilisateurs), `update.js` (nouvelle version), `header.js` (guide, déconnexion) et `logs.js`.
  - `style.css` : généré par Tailwind, ne pas l'éditer à la main.
  - `highlight.css` : surlignage de la recherche, hors Tailwind.
- `cms/web/src/` : sources Tailwind v4. `input.css` importe `theme.css` (couleurs) et `components/*.css` (une couche `@layer components` par fichier).
- `cms/source/` : le code métier, importé par paquet (`from content.html_tree import parse`).
  - `core/` : `data_dir.py` (dossier `~/.mycms`, caché, et verrouillage de fichiers ; l'ancien `~/.rout_art_cms` est renommé au premier lancement), `config_manager.py` (`config.json`), `auth_manager.py` (comptes ; empreinte par défaut de Werkzeug : scrypt depuis la 3.0, pbkdf2 avant), `auth_file.py` (`auth.json` verrouillé, reprise de l'ancien format), `updates.py` (nouvelle version sur GitHub) et `logger.py`.
  - `version.py` : `VERSION`, la version de MyCMS.
  - `content/` :
    - `html_tree.py` : arbre HTML avec les positions exactes dans le fichier ;
    - `hybrid_saver.py` et `node_diff.py` : la sauvegarde hybride ;
    - `html_manager.py` : extraction des `.editable`, `apply_editable_html`, extraits de code ;
    - `css_weights.py` : gras d'après le CSS du site (`<link>`, `@import`, variables, spécificité, héritage) ;
    - `categories.py` : catégorie de chaque élément éditable, déduite de la structure de la page ;
    - `structure.py` : dupliquer ou supprimer un élément de liste ou une ligne de tableau ;
    - `published.py` : version publiée de chaque élément, associée par le contenu ;
    - `changes.py` : changements d'une page entre deux versions, élément par élément (historique) ;
    - `page_finder.py` : détection des pages.
  - `publishing/` :
    - `git_manager.py` : clone, `pending()`, `unpublished_pages()`, version publiée ; le pull et le push sont dans `git_sync.py` (conflits) ;
    - `checks.py` : vérification avant publication ; `online.py` : suivi de la mise en ligne ; `history.py` et `commit_details.py` : historique lisible et détail d'une modification ;
    - `git_status.py` : rapport de l'onglet Git ;
    - `sitemap_generator.py`, `sitemap_files.py`, `robots.py` et `site_url.py` : sitemap, robots.txt, URL du site.
  - `desktop/` : `server_manager.py` (prévisualisation, `ThreadingHTTPServer` sur 127.0.0.1), `folder_picker.py` (classe `FolderPicker`), `tray.py` (icône de notification) et `startup.py` (instance unique, port libre, `show_error`).
- `cms/installer/` : compilation. `build_exe.py` et `mycms.spec` (PyInstaller), `build_msi.py`, `MyCMS.wixproj` et `Package.wxs` (WiX, avec Git portable MinGit).
  - Un nouveau module Python doit être ajouté aux `hiddenimports` de `mycms.spec`, et un nouveau dossier de l'interface à ses `datas`.
- `cms/icon/logo.ico` : l'icône de l'exe, de l'installeur et de la zone de notification.
- `run.bat` : lancement depuis les sources, sur le port 5050.
- `.github/workflows/` : `tests.yml` (tests à chaque push) et `release.yml` (exe et `.msi` joints à une release, sur un tag `v<version>`).
- `cms/tests/` (pytest) et `cms/web/tests/` (`node:test`) : les tests, lancés par `run_tests.bat` (voir « Tests »).

## Commandes

- Tests : `run_tests.bat`, ou `python -m pytest` et `cd cms/web && npm test`.
- Lancer : `python cms/web/server.py`, ou `python cms/web/server.py --port 5060 --no-browser --no-tray`.
- Dépendances : `cms/requirements.txt` pour l'exécution, `cms/requirements-build.txt` (ajoute PyInstaller) pour compiler, `cms/requirements-dev.txt` (ajoute pytest) pour les tests.
- CSS, après toute modification de `src/` ou ajout de classes Tailwind dans les modèles ou les scripts : `cd cms/web && npm run build:css`. `style.css` est versionné, pour que l'application tourne sans Node.
- Exécutable : `python cms/installer/build_exe.py`, qui produit `dist/MyCMS.exe`.
- Installeur : `compile_msi.bat`, qui produit `dist/MyCMS-<version>.msi`. Nécessite le SDK .NET.
- Version : la changer **à la fois** dans `cms/web/package.json` (lue par le `.msi`) et dans `cms/source/version.py` (lue par l'application). Un test vérifie qu'elles sont identiques.
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

- **Dossier de données `~/.mycms`** : remplace `~/.rout_art_cms`, renommé automatiquement (copié si le renommage échoue). Il reçoit l'attribut « caché » de Windows, puisque le point au début du nom ne cache rien sous Windows.
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
  - Le serveur calcule les catégories (`content/categories.py`) et le chargement d'une page renvoie `category` pour chaque élément. Rien n'est écrit dans le site.
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
  - **＋ Dupliquer** et **✕ Supprimer** : pour un élément de liste ou une ligne de tableau (`content/structure.py`, `POST /api/structure/<page>` avec `hash`, `action` et `index`).
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
- **Version publiée associée par le contenu (corrigé)** (`content/published.py`) : elle était associée par la position. Après un ajout ou une suppression, tous les éléments suivants recevaient de faux marqueurs, et « Version en ligne » aurait remis le texte d'un autre élément.
  - Maintenant : alignement `difflib` sur (balise, contenu). Dans un bloc modifié, les éléments les plus semblables sont associés, dans l'ordre (programmation dynamique, bornée à 2 500 comparaisons). Une copie fraîchement ajoutée est « nouvelle » (+).

## Changements de la v2.1.3

- **Vérification avant publication** (`publishing/checks.py`, `GET /api/checks`). Avant chaque push (onglet Git et fenêtre Quitter), les pages pas encore publiées sont vérifiées. S'il y a des problèmes, ils s'affichent et l'utilisateur choisit de publier quand même ou non. Le bouton « Vérifier le site » (`?scope=all`) vérifie tout le site.
  - Vérifié : liens et images vers des fichiers absents (adresses résolues comme le navigateur, sans remonter au-dessus de la racine), ancres `#…` introuvables, `mailto:` et `tel:` mal formés, éléments éditables vides, `src` vide.
  - Les adresses externes ne sont pas vérifiées : pas de réseau.
  - Le site de référence a 2 vrais liens cassés dans `page/financement.html` (lignes 352 et 358) : `../files/…pdf` au lieu de `../files/voiture/…pdf`.
- **Suivi de la mise en ligne** (`publishing/online.py`, `GET /api/online?page=…`). Le push renvoie `pages`, les pages HTML envoyées. L'onglet Git interroge le site en ligne toutes les 10 s, pendant 10 min au plus, jusqu'à ce qu'il renvoie le même contenu que les fichiers locaux, fins de ligne mises à part.
- **Conflits** (`publishing/git_sync.py`) : le repository n'est jamais laissé à moitié fusionné.
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
- **Historique lisible** dans l'onglet Git (`publishing/history.py`, `GET /api/git/history`, `git/history.js`). Il montre les 20 derniers commits : « Marie a modifié page/tarifs.html (et 1 autre fichier) », la date en français, la première ligne du message, et l'état « Publié » ou « Pas encore publié » (commit présent ou non sur la branche distante).
  - Il est rafraîchi avec le statut, après chaque action Git.
- Tests : GitPython lit l'identité du poste dans `~/.gitconfig` (pas dans `GIT_CONFIG_GLOBAL`). `conftest.py` y écrit donc la même identité de test.

## Changements de la v2.1.5

- **GitHub Actions** (`.github/workflows/`) :
  - `tests.yml` : `pytest -v` et `npm test` à chaque push et pull request, sous `windows-latest` (verrou NTFS, CRLF).
  - `release.yml` : sur un tag `v*`, vérifie que le tag correspond à `package.json`, lance les tests, compile `MyCMS.exe` puis `MyCMS-<version>.msi`, et les joint à une release GitHub. `build_msi.py` vide `dist/`, d'où l'exe mis de côté dans `release/`.
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

- **Détail d'une modification de l'historique** : un clic sur une ligne de l'historique de l'onglet Git la déplie (`git/history-details.js`, `GET /api/git/commit/<hash>`, `publishing/commit_details.py`, `content/changes.py`). Le détail est chargé une seule fois.
  - Pour chaque page modifiée, les éléments éditables sont associés entre les deux versions comme pour les marqueurs (`published.align`). Chaque changement est classé « Modifié », « Mise en forme » (même texte : gras, lien…), « Ajouté » ou « Supprimé », avec sa catégorie.
  - Les mots supprimés sont barrés en rouge, les mots ajoutés surlignés en vert (`word_diff` : `difflib` sur les mots, chacun suivi de ses espaces, pour faire des blocs).
  - Une page dont aucun texte modifiable n'a changé l'indique (modification du code). Le diff Git reste dans un volet repliable « Voir le code modifié » (300 lignes au plus), puis viennent les autres fichiers.
  - Au plus 100 changements par page. Un premier commit, sans parent, montre toute la page comme ajoutée.
  - Un hash au bon format mais inconnu fait lever `BadName` par gitdb : la réponse est « Modification introuvable » (404).
- **Statut du repository** : la carte passe avant l'historique, et sa section « Historique récent » est retirée.
- **« Vérifier le site »** : les problèmes s'affichent dans un encadré rouge sous les boutons (`#check-results`, `.check-results.error`), avec la page, la ligne et une phrase sur quoi faire. Le message en bas de l'écran est rouge. Sans problème, l'encadré est vert. Avant, la liste allait dans le statut, plus bas, et le message était vert.
- **« ↺ Version en ligne »** : le message dit « sauvegardez » seulement s'il reste quelque chose à sauvegarder. Si le fichier enregistré était déjà la version en ligne, il dit « Texte revenu à la version en ligne : rien à sauvegarder ».

## Tests

**Lancer `run_tests.bat` avant chaque commit.** Il installe ce qui manque, puis lance les deux suites. GitHub Actions (`tests.yml`) les relance à chaque push, sous Windows. Ses arguments sont passés à pytest (`run_tests.bat -q`, `run_tests.bat -k editor`).

- **Python** : `python -m pytest`, depuis la racine (`pytest.ini`). Il dépend de `cms/requirements-dev.txt`.
  - `cms/tests/` contient un dossier par paquet : `core/`, `content/`, `publishing/` et `desktop/` (dont `server.py`).
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
