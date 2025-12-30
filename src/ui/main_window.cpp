#include "ui/main_window.hpp"
#include <QVBoxLayout>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setWindowTitle("🖍️ MyCMS - Content Manager");
    setGeometry(100, 100, 1400, 800);
    setMinimumSize(1000, 600);

    createUI();
    loadSettings();
}

void MainWindow::createUI()
{
    m_tabWidget = new QTabWidget(this);

    m_gitTab = new GitTab(this);
    m_editorTab = new EditorTab(this);
    m_settingsTab = new SettingsTab(this);

    m_tabWidget->addTab(m_gitTab, "🔗 Git & Synchronisation");
    m_tabWidget->addTab(m_editorTab, "✏️  Éditeur de Contenu");
    m_tabWidget->addTab(m_settingsTab, "⚙️  Paramètres");

    setCentralWidget(m_tabWidget);
}

void MainWindow::loadSettings()
{
    // TODO: Charger la géométrie de la fenêtre depuis config
}

void MainWindow::saveSettings()
{
    // TODO: Sauvegarder la géométrie de la fenêtre dans config
}
