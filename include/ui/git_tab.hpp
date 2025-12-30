#ifndef GIT_TAB_HPP
#define GIT_TAB_HPP

#include <QWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QTextEdit>
#include "core/git_manager.hpp"

class GitTab : public QWidget
{
    Q_OBJECT

public:
    explicit GitTab(QWidget *parent = nullptr);
    ~GitTab() = default;

private slots:
    void onBrowseRepo();
    void onVerifyRepo();
    void onPull();
    void onPush();
    void onStatus();
    void onAddUntracked();

private:
    void createUI();

    QLineEdit *m_repoPathInput;
    QLineEdit *m_commitMessageInput;
    QPushButton *m_browseBtn;
    QPushButton *m_verifyBtn;
    QPushButton *m_pullBtn;
    QPushButton *m_pushBtn;
    QPushButton *m_statusBtn;
    QPushButton *m_addUntrackedBtn;
    QTextEdit *m_statusDisplay;

    GitManager m_gitManager;
};

#endif // GIT_TAB_HPP
