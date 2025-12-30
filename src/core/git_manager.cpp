#include "core/git_manager.hpp"

GitManager::GitManager()
    : m_libGit2Initialized(0)
{
    initLibGit2();
}

GitManager::~GitManager()
{
    cleanupLibGit2();
}

void GitManager::initLibGit2()
{
    // TODO: Initialiser libgit2
    m_libGit2Initialized = 1;
}

void GitManager::cleanupLibGit2()
{
    // TODO: Nettoyer libgit2
}

GitStatus GitManager::verifyRepo(const std::string &repo_path)
{
    GitStatus status;
    // TODO: Vérifier que le repo est valide
    status.success = false;
    status.message = "TODO: Implement verifyRepo";
    return status;
}

GitStatus GitManager::pull(const std::string &repo_path)
{
    GitStatus status;
    // TODO: Faire un pull
    status.success = false;
    status.message = "TODO: Implement pull";
    return status;
}

GitStatus GitManager::push(const std::string &repo_path, const std::string &commit_message)
{
    GitStatus status;
    // TODO: Faire un push
    status.success = false;
    status.message = "TODO: Implement push";
    return status;
}

GitStatus GitManager::getStatus(const std::string &repo_path)
{
    GitStatus status;
    // TODO: Récupérer le statut
    status.success = false;
    status.message = "TODO: Implement getStatus";
    return status;
}

GitStatus GitManager::addUntracked(const std::string &repo_path)
{
    GitStatus status;
    // TODO: Ajouter les fichiers non suivis
    status.success = false;
    status.message = "TODO: Implement addUntracked";
    return status;
}

std::string GitManager::getActiveBranch(git_repository *repo)
{
    // TODO: Récupérer la branche active
    return "main";
}

std::string GitManager::getRemoteURL(git_repository *repo)
{
    // TODO: Récupérer l'URL du remote
    return "unknown";
}
