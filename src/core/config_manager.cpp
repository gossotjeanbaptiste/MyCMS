#include "core/config_manager.hpp"
#include <filesystem>
#include <fstream>

namespace fs = std::filesystem;

ConfigManager::ConfigManager()
{
    loadConfig();
}

void ConfigManager::loadConfig(const std::string &file_path)
{
    std::string config_path = file_path.empty() ? getConfigPath() : file_path;

    if (fs::exists(config_path))
    {
        try
        {
            std::ifstream file(config_path);
            file >> m_config;
            m_configFilePath = config_path;
        }
        catch (const std::exception &e)
        {
            createDefaultConfig();
        }
    }
    else
    {
        createDefaultConfig();
    }
}

void ConfigManager::saveConfig()
{
    try
    {
        std::ofstream file(m_configFilePath);
        file << m_config.dump(2) << std::endl;
    }
    catch (const std::exception &e)
    {
        // TODO: Log l'erreur
    }
}

std::string ConfigManager::getRepoPath() const
{
    return m_config.value("repo_path", "");
}

void ConfigManager::setRepoPath(const std::string &path)
{
    m_config["repo_path"] = path;
}

bool ConfigManager::getAutoPull() const
{
    return m_config.value("auto_pull", false);
}

void ConfigManager::setAutoPull(bool value)
{
    m_config["auto_pull"] = value;
}

bool ConfigManager::getAutoRefresh() const
{
    return m_config.value("auto_refresh", true);
}

void ConfigManager::setAutoRefresh(bool value)
{
    m_config["auto_refresh"] = value;
}

int ConfigManager::getDefaultPort() const
{
    return m_config.value("default_port", 8000);
}

void ConfigManager::setDefaultPort(int port)
{
    m_config["default_port"] = port;
}

std::string ConfigManager::getConfigPath() const
{
    // TODO: Utiliser le répertoire utilisateur (AppData sur Windows, ~/.config sur Linux)
    return "mycms_config.json";
}

void ConfigManager::createDefaultConfig()
{
    m_config = json{
        {"repo_path", ""},
        {"auto_pull", false},
        {"auto_refresh", true},
        {"default_port", 8000}};
    m_configFilePath = getConfigPath();
}
