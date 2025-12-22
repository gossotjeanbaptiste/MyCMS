# 🚗 ROUT'ART CMS - Documentation Complète

> Application de gestion de contenu pour le site Rout'Art  
> Édition HTML • Git Sync • Prévisualisation • Interface GUI  
> ✨ Compilable en .exe pour Windows 11

---

## 📚 Table des Matières

1. [🚀 Démarrage Rapide](#démarrage-rapide)
2. [📁 Structure du Projet](#structure-du-projet)
3. [🎮 Guide d'Utilisation](#guide-dutilisation)
4. [⚙️ Installation Complète](#installation-complète)
5. [🔨 Compilation en .exe](#compilation-en-exe)
6. [🏗️ Architecture Technique](#architecture-technique)
7. [🐛 Dépannage](#dépannage)

---

## 🚀 Démarrage Rapide

### Option 1: Exécutable Windows (Recommandé)
```bash
Double-cliquez: rout_art_cms.exe
```

### Option 2: Python directement
```bash
cd cms/source
python rout_art_cms.py
```

### Option 3: Depuis le répertoire cms
```bash
cd cms
python source/rout_art_cms.py
```

---

## 📁 Structure du Projet

```
Rout-Art/
│
└── cms/                                ← 📁 Dossier CMS (tout le système)
    │
    ├── 📄 CMS.md                       (Vue d'ensemble du CMS)
    ├── 📄 DOCUMENTATION.md             (Documentation complète - VOUS ÊTES ICI)
    ├── 📄 README_CMS.md                (Guide de démarrage rapide)
    ├── 📄 SITEMAP_AUTOMATION.md        (Documentation générateur sitemap)
    │
    ├── 🎨 icon/                        (Icônes et logos)
    │   ├── logo-routart.png            (Logo PNG moderne)
    │   └── logo_routart.ico            (Logo ICO pour .exe)
    │
    ├── 📦 requirements.txt             (Dépendances Python)
    │
    └── 🔧 source/                      (Code source)
        ├── __init__.py                 (Marque Python package)
        │
        ├── 🎯 rout_art_cms.py          (Application principale - GUI)
        │
        ├── 🏗️ Modules Métier:
        │   ├── git_manager.py          (Gestion Git: pull/push/status)
        │   ├── html_manager.py         (Édition HTML: lecture/écriture)
        │   ├── server_manager.py       (Serveur HTTP local + validation)
        │   ├── config_manager.py       (Config: cache/validations/hooks)
        │   ├── logger.py               (Journalisation centralisée)
        │   └── sitemap_generator.py    (Génération automatique sitemap)
        │
        └── 🔨 Compilation & Utilitaires:
            ├── build_exe.py            (Compilation PyInstaller)
            ├── clean_config.py         (Nettoyage configuration)
            ├── config_manager_example.py (Exemples d'utilisation)
            └── rout_art_cms.spec       (Configuration compilation)
```

### Fichiers Clés

| Fichier                | Location  | Description                                             |
| ---------------------- | --------- | ------------------------------------------------------- |
| `rout_art_cms.py`      | `source/` | Application GUI principale - CustomTkinter              |
| `config_manager.py`    | `source/` | Configuration persistante (cache + validations + hooks) |
| `git_manager.py`       | `source/` | Opérations Git (pull/push)                              |
| `html_manager.py`      | `source/` | Édition fichiers HTML                                   |
| `server_manager.py`    | `source/` | Serveur local avec validation de port                   |
| `logger.py`            | `source/` | Logs centralisés (fichier + mémoire)                    |
| `sitemap_generator.py` | `source/` | Génération automatique de sitemap                       |
| `build_exe.py`         | `source/` | Compilation en exécutable Windows                       |
| `clean_config.py`      | `source/` | Script de nettoyage de configuration                    |
| `requirements.txt`     | `cms/`    | Toutes les dépendances Python                           |
| `DOCUMENTATION.md`     | `cms/`    | Documentation complète (ceci)                           |
| `README_CMS.md`        | `cms/`    | Quick start guide                                       |
| `CMS.md`               | `cms/`    | Vue d'ensemble générale                                 |

---

## 🎮 Guide d'Utilisation

### Écran Initial

L'application se lance avec une interface à **5 onglets**:

#### 1️⃣ Onglet "Git & Synchronisation"
- **Pull**: Récupérez les modifications du repository
- **Push**: Publiez vos changements
- **Statut**: Vérifiez l'état du repository
- **Message commit**: Rédigez un message pour le push

#### 2️⃣ Onglet "Éditeur Contenu"
- **Sélectionner fichier**: Choisissez un fichier HTML à éditer
- **Prévisualisation**: Voyez le contenu actuel
- **Recherche/Remplace**: Trouvez et modifiez du texte
- **Sauvegarder**: Enregistrez vos modifications

#### 3️⃣ Onglet "Prévisualisation"
- **Démarrer serveur**: Lance un serveur HTTP local
- **Port**: Personnalisez le port (défaut: 8000)
- **Ouvrir navigateur**: Lance la prévisualisation
- **Logs**: Consultez les logs du serveur

**Améliorations Récentes:**
- ✅ **Synchronisation config ↔ UI**: Le port se charge automatiquement depuis la configuration
- ✅ **Mise à jour temps réel**: L'URL se met à jour au fur et à mesure que vous tapez le port
- ✅ **Validation stricte**: Le port doit être entre 1-65535
- ✅ **Fallback automatique**: Port invalide → basculement à 8000
- ✅ **Affichage des erreurs**: Messages clairs si le port est invalide (ex: "⚠️  Port -16500 invalide")
- ✅ **Nettoyage automatique**: Les ports invalides en config sont corrigés au démarrage

#### 4️⃣ Onglet "Paramètres"
- **Chemin repository**: Configurez le dossier Git
- **Auto pull au démarrage**: Synchronisation automatique
- **Auto refresh**: Actualisation automatique
- **Réinitialiser**: Restaure les paramètres par défaut

#### 5️⃣ Onglet "Logs"
- **Historique complet**: Tous les événements
- **Filtrage**: Par niveau ou type
- **Export**: Téléchargez les logs
- **Temps réel**: Mise à jour instantanée

### Flux Typique d'Utilisation

```
1. ⚙️ CONFIGURATION (1ère fois)
   └─ Aller à "Paramètres"
   └─ Entrer le chemin du repository
   └─ Cliquer "Sauvegarder"

2. 🔄 TRAVAIL QUOTIDIEN
   └─ Git: Pull
   └─ Éditeur: Ouvrir et modifier fichier
   └─ Prévisualisation: Vérifier le résultat
   └─ Git: Push avec message
   └─ Logs: Vérifier succès

3. 💾 AVANT DE QUITTER
   └─ Tous les fichiers sont auto-sauvegardés
   └─ Les logs sont archivés
```

---

## ⚙️ Installation Complète

### Prérequis
- Python 3.9+ (ou exécutable .exe fourni)
- Windows 7+ ou WSL
- 200 MB d'espace disque

### Étape 1: Installation des Dépendances

```bash
cd cms
pip install -r requirements.txt
```

Ou si vous préférez directement:
```bash
pip install customtkinter beautifulsoup4 gitpython
```

Cela installe:
- `customtkinter` (GUI moderne)
- `beautifulsoup4` (Édition HTML)
- `gitpython` (Gestion Git)

### Étape 2: Lancer l'Application

```bash
cd cms/source
python rout_art_cms.py
```

---

## 🔨 Compilation en .exe

### Prérequis de Compilation
```bash
pip install pyinstaller
```

### Compiler

```bash
cd cms/source
python build_exe.py
```

**Résultat:**
- Exécutable créé dans `dist/Rout'Art CMS/`
- Nom: `Rout'Art CMS.exe`
- Taille: ~200 MB (inclut Python)
- Aucune dépendance requise

### Tester l'Exécutable

```bash
# Navigez dans le dossier de sortie
cd dist/Rout'Art CMS/

# Lancez l'exe
Rout'Art CMS.exe
```

---

## 🏗️ Architecture Technique

### Modules Principaux

#### `git_manager.py`
Gère toutes les opérations Git:
```python
pull()          # Récupère les modifications
push(message)   # Publie les changements
get_status()    # Affiche l'état du repo
get_history()   # Historique des commits
```

#### `html_manager.py`
Édition et manipulation HTML:
```python
read_file(path)              # Lit un fichier HTML
write_file(path, content)    # Sauvegarde
find_element(selector)       # Localise un élément
replace_element(old, new)    # Remplace du contenu
```

#### `server_manager.py`
Serveur HTTP local pour prévisualisation:
```python
start(port, path)   # Démarre le serveur
stop()              # Arrête le serveur
is_running()        # État du serveur
```

Amélioration récente:
- ✅ **Validation du port**: Vérifie que le port est entre 1-65535
- ✅ **Fallback automatique**: Utilise le port 8000 si invalide
- ✅ **Messages d'erreur clairs**: Affiche quand un port est corrigé

#### `config_manager.py` - Gestion Avancée
Configuration persistante avec **cache**, **validations** et **hooks**:

**Stockage & Chargement:**
```python
load_config()       # Charge depuis ~/.rout_art_cms/config.json
save_config()       # Sauvegarde persistante
```

**Cache en Mémoire:**
```
Avantage: Accès instantané sans lire le fichier à chaque fois
Synchronisation: Automatique lors de chaque modification
Performance: +100x plus rapide pour lectures répétées
```

**Validations Strictes:**
```python
# Schéma de validation appliqué à chaque modification:
- repo_path: string (chemin existant)
- auto_pull: boolean
- auto_refresh: boolean
- default_port: integer (1-65535)
- theme: string (dark ou light)
- window_width: integer (min 400)
- window_height: integer (min 300)

# Exemples:
set_default_port(99999)   # ❌ Erreur: > 65535
set_default_port(8000)    # ✅ Accepté
set_theme("neon")         # ❌ Erreur: not in [dark, light]
set_theme("dark")         # ✅ Accepté
```

**Hooks - Actions Automatiques:**
```python
# Avant modification (before hook)
config.register_hook("theme", "before", callback)

# Après modification (after hook)
config.register_hook("theme", "after", callback)

# Exemple d'utilisation:
def apply_theme(key, old, new):
    print(f"Thème changé: {old} → {new}")
    update_ui_theme(new)  # Déclenche mise à jour UI

config.register_hook("theme", "after", apply_theme)
```

**Auto-nettoyage:**
```
À chaque démarrage:
- Vérifie chaque valeur sauvegardée
- Corrige automatiquement les valeurs invalides
- Affiche des avertissements
- Réenregistre la config nettoyée
```

#### `logger.py`
Centralisation des logs:
```python
log(msg)            # Info
log_error(err)      # Erreur
log_success(msg)    # Succès
get_logs()          # Récupère l'historique
get_recent_logs()   # Derniers N logs
```

### Flux de Données

```
Utilisateur
    ↓
[Interface GUI - CustomTkinter]
    ├─ _create_preview_tab()      (Synchronisation config ↔ UI)
    ├─ _update_preview_url()      (Mise à jour URL en temps réel)
    └─ _start_server()            (Validation + fallback)
    ↓
[Managers - Métier]
    ├─ git_manager (GitPython)
    ├─ html_manager (BeautifulSoup4)
    ├─ server_manager (http.server + validation)
    ├─ config_manager (JSON + cache + validations + hooks)
    └─ logger (File + Memory)
    ↓
[Système de fichiers + Git + HTTP]
```

### Threading

Les opérations longues tournent en thread séparé:
- Git pull/push
- Démarrage serveur
- Lecture de fichiers volumineux

Cela garde l'interface responsive.

---

## 🐛 Dépannage

### "ModuleNotFoundError: No module named..."

**Solution:**
```bash
cd cms
pip install -r requirements.txt
```

### "Repository not found"

1. Vérifiez le chemin dans ⚙️ Paramètres
2. Assurez-vous que c'est un dossier Git valide
3. Cliquez "Sauvegarder"

### Port invalide ou "port must be 0-65535"

**Cause:** La configuration contient un port invalide (par exemple: -16500)

**Solutions:**

1. **Nettoyage automatique** (Recommandé):
```bash
cd cms/source
python clean_config.py
```
Cela:
- Détecte les valeurs invalides
- Les corrige automatiquement
- Sauvegarde la config nettoyée

2. **Réinitialisation manuelle**:
   - Ouvrez ⚙️ Paramètres
   - Cliquez "Réinitialiser"
   - Redémarrez l'application

3. **Suppression du fichier config**:
```bash
# Windows (PowerShell):
Remove-Item $env:USERPROFILE\\.rout_art_cms\\config.json

# Relancez l'app - la config par défaut sera recréée
```

### Serveur HTTP n'apparaît pas

1. Vérifiez que le port n'est pas utilisé
2. Essayez avec un autre port (ex: 8001)
3. Consultez les logs pour plus de détails
4. Si le port était invalide, exécutez: `python cms/source/clean_config.py`

### Les changements Git ne fonctionnent pas

1. Vérifiez la configuration Git: `git config --list`
2. Testez la connexion au repository
3. Vérifiez les permissions fichiers

### L'URL de prévisualisation affiche "⚠️ Port invalide"

Cela signifie que vous avez saisi un port invalide dans le champ.

**Solution:**
- Vérifiez que c'est un nombre entre 1 et 65535
- Appuyez sur "Démarrer Serveur" pour que le port soit corrigé automatiquement
- Le port sera remplacé par 8000

---

## 📋 Checklist de Déploiement

Avant de distribuer l'application:

- [ ] Compiler l'exe: `cd cms/source && python build_exe.py`
- [ ] Tester l'exe sur une machine sans Python
- [ ] Vérifier tous les onglets fonctionnent
- [ ] Tester Git pull/push
- [ ] Tester édition HTML
- [ ] Tester prévisualisation
- [ ] Vérifier logs complets

---

## 📞 Aide & Support

### Fichiers de Logs
- **Localisation**: `~/.rout_art_cms/app.log`
- **Consultez les logs** pour diagnostiquer les problèmes
- **Export**: Utilisez le bouton "Export" dans l'onglet Logs

### Informations de Configuration
- **Stockage**: `~/.rout_art_cms/config.json`
- **Réinitialiser**: Cliquez "Réinitialiser" dans Paramètres

---

## ℹ️ Informations Techniques

| Aspect            | Détail                |
| ----------------- | --------------------- |
| **Langage**       | Python 3.9+           |
| **GUI**           | CustomTkinter 5.0+    |
| **HTML**          | BeautifulSoup4 4.11+  |
| **Git**           | GitPython 3.1+        |
| **Serveur**       | http.server (stdlib)  |
| **Compilation**   | PyInstaller 5.0+      |
| **Taille .exe**   | ~200 MB               |
| **Mémoire**       | 50-150 MB             |
| **Compatibilité** | Windows 7+            |
| **Python**        | 3.9, 3.10, 3.11, 3.12 |

---

## 🔄 Améliorations Récentes (v1.8.0+)

### Configuration Avancée
- **Cache en mémoire**: Lectures 100x plus rapides
- **Validations strictes**: Impossible de sauvegarder des données invalides
- **Hooks automatiques**: Déclenchez des actions lors de modifications
- **Auto-nettoyage**: Les valeurs invalides sont corrigées au démarrage

### Interface Utilisateur
- **Synchronisation config ↔ UI**: Charge automatiquement les paramètres sauvegardés
- **Mise à jour temps réel**: L'URL change au fur et à mesure que vous modifiez le port
- **Fallback intelligent**: Port invalide → basculement automatique à 8000
- **Messages d'erreur clairs**: Affichage des avertissements en cas de problème

### Robustesse
- **Initialisation correcte**: Tous les managers sont prêts avant l'interface
- **Validation du port**: Accepte uniquement 1-65535
- **Gestion des erreurs**: Essayez une valeur par défaut si la saisie est invalide
- **Logs détaillés**: Traçabilité complète des opérations

### Scripts Utilitaires
- **clean_config.py**: Nettoie et corrige la configuration
- **config_manager_example.py**: Exemples d'utilisation des validations et hooks

---

## ✨ Version

**Rout'Art CMS v1.8.0**
- Status: Production Ready ✅
- Dernière mise à jour: 14 décembre 2025
- Auteur: Jean-Baptiste (POGGIO) GOSSOT for Auto-École Rout'Art
- License: MIT

**Nouveautés v1.8.0:**
- ✨ Configuration avec cache, validations et hooks
- ✨ Port server avec fallback automatique
- ✨ Interface synchronized avec la config
- ✨ Nettoyage automatique des données invalides
- ✨ Messages d'erreur améliorés
- ✨ Structure cms/ avec dossier source/ dédié

---

**À bientôt!** 🚀
