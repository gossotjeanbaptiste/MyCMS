#include <criterion/criterion.h>
#include "../include/core/html_manager.hpp"

Test(HTMLManager, extract_editable_elements)
{
    HTMLManager manager;

    // TODO: Créer un fichier HTML de test
    // HTMLResult result = manager.extractEditableElements("test.html");

    // cr_assert(!result.success); // Devrait échouer si le fichier n'existe pas
}

Test(HTMLManager, read_write_file)
{
    HTMLManager manager;

    // TODO: Tester la lecture/écriture de fichiers
    // std::string content = manager.readFile("test.html");
    // cr_assert(content.empty() || !content.empty()); // placeholder
}
