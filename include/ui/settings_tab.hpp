#ifndef SETTINGS_TAB_HPP
#define SETTINGS_TAB_HPP

#include <QWidget>
#include <QLineEdit>
#include <QCheckBox>
#include <QPushButton>
#include "core/config_manager.hpp"

class SettingsTab : public QWidget
{
    Q_OBJECT

public:
    explicit SettingsTab(QWidget *parent = nullptr);
    ~SettingsTab() = default;

private slots:
    void onSaveSettings();
    void onResetSettings();

private:
    void createUI();
    void loadSettings();

    QLineEdit *m_defaultRepoInput;
    QCheckBox *m_autoPullCheckBox;
    QCheckBox *m_autoRefreshCheckBox;
    QPushButton *m_saveBtn;
    QPushButton *m_resetBtn;

    ConfigManager m_configManager;
};

#endif // SETTINGS_TAB_HPP
