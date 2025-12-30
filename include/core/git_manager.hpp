#ifndef GIT_MANAGER_HPP
#define GIT_MANAGER_HPP

#include <string>
#include <vector>
#include <git2.h>

struct GitStatus
{
    bool success;
    std::string message;
    std::string output;
};

class GitManager
{
public:
    GitManager();
    ~GitManager();

    GitStatus verifyRepo(const std::string &repo_path);
    GitStatus pull(const std::string &repo_path);
    GitStatus push(const std::string &repo_path, const std::string &commit_message);
    GitStatus getStatus(const std::string &repo_path);
    GitStatus addUntracked(const std::string &repo_path);

private:
    void initLibGit2();
    void cleanupLibGit2();
    std::string getActiveBranch(git_repository *repo);
    std::string getRemoteURL(git_repository *repo);

    int m_libGit2Initialized;
};

#endif // GIT_MANAGER_HPP
