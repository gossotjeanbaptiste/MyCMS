#include <criterion/criterion.h>
#include "../include/core/git_manager.hpp"

Test(GitManager, verify_repo)
{
    GitManager manager;

    // TODO: Tester avec un vrai repo
    GitStatus status = manager.verifyRepo(".");

    // Le test dépend si le répertoire courant est un repo git
    // cr_assert_not_null(status.message);
}

Test(GitManager, get_status)
{
    GitManager manager;

    // TODO: Tester sur un repo valide
    GitStatus status = manager.getStatus(".");

    // cr_assert(status.success);
}
