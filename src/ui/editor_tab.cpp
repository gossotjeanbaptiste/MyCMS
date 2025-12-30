#include "ui/editor_tab.hpp"
#include <QVBoxLayout>
#include <QLabel>

EditorTab::EditorTab(QWidget *parent)
    : QWidget(parent)
{
    createUI();
}

void EditorTab::createUI()
{
    QVBoxLayout *layout = new QVBoxLayout(this);

    // TODO: Implementer l'UI du tab Éditeur
    QLabel *label = new QLabel("Editor Tab - TODO", this);
    layout->addWidget(label);

    setLayout(layout);
}

void EditorTab::onFileSelected(const QString &fileName)
{
    // TODO: Charger le fichier et afficher les éléments éditables
}

void EditorTab::onRefreshFiles()
{
    // TODO: Rafraîchir la liste des fichiers
}

void EditorTab::onSave()
{
    // TODO: Sauvegarder les modifications
}

void EditorTab::onReload()
{
    // TODO: Recharger le fichier
}

void EditorTab::loadEditableElements()
{
    // TODO: Charger les éléments éditables du fichier courant
}
