# 🚗 Rout'Art CMS v1.0.0

> **Application de Gestion de Contenu pour le site Rout'Art**  
> Édition HTML • Git Sync • Prévisualisation Local • Interface GUI  
> ✨ Compilable en .exe autonome pour Windows 11

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)
[![PyInstaller](https://img.shields.io/badge/Compile-PyInstaller-orange?style=flat-square)](https://pyinstaller.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)]()

---

## 🚀 Démarrage Rapide

### ⚡ 30 secondes pour commencer

```bash
# Option 1 : Exécutable (le plus simple)
Double-cliquez: rout_art_cms.exe

# Option 2 : Avec Python
python setup_dependencies.py
python rout_art_cms.py

# Option 3 : Menu interactif
python launcher.py
```

**✓ C'est tout! L'application se lance.**

---

## 📋 Table des matières

- [🎯 Vue d'ensemble](#-vue-densemble)
- [✨ Fonctionnalités](#-fonctionnalités-principales)
- [📥 Installation](#-installation)
- [🎮 Utilisation](#-utilisation)
- [🔨 Compilation](#-compilation-en-exe)
- [📚 Documentation](#-documentation)
- [🐛 Dépannage](#-dépannage)
- [📞 Support](#-support)

---

## 🎯 Vue d'ensemble

**Rout'Art CMS** est une application desktop complète permettant de gérer le site web de l'auto-école directement depuis une interface graphique intuitive.

**Plus besoin de:**
- ❌ Connaître le code HTML
- ❌ Utiliser la ligne de commande
- ❌ Comprendre Git

**Tout ce que vous pouvez faire:**
- ✅ Éditer les pages du site
- ✅ Synchroniser automatiquement avec GitHub
- ✅ Prévisualiser localement
- ✅ Voir l'historique des modifications

---

## ✨ Fonctionnalités principales

### 🔗 Git & Synchronisation
- **Pull automatique** des derniers changements
- **Push sécurisé** avec messages de commit
- **Statut temps réel** du repository
- **Historique complet** des commits
- Gestion d'erreurs et notifications

### ✏️ Éditeur de Contenu
- **Sélection facile** des fichiers HTML
- **Édition en direct** du contenu
- **Rechercher/Remplacer** intégré
- **Sauvegarde instantanée**
- Reload automatique

### 👁️ Prévisualisation Locale
- **Serveur HTTP intégré**
- Port personnalisable
- **Ouverture directe** dans le navigateur
- Logs du serveur en temps réel
- Parfait pour tester avant de publier

### ⚙️ Configuration Intelligente
- **Sauvegarde automatique** des paramètres
- Pull/Refresh automatiques (optionnel)
- Réinitialisation facile
- Stockage sécurisé

### 📋 Logs Centralisés
- **Historique complet** de toutes les opérations
- **Affichage temps réel**
- Export vers fichier
- Aide au dépannage

---

## 📥 Installation

### Prérequis
- **Windows 11** (ou 10 avec Python 3.9+)
- 500 MB d'espace disque
- 2 GB de RAM minimum

### Option 1: Exécutable (Recommandé)
```bash
# Télécharger: Rout'Art CMS.exe
# Double-cliquez sur le fichier
# ✓ L'application se lance!
```

### Option 2: Depuis Python
```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python rout_art_cms.py
```

### Option 3: Menu Interactif
```bash
python launcher.py
# Sélectionnez l'option depuis le menu
```

---

## 🎮 Utilisation

### Première Utilisation
1. Ouvrir l'application
2. Aller à **⚙️ Paramètres**
3. Entrer le chemin de votre repository Rout'Art
4. Cliquer **Sauvegarder**

### Workflow Typique

```
1. PULL (Récupérer les changements)
   🔗 Git & Synch → ⬇️ Pull

2. ÉDITER (Modifier les pages)
   ✏️ Éditeur → Sélectionner fichier → Modifier → 💾 Sauvegarder

3. PRÉVISUALISER (Voir le résultat)
   👁️ Prévisualisation → ▶️ Démarrer → 🌐 Navigateur

4. PUSH (Publier sur GitHub)
   🔗 Git & Synch → Entrer message → ⬆️ Push
```

### Consultez les Logs
```
📋 Logs → Voir historique des opérations
          → 💾 Exporter si besoin
```

---

## 🔨 Compilation en .exe

Pour créer un exécutable autonome:

```bash
# 1. Installer PyInstaller
pip install pyinstaller

# 2. Compiler (automatique)
python build_exe.py

# Ou (manuel)
pyinstaller rout_art_cms.spec

# Résultat
📁 dist/Rout'Art CMS/Rout'Art CMS.exe
```

L'exécutable peut être distribué et fonctionne sur toute machine Windows sans Python.

---

## 📚 Documentation

### Pour DÉMARRER
- **QUICK_HELP.txt** ← **Commencez ici!**
- CMS_QUICKSTART.md

### Pour COMPRENDRE
- **CMS_README.md** - Documentation complète
- PROJECT_SUMMARY.py - Architecture et technos
- INDEX_COMPLET.md - Index détaillé

### Pour INSTALLER
- GUIDE_INSTALLATION.py - Guide complet
- setup_dependencies.py - Installation auto

### Pour COMPILER
- build_exe.py - Script de compilation
- rout_art_cms.spec - Configuration PyInstaller

### Pour DÉPLOYER
- DEPLOYMENT_CHECKLIST.py - Checklist complète
- create_deployment.py - Package de distribution

---

## 🐛 Dépannage

### "Python n'est pas reconnu"
```
1. Télécharger Python: https://www.python.org
2. Installer en cochant "Add Python to PATH"
3. Redémarrer l'ordinateur
```

### "Dépendances manquantes"
```
pip install -r requirements.txt
```

### "Le port 8000 est déjà utilisé"
```
1. Aller à 👁️ Prévisualisation
2. Changer le port (ex: 8001)
3. Relancer le serveur
```

### "Repository non trouvé"
```
1. Vérifier le chemin (ex: C:\Users\XXX\Rout-Art)
2. Vérifier que c'est un dossier Git
3. Consulter les logs pour plus de détails
```

### Plus de problèmes?
```bash
# Exécuter les tests de configuration
python test_configuration.py

# Voir le guide complet
python GUIDE_INSTALLATION.py

# Consulter la doc
Voir: CMS_README.md section Dépannage
```

---

## 🎓 Exemple d'Utilisation Complète

### Scénario: Mettre à jour les tarifs

```
1. PULL pour récupérer les changements récents
   🔗 Git → ⬇️ Pull

2. ÉDITER le fichier des tarifs
   ✏️ Éditeur → page/tarifs.html
   → Trouver le prix à modifier
   → Changer la valeur
   → 💾 Sauvegarder

3. PRÉVISUALISER avant de publier
   👁️ Prévisualisation → ▶️ Démarrer Serveur
   → 🌐 Ouvrir Navigateur
   → Vérifier que tout est correct
   → F5 pour rafraîchir après chaque modification

4. PUBLIER les changements
   🔗 Git → Message: "Mise à jour des tarifs"
   → ⬆️ Push
   ✓ Les changements sont maintenant sur GitHub!
```

---

## 💾 Dépendances

Automatiquement installées avec:
```bash
pip install -r requirements.txt
```

Ou manuellement:
```
customtkinter>=5.0.0        # Interface GUI moderne
beautifulsoup4>=4.11.0      # Parsing HTML
gitpython>=3.1.0            # Opérations Git
```

---

## 📊 Système Requis

| Critère | Minimum | Recommandé |
|---------|---------|-----------|
| OS | Windows 10 | Windows 11 |
| RAM | 2 GB | 4 GB |
| Disque | 500 MB | 1 GB |
| Processeur | Dual-core | Quad-core |

---

## 🎁 Fichiers Inclus

```
Rout-Art/
├── rout_art_cms.py              ⭐ Application principale
├── cms/                         🔧 Modules fonctionnels
├── requirements.txt             📦 Dépendances
├── setup_dependencies.py        🛠️  Installation auto
├── run.bat                      🖥️  Lanceur Windows
├── launcher.py                  🎮 Menu interactif
├── build_exe.py                 🔨 Compilation
├── test_configuration.py        🧪 Tests
├── CMS_README.md                📚 Documentation
├── QUICK_HELP.txt               🆘 Aide rapide
├── GUIDE_INSTALLATION.py        📖 Guide complet
└── ... (autres fichiers)
```

---

## 🚀 Prochaines Étapes

### 1. Aujourd'hui
- [ ] Installer les dépendances
- [ ] Lancer l'application
- [ ] Configurer le repository

### 2. Demain
- [ ] Éditer une page
- [ ] Tester la prévisualisation
- [ ] Faire un premier push

### 3. Cette Semaine
- [ ] Compiler en .exe
- [ ] Distribuer à l'équipe
- [ ] Former les utilisateurs

### 4. À l'Avenir
- [ ] Améliorer les fonctionnalités
- [ ] Ajouter de nouveaux modules
- [ ] Collecter feedback

---

## 📞 Support & Contact

### Questions?
- **📖 Documentation:** CMS_README.md
- **🆘 Aide Rapide:** QUICK_HELP.txt
- **🧪 Tester:** python test_configuration.py

### Problèmes?
- **📋 Logs:** Consulter l'onglet Logs
- **🐛 Issues:** https://github.com/gossotjeanbaptiste/Rout-Art/issues
- **📧 Email:** support@routart.fr

### Suggestions?
- **💬 Discussions:** GitHub Discussions
- **✨ Features:** Ouvrir une issue
- **📧 Feedback:** support@routart.fr

---

## 📄 License

MIT License - Voir LICENSE.md

```
MIT License

Copyright (c) 2025 Rout'Art

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🌟 Contribution

Contributions bienvenues!

```bash
# 1. Fork le repository
# 2. Créer une branche (git checkout -b feature/xyz)
# 3. Commit les changements (git commit -m 'Add feature')
# 4. Push (git push origin feature/xyz)
# 5. Ouvrir une Pull Request
```

---

## 📈 Historique des Versions

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | Nov 2025 | ✅ Production |

---

## 🎊 Conclusion

Rout'Art CMS est une solution **complète, professionnelle et facile à utiliser** pour gérer le site web de votre auto-école.

**Prêt à commencer?**

```bash
# Lancez simplement:
python launcher.py
# OU double-cliquez: rout_art_cms.exe
```

---

<div align="center">

**Made with ❤️ by Rout'Art Team**

[🌐 Site Web](https://routart.fr) • [💻 GitHub](https://github.com/gossotjeanbaptiste/Rout-Art) • [📧 Support](mailto:support@routart.fr)

**Version 1.0.0** | Novembre 2025

⭐ Si vous aimez ce projet, n'hésitez pas à le partager! ⭐

</div>
