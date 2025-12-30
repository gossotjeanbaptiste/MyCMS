# MyCMS C++ - Projet Template

Projet skeleton pour démarrer la refonte C++ de MyCMS CMS en février 2026.

## 📂 Structure

```
mycms-cpp/
├── README.md              # Vue d'ensemble du projet
├── CMakeLists.txt         # Configuration build (Qt6, libgit2, pugixml, nlohmann/json)
├── main.cpp              # Point d'entrée
├── include/              # Headers (.hpp)
│   ├── ui/               # Interface Qt6
│   │   ├── main_window.hpp
│   │   ├── git_tab.hpp
│   │   ├── editor_tab.hpp
│   │   └── settings_tab.hpp
│   ├── core/             # Logique métier
│   │   ├── git_manager.hpp
│   │   ├── html_manager.hpp
│   │   ├── config_manager.hpp
│   │   ├── python_builder.hpp
│   │   └── logger.hpp
│   └── utils/            # Utilitaires
│       ├── file_utils.hpp
│       └── string_utils.hpp
├── src/                  # Implémentations (.cpp)
│   ├── ui/
│   ├── core/
│   └── utils/
├── tests/                # Tests unitaires (Criterion)
│   ├── test_git_manager.cpp
│   ├── test_html_manager.cpp
│   └── CMakeLists.txt
├── assets/               # Ressources (icons, etc.)
└── build/                # Build output (généré)
```

## 🏗️ Architecture

- **UI** : Qt 6 (QTabWidget, QLineEdit, QTextEdit, etc.)
- **Git** : libgit2 (API C pour Git operations)
- **HTML** : pugixml (parsing et manipulation DOM)
- **Config** : nlohmann/json (persistence JSON)
- **Build** : CMake 3.20+
- **Tests** : Criterion (framework C de test)

## 🚀 Quick Start (Février 2026)

```bash
# Setup
cd mycms-cpp
mkdir build
cd build

# Build
cmake -DCMAKE_TOOLCHAIN_FILE=vcpkg/scripts/buildsystems/vcpkg.cmake ..
cmake --build . --config Release

# Run
./bin/MyCMS  # ou Debug/MyCMS.exe
```

## ✅ Checklist Développement

- [ ] Install Qt 6.5+ et outils
- [ ] Configure vcpkg (Qt6, libgit2, pugixml, nlohmann/json)
- [ ] First successful build
- [ ] Implement GitManager + tests
- [ ] Implement HTMLManager + tests
- [ ] Build UI Tabs (Git, Editor, Settings)
- [ ] ConfigManager + Persistence
- [ ] PythonBuilder (PyInstaller integration)
- [ ] Logger + File I/O
- [ ] Dark theme + Styling
- [ ] Release build & packaging

## 📝 Notes

- Tous les fichiers .cpp contiennent des `TODO` pour marquer les sections à implémenter
- La structure est prête à copier en février - pas de modifications nécessaires
- Utiliser Qt Creator ou VSCode + CMake Tools pour développer
- Tests avec Criterion (optionnel en V1, mais structure prête)

---

**À revisiter en 6 semaines !** 🎯
