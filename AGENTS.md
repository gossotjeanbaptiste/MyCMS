# MyCMS : notes pour les agents

À lire en début de conversation. À tenir à jour quand l'architecture, les commandes ou les règles changent.

## Le projet

CMS local qui permet de modifier les textes d'un site statique (HTML hébergé sur GitHub / GitHub Pages) sans toucher au code. L'utilisateur final n'est pas technique : c'est le personnel du site de l'auto-école Rout'Art. L'interface est web (Flask + Tailwind), servie en local, et distribuée sous Windows en `.exe` et en `.msi`.

- Langue : interface, messages, commentaires et docstrings en **français**. Noms de variables et de fonctions en anglais.
- Branche de travail : `web_v2`. Version courante : 2.0.3.
- Site de référence pour les tests : `C:\Users\jbgos\Documents\Tek\Rout'Art`. Il est en CRLF, compte 17 pages, et `page/formations.html` contient 229 éléments éditables.
  - **Ne jamais modifier ce dépôt ni pousser dessus pendant les tests.** Travailler sur une copie.
  - La copie hérite de l'URL GitHub réelle : avant tout test de publication, faire pointer son `origin` (fetch **et** push) vers un dépôt bare local.

## Arborescence

- `cms/web/server.py` : serveur Flask. Il fournit l'API JSON et les pages, vérifie la connexion avant chaque requête (`before_request`), et accepte les options `--port`, `--no-browser` et `--no-tray`.
- `cms/web/static/` :
  - `index.html` et `app.js` : toute l'interface, en JS sans framework ;
  - `login.html` et `login.js` : la connexion ;
  - `preview-helper.js` : injecté dans les pages servies par la prévisualisation, pour l'aperçu en direct ;
  - `style.css` : généré par Tailwind, ne pas l'éditer à la main ;
  - `highlight.css` : surlignage de la recherche, hors Tailwind.
- `cms/web/src/input.css` : source Tailwind v4. Les composants sont dans `@layer components`.
- `cms/source/` : le code métier.
  - `html_source.py` : arbre HTML avec les positions exactes dans le fichier, et `HybridSaver` pour la sauvegarde hybride.
  - `html_manager.py` : extraction des éléments `.editable`, `apply_editable_html` (utilisé par le web), `apply_editable_texts` (ancienne app CTk), extraits de code.
  - `css_weights.py` : détermine quels éléments sont en gras d'après le CSS du site (`<link>`, `@import`, variables CSS, spécificité, héritage).
  - `page_finder.py` : détection automatique des pages.
  - `sitemap_generator.py` : création du sitemap, déplacement à la racine, détection de l'URL du site.
  - `git_manager.py` : pull, push, clone. `pending()` liste ce qui n'est pas encore publié.
  - `server_manager.py` : serveur de prévisualisation (`ThreadingHTTPServer` sur 127.0.0.1).
  - `data_dir.py` : dossier de données `~/.mycms` (caché ; l'ancien `~/.rout_art_cms` est renommé au premier lancement), et verrouillage de fichiers.
  - `config_manager.py` : configuration dans `~/.mycms/config.json`.
  - `auth_manager.py` : identifiants dans `~/.mycms/auth.json`, empreinte scrypt. Le fichier est verrouillé contre la modification.
  - `logger.py` : journal de l'application.
  - `mycms.py` : ancienne interface CustomTkinter. Elle est conservée mais n'est plus compilée.
  - Compilation : `build_exe.py` et `mycms.spec` (PyInstaller) ; `build_msi.py` et `cms/installer/` (WiX, avec Git portable MinGit embarqué).
- `app.py` et `run.bat` : lancement depuis les sources, sur le port 5050.

## Commandes

- Lancer : `python app.py`, ou `python cms/web/server.py --port 5060 --no-browser --no-tray`.
- CSS, après toute modification de `input.css` ou ajout de classes Tailwind dans le HTML ou le JS : `cd cms/web && npm run build:css`. `style.css` est versionné, pour que l'application tourne sans Node.
- Exécutable : `python cms/source/build_exe.py`, qui produit `dist/MyCMS.exe`.
- Installeur : `compile_msi.bat`, qui produit `dist/MyCMS-<version>.msi`. Nécessite le SDK .NET.
- Version : la changer **à la fois** dans `cms/web/package.json` (lue par le `.msi`) et dans `cms/source/__init__.py`.

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
- **Erreurs visibles sans console** : `_show_error` affiche une boîte de message Windows (`MessageBoxW`), par exemple si le port est pris par un autre programme ou si le serveur s'arrête sur une erreur. Dans les tests, remplacer `server._show_error`, sinon la boîte bloque le test et s'affiche sur l'écran de l'utilisateur.

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

## Tests

Il n'y a pas de suite de tests dans le dépôt. Les vérifications faites jusqu'ici, à refaire selon ce qui est touché :

- **Tests unitaires Python** de `HybridSaver`, avec des entrées qui imitent le navigateur : `<b>`, attributs réécrits, fins de ligne `\n`, marqueurs de verrou.
- **Aller-retour dans jsdom** sur toutes les pages du site : on extrait les vraies fonctions `buildRichEditor` et `serializeRich` d'`app.js`, et on vérifie que le fichier reste identique.
- **Bout en bout dans Chrome** avec `puppeteer-core`.
  - Chrome se trouve dans `C:\Program Files\Google\Chrome\Application\chrome.exe`.
  - Lancer le serveur avec `USERPROFILE` pointant vers un dossier temporaire, pour isoler la config et les identifiants.
  - Se connecter avec `POST /api/auth/setup` (premier lancement), sinon `POST /api/auth/login`.
  - Attention : après une sauvegarde, l'éditeur se recharge. Attendre la fin du rechargement avant d'agir dessus.

## Conventions Git

- **Petits commits ciblés**, un par fonctionnalité ou correctif, dans l'ordre des dépendances. Jamais un gros commit unique.
- Messages en anglais, préfixés `[ADD]`, `[FIX]`, `[UPDATE]` ou `[DEL]`.
- Ne commiter et ne pousser que sur demande.
