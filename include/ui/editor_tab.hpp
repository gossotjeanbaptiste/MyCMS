#ifndef EDITOR_TAB_HPP
#define EDITOR_TAB_HPP

#include <QWidget>
#include <QComboBox>
#include <QPushButton>
#include <QScrollArea>
#include <QVBoxLayout>
#include "core/html_manager.hpp"

class EditorTab : public QWidget
{
    Q_OBJECT

public:
    explicit EditorTab(QWidget *parent = nullptr);
    ~EditorTab() = default;

private slots:
    void onFileSelected(const QString &fileName);
    void onRefreshFiles();
    void onSave();
    void onReload();

private:
    void createUI();
    void loadEditableElements();

    QComboBox *m_fileSelector;
    QPushButton *m_refreshBtn;
    QPushButton *m_saveBtn;
    QPushButton *m_reloadBtn;
    QScrollArea *m_editableElementsArea;
    QWidget *m_editableElementsContainer;
    QVBoxLayout *m_editableElementsLayout;

    HTMLManager m_htmlManager;
    QString m_currentFile;
};

#endif // EDITOR_TAB_HPP
