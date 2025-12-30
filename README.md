# 🖍️ MyCMS - C++ Edition

Refonte C++ haute performance du gestionnaire de contenu MyCMS CMS.

## 📋 Vue d'ensemble

**MyCMS (C++)** est une application de gestion de contenu web desktop pour :
- Synchronisation Git (pull/push) avec dépôts distants
- Édition HTML intégrée avec éléments éditables (class="editable")
- Compilation Python → EXE unique (via PyInstaller)
- Gestion de configuration JSON
- Logging détaillé

### ✅ Scope V1

- **Git Manager** : Pull, push, status, add untracked files
- **HTML Editor** : Édition d'éléments éditables, sauvegarde
- **UI Tabs** : Git, Éditeur, Paramètres, Logs
- **Python Builder** : Intégration PyInstaller
- **Config Manager** : Persistence JSON

### ❌ Scope V2+

- Serveur HTTP local + preview
- Sitemap auto-generation
- Logger in-app avancé

---

## 🏗️ Architecture

```
mycms-cpp/
├── README.md                 # Ce fichier
├── CMakeLists.txt           # Build configuration (Qt6, libgit2, etc.)
├── main.cpp                 # Point d'entrée
├── include/                 # Headers (.hpp)
│   ├── ui/
│   │   ├── main_window.hpp
│   │   ├── git_tab.hpp
│   │   ├── editor_tab.hpp
│   │   └── settings_tab.hpp
│   ├── core/
│   │   ├── git_manager.hpp
│   │   ├── html_manager.hpp
│   │   ├── config_manager.hpp
│   │   ├── python_builder.hpp
│   │   └── logger.hpp
│   └── utils/
│       ├── file_utils.hpp
│       └── string_utils.hpp
├── src/                     # Implementation (.cpp)
│   ├── ui/
│   ├── core/
│   └── utils/
├── tests/                   # Tests (Criterion)
│   ├── test_git_manager.cpp
│   ├── test_html_manager.cpp
│   └── CMakeLists.txt
├── assets/                  # Resources (icons, etc.)
│   └── logo.png
└── build/                   # Build output (ignore)
```

---

## 🛠️ Dépendances

### Obligatoires
- **Qt 6.5+** : UI framework multiplateforme
- **libgit2** : Git operations (C API)
- **pugixml** : HTML parsing & DOM
- **nlohmann/json** : JSON config

### Optionnelles (Tests)
- **Criterion** : Unit testing framework
- **CMake 3.20+** : Build system

---

## 📦 Installation & Build

### Prerequisites
```bash
# Windows (MSVC 2022 + Qt 6)
# Installer Qt Creator et Qt 6.5+ depuis https://www.qt.io/download

# ou via vcpkg
git clone https://github.com/Microsoft/vcpkg.git
.\vcpkg\bootstrap-vcpkg.bat
```

### Build
```bash
mkdir build
cd build
cmake -DCMAKE_TOOLCHAIN_FILE=vcpkg/scripts/buildsystems/vcpkg.cmake ..
cmake --build . --config Release

# Exécutable : build/Release/MyCMS.exe (ou Debug/MyCMS)
```

### Tests
```bash
cd build
ctest --output-on-failure
```

---

## 📚 Modules Principaux

### Core Managers

#### GitManager
```cpp
class GitManager {
public:
    bool pull(const std::string& repo_path);
    bool push(const std::string& repo_path, const std::string& message);
    std::string getStatus(const std::string& repo_path);
    // ...
};
```

#### HTMLManager
```cpp
class HTMLManager {
public:
    std::vector<EditableElement> extractEditableElements(const std::string& file_path);
    bool saveFile(const std::string& file_path, const std::vector<EditableElement>& elements);
    // ...
};
```

#### ConfigManager
```cpp
class ConfigManager {
public:
    void loadConfig(const std::string& file_path);
    void saveConfig();
    std::string getRepoPath() const;
    // ...
};
```

#### PythonBuilder
```cpp
class PythonBuilder {
public:
    bool buildExecutable(const std::string& script_path, const std::string& output_path);
    std::string getLastOutput() const;
    // ...
};
```

---

## 🎨 UI Design

5 Tabs principales (Qt QTabWidget) :

1. **Git & Synchronisation**
   - Path selector + browse button
   - Pull / Push / Status buttons
   - Commit message input
   - Status display (git output)

2. **Éditeur de Contenu**
   - File combobox selector
   - Scrollable editable elements list
   - TextEdit widgets (dark theme)
   - Save / Reload buttons

3. **Paramètres**
   - Default repo path
   - Auto-pull at startup (checkbox)
   - Auto-refresh editor (checkbox)
   - Save / Reset buttons

4. **Logs**
   - Logs display (QTextEdit, read-only)
   - Clear / Export buttons

5. **Python Builder** (V1.1)
   - Script path input
   - Build button
   - Output log

---

## 🔗 Migrations depuis Python

| Python                 | C++                  |
| ---------------------- | -------------------- |
| `git.Repo` (GitPython) | `libgit2` C bindings |
| `BeautifulSoup`        | `pugixml`            |
| `tkinter`              | `Qt 6`               |
| JSON config custom     | `nlohmann/json`      |
| `subprocess`           | `QProcess`           |
| `threading`            | `QThread`            |

---

## 📝 Checklist Développement

- [ ] Setup CMake + Qt 6 template
- [ ] GitManager + tests
- [ ] HTMLManager + tests
- [ ] UI Git Tab
- [ ] UI Editor Tab
- [ ] ConfigManager
- [ ] PythonBuilder
- [ ] UI Paramètres Tab
- [ ] Logger
- [ ] Dark theme (stylesheet)
- [ ] Release build & packaging
- [ ] Documentation utilisateur

---

## 🚀 Roadmap

- **V1.0** (Juin 2026) : Git + Editor + Settings
- **V1.1** (Juillet 2026) : Python Builder intégré
- **V2.0** (Septembre 2026) : Serveur HTTP + Preview
- **V2.5** : Sitemap generator, Advanced logger

---

## 📞 Notes de Développement

### Threading
- Git ops → QThread (bloquant)
- File I/O → QThread
- UI updates → QMetaObject::invokeMethod (thread-safe)

### Performance Targets
- Git pull : < 2s
- File load/save : < 500ms
- Startup : < 1s

### Testing Strategy
- Unit tests (Criterion) pour chaque manager
- Integration tests pour workflows Git
- Manual UI tests pour UX

---

## 📄 License

Jean-Baptiste (POGGIO) GOSSOT 

---

**Prêt à coder ?** 🎯 Commencez par `mkdir build && cmake ..` en février !
