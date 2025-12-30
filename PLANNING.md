# Planification Migration Python → C++ (6 semaines)

## Timeline Globale
- **Maintenant** (30 déc 2025) : Planification architecture ✅
- **Janvier** : Finalize Python, documentation
- **Février-Juin 2026** : Développement C++ (4,5 mois)

## Phase 1 : Setup & Infra (Semaines 1-2)
**Durée** : 2 semaines = ~60-80 heures

### Tâches
- [ ] Installer Qt Creator 6.5+
- [ ] Configurer vcpkg + récupérer dépendances
- [ ] Test build du template
- [ ] Setup Git repo C++
- [ ] Documentationion architecture détaillée
- [ ] Créer fichiers de test (Criterion)

**Livrables** : Build fonctionnel, window Qt vide

---

## Phase 2 : Git Manager (Semaines 3-5)
**Durée** : 3 semaines = ~90-120 heures

### Tâches
- [ ] Implement libgit2 wrapper (init, open repo)
- [ ] verifyRepo() avec gestion erreurs
- [ ] pull() complet (fetch + pull)
- [ ] push() complet (add + commit + push)
- [ ] getStatus() avec output formaté
- [ ] addUntracked() (git add .)
- [ ] Error handling + logging
- [ ] Unit tests (Criterion)

**Livrables** : GitManager 100% fonctionnel, testé

---

## Phase 3 : UI Git Tab (Semaines 4-5)
**Durée** : 2 semaines = ~60-80 heures (overlap avec phase 2)

### Tâches
- [ ] UI Layout (path input, buttons, status display)
- [ ] File dialog pour browse repo
- [ ] Signal/slots pour chaque action
- [ ] Threading (QThread pour Git ops)
- [ ] Status display (textbox)
- [ ] Error messages (QMessageBox)
- [ ] Dark theme stylesheet

**Livrables** : Git Tab complètement fonctionnelle

---

## Phase 4 : HTML Manager (Semaines 6-8)
**Durée** : 3 semaines = ~90-120 heures

### Tâches
- [ ] Implement pugixml wrapper
- [ ] readFile() et writeFile()
- [ ] extractEditableElements() (parser class='editable')
- [ ] Gestion des iframe (src attribute)
- [ ] Prettify output HTML
- [ ] Error handling
- [ ] Unit tests (Criterion)
- [ ] Intégration logger

**Livrables** : HTMLManager 100% fonctionnel, testé

---

## Phase 5 : UI Editor Tab (Semaines 9-11)
**Durée** : 3 semaines = ~90-120 heures

### Tâches
- [ ] File selector combobox
- [ ] Scrollable area pour éléments éditables
- [ ] TextEdit widgets pour chaque élément
- [ ] Display element info (tag, id, index)
- [ ] Save() avec HTMLManager
- [ ] Reload() et refresh files
- [ ] Threading pour file I/O
- [ ] Styling (dark theme)

**Livrables** : Editor Tab fonctionnelle, UX fluide

---

## Phase 6 : ConfigManager & Settings (Semaines 12-14)
**Durée** : 3 semaines = ~90-120 heures

### Tâches
- [ ] Implement ConfigManager (JSON)
- [ ] Default config creation
- [ ] Save/Load config
- [ ] Settings Tab UI
- [ ] Repo path input + validation
- [ ] Auto-pull checkbox
- [ ] Auto-refresh checkbox
- [ ] Save/Reset buttons
- [ ] Persistence au démarrage

**Livrables** : Configuration système complète

---

## Phase 7 : Python Builder (Semaines 13-14)
**Durée** : 2 semaines = ~60-80 heures (peut être parallèle)

### Tâches
- [ ] Implement PythonBuilder (QProcess)
- [ ] Launcher PyInstaller avec arguments
- [ ] Output capture (stdout/stderr)
- [ ] Progress reporting
- [ ] Error handling
- [ ] Logs display
- [ ] Tests sur vraie build Python

**Livrables** : Python builder intégré

---

## Phase 8 : Intégration & Tests (Semaines 15-17)
**Durée** : 3 semaines = ~90-120 heures

### Tâches
- [ ] Full workflow testing (git pull → edit → save → push)
- [ ] Error scenarios (corrupt repo, missing files, etc.)
- [ ] Performance profiling
- [ ] Memory leaks check (valgrind)
- [ ] Qt stylesheet final (dark mode)
- [ ] Keyboard shortcuts
- [ ] Undo/redo (optionnel)
- [ ] Auto-save (optionnel)

**Livrables** : MVP complètement testée

---

## Phase 9 : Polish & Release (Semaines 18-19)
**Durée** : 2 semaines = ~60-80 heures

### Tâches
- [ ] Build release (optimisations -O3)
- [ ] Packaging Windows (.exe installer ou portable)
- [ ] Icon/branding final
- [ ] Documentation utilisateur
- [ ] Changelog
- [ ] Version bump (1.0.0)
- [ ] Release notes
- [ ] Backup Python pour fallback

**Livrables** : MyCMS C++ v1.0 released 🎉

---

## Priorités en Cas de Retard

Si derrière le schedule :
1. **Must-have** : Git ops + Editor basic
2. **Nice-to-have** : Python builder, dark theme polish
3. **V1.1** : Sitemap, advanced logging, preview server

## Points de Contrôle (Checkpoints)

- **Week 2** : Qt template compiling ✅
- **Week 5** : GitManager demo (pull/push/status) 
- **Week 8** : Editor loading files
- **Week 11** : Full edit + save workflow
- **Week 14** : Config + Python builder
- **Week 17** : Full integration tests passing
- **Week 19** : Release ready 🚀

---

## Ressources Développement

- Qt 6 Docs : https://doc.qt.io/qt-6/
- libgit2 : https://libgit2.org/
- pugixml : https://pugixml.org/
- nlohmann/json : https://github.com/nlohmann/json
- Criterion : https://criterion.readthedocs.io/

---

Bon coding en février ! 🎯
