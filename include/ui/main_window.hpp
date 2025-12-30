#ifndef MAIN_WINDOW_HPP
#define MAIN_WINDOW_HPP

#include <QMainWindow>
#include <QTabWidget>
#include "git_tab.hpp"
#include "editor_tab.hpp"
#include "settings_tab.hpp"

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow() = default;

private:
    void createUI();
    void loadSettings();
    void saveSettings();

    QTabWidget *m_tabWidget;
    GitTab *m_gitTab;
    EditorTab *m_editorTab;
    SettingsTab *m_settingsTab;
};

#endif // MAIN_WINDOW_HPP
