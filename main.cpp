#include <QApplication>
#include "ui/main_window.hpp"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    // Configurer l'application
    app.setApplicationName("MyCMS");
    app.setApplicationVersion("1.0.0");
    app.setApplicationDisplayName("🖍️ MyCMS - Content Manager");

    // Créer et afficher la fenêtre principale
    MainWindow window;
    window.show();

    return app.exec();
}
