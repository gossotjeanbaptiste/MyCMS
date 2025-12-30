#include "ui/git_tab.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>

GitTab::GitTab(QWidget *parent)
    : QWidget(parent)
{
    createUI();
}

void GitTab::createUI()
{
    QVBoxLayout *layout = new QVBoxLayout(this);

    // TODO: Implementer l'UI du tab Git
    QLabel *label = new QLabel("Git Tab - TODO", this);
    layout->addWidget(label);

    setLayout(layout);
}

void GitTab::onBrowseRepo()
{
    // TODO: Ouvrir file dialog pour sélectionner un repo
}

void GitTab::onVerifyRepo()
{
    // TODO: Vérifier que le repo est valide
}

void GitTab::onPull()
{
    // TODO: Faire un git pull
}

void GitTab::onPush()
{
    // TODO: Faire un git push
}

void GitTab::onStatus()
{
    // TODO: Afficher le statut git
}

void GitTab::onAddUntracked()
{
    // TODO: Ajouter les fichiers non suivis
}
