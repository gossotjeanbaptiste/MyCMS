#include "ui/settings_tab.hpp"
#include <QVBoxLayout>
#include <QLabel>

SettingsTab::SettingsTab(QWidget *parent)
    : QWidget(parent)
{
    createUI();
    loadSettings();
}

void SettingsTab::createUI()
{
    QVBoxLayout *layout = new QVBoxLayout(this);

    // TODO: Implementer l'UI du tab Paramètres
    QLabel *label = new QLabel("Settings Tab - TODO", this);
    layout->addWidget(label);

    setLayout(layout);
}

void SettingsTab::loadSettings()
{
    // TODO: Charger les paramètres depuis ConfigManager
}

void SettingsTab::onSaveSettings()
{
    // TODO: Sauvegarder les paramètres
}

void SettingsTab::onResetSettings()
{
    // TODO: Réinitialiser les paramètres par défaut
}
